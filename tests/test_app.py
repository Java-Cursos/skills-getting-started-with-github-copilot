"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects(self):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for the GET /activities endpoint"""

    def test_get_activities_returns_list(self):
        """Test that get_activities returns a list of activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0

    def test_get_activities_has_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        for activity_name, activity_data in activities.items():
            for field in required_fields:
                assert field in activity_data, f"Activity {activity_name} missing {field}"

    def test_get_activities_contains_expected_activities(self):
        """Test that expected activities are in the list"""
        response = client.get("/activities")
        activities = response.json()
        
        expected_activities = ["Chess Club", "Basketball Team", "Soccer Club", "Art Club"]
        
        for activity in expected_activities:
            assert activity in activities


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=test@mergington.edu",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Signed up" in data["message"]

    def test_signup_invalid_activity(self):
        """Test signup with invalid activity name"""
        response = client.post(
            "/activities/NonExistent%20Club/signup?email=test@mergington.edu",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_duplicate_student(self):
        """Test that duplicate signups are rejected"""
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(
            "/activities/Drama%20Society/signup?email=" + email,
            headers={"Content-Type": "application/json"}
        )
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(
            "/activities/Drama%20Society/signup?email=" + email,
            headers={"Content-Type": "application/json"}
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"]

    def test_signup_adds_participant(self):
        """Test that signup actually adds the participant to the activity"""
        email = "newstudent@mergington.edu"
        activity_name = "Mathletes"
        
        # Get initial participant count
        response_before = client.get("/activities")
        initial_count = len(response_before.json()[activity_name]["participants"])
        
        # Sign up new participant
        client.post(
            f"/activities/{activity_name}/signup?email={email}",
            headers={"Content-Type": "application/json"}
        )
        
        # Get updated participant count
        response_after = client.get("/activities")
        updated_count = len(response_after.json()[activity_name]["participants"])
        
        assert updated_count == initial_count + 1
        assert email in response_after.json()[activity_name]["participants"]
