"""
Test suite for the Mergington High School Activities API

Tests cover:
- GET /activities endpoint
- POST /activities/{activity_name}/signup endpoint
- DELETE /activities/{activity_name}/unregister endpoint
- GET / (root) endpoint
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Provide a test client for the FastAPI application"""
    return TestClient(app)


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Verify all 9 activities are present
        assert len(data) == 9
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Tennis Club",
            "Art Studio",
            "Music Ensemble",
            "Debate Club",
            "Science Club"
        ]
        for activity in expected_activities:
            assert activity in data

    def test_activity_has_required_fields(self, client):
        """Test that each activity has all required fields"""
        response = client.get("/activities")
        data = response.json()
        
        required_fields = {"description", "schedule", "max_participants", "participants"}
        for activity_name, activity_data in data.items():
            assert set(activity_data.keys()) == required_fields
            assert isinstance(activity_data["description"], str)
            assert isinstance(activity_data["schedule"], str)
            assert isinstance(activity_data["max_participants"], int)
            assert isinstance(activity_data["participants"], list)

    def test_participants_are_strings(self, client):
        """Test that all participants in activities are email strings"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            for participant in activity_data["participants"]:
                assert isinstance(participant, str)
                assert "@" in participant


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success_new_student(self, client):
        """Test successful signup for a new student"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "test.student@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test.student@mergington.edu" in data["message"]

    def test_signup_adds_student_to_participants(self, client):
        """Test that signup actually adds the student to participants"""
        email = "new.student@mergington.edu"
        
        # Get initial activities
        initial_response = client.get("/activities")
        initial_data = initial_response.json()
        initial_participants = initial_data["Chess Club"]["participants"].copy()
        
        # Signup new student
        client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        
        # Verify student was added
        updated_response = client.get("/activities")
        updated_data = updated_response.json()
        updated_participants = updated_data["Chess Club"]["participants"]
        
        assert email in updated_participants
        assert len(updated_participants) == len(initial_participants) + 1

    def test_signup_duplicate_student_returns_400(self, client):
        """Test that signing up an already-registered student returns 400"""
        email = "michael@mergington.edu"  # Already in Chess Club
        
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()

    def test_signup_nonexistent_activity_returns_404(self, client):
        """Test that signup for a non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_signup_multiple_students_different_activities(self, client):
        """Test that different students can signup for different activities"""
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        
        # Signup for different activities
        response1 = client.post(
            "/activities/Art Studio/signup",
            params={"email": email1}
        )
        response2 = client.post(
            "/activities/Debate Club/signup",
            params={"email": email2}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify both are in their respective activities
        activities = client.get("/activities").json()
        assert email1 in activities["Art Studio"]["participants"]
        assert email2 in activities["Debate Club"]["participants"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client):
        """Test successful unregistration of a student"""
        email = "michael@mergington.edu"  # Already in Chess Club
        
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]

    def test_unregister_removes_student_from_participants(self, client):
        """Test that unregister actually removes the student"""
        email = "daniel@mergington.edu"  # Already in Chess Club
        
        # Verify student is in activity
        activities = client.get("/activities").json()
        assert email in activities["Chess Club"]["participants"]
        
        # Unregister student
        client.delete(
            "/activities/Chess Club/unregister",
            params={"email": email}
        )
        
        # Verify student was removed
        updated_activities = client.get("/activities").json()
        assert email not in updated_activities["Chess Club"]["participants"]

    def test_unregister_nonregistered_student_returns_400(self, client):
        """Test that unregistering a non-registered student returns 400"""
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"].lower()

    def test_unregister_nonexistent_activity_returns_404(self, client):
        """Test that unregister for a non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_unregister_then_signup_again(self, client):
        """Test that a student can unregister and then signup again"""
        email = "reusable@mergington.edu"
        activity = "Programming Class"
        
        # Initial signup
        response1 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Unregister
        response2 = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Signup again
        response3 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response3.status_code == 200
        
        # Verify student is in activity
        activities = client.get("/activities").json()
        assert email in activities[activity]["participants"]


class TestRootEndpoint:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_static_index(self, client):
        """Test that root endpoint redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]

    def test_root_redirect_destination_exists(self, client):
        """Test that the redirect destination is valid"""
        response = client.get("/", follow_redirects=True)
        assert response.status_code == 200


class TestActivityDataIntegrity:
    """Tests for data consistency and integrity"""

    def test_activities_data_consistency(self, client):
        """Test that activity data remains consistent across multiple calls"""
        response1 = client.get("/activities")
        response2 = client.get("/activities")
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Compare activity names and structure
        assert set(data1.keys()) == set(data2.keys())
        
        for activity_name in data1:
            assert data1[activity_name]["description"] == data2[activity_name]["description"]
            assert data1[activity_name]["schedule"] == data2[activity_name]["schedule"]
            assert data1[activity_name]["max_participants"] == data2[activity_name]["max_participants"]

    def test_max_participants_values_are_positive(self, client):
        """Test that all activities have positive max_participants values"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert activity_data["max_participants"] > 0
            assert activity_data["max_participants"] == int(activity_data["max_participants"])

    def test_no_duplicate_participants_allowed(self, client):
        """Test that no student can be registered twice for the same activity"""
        email = "duplicate.test@mergington.edu"
        
        # First signup
        response1 = client.post(
            "/activities/Gym Class/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Second signup attempt
        response2 = client.post(
            "/activities/Gym Class/signup",
            params={"email": email}
        )
        assert response2.status_code == 400
        
        # Verify only one instance in participants
        activities = client.get("/activities").json()
        count = activities["Gym Class"]["participants"].count(email)
        assert count == 1
