"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


@pytest.fixture
def clear_participants():
    """Reset participants before and after each test"""
    from src import app as app_module
    
    # Store original participants
    original_participants = {}
    for activity_name, activity_data in app_module.activities.items():
        original_participants[activity_name] = activity_data["participants"].copy()
    
    yield
    
    # Restore original participants after test
    for activity_name, activity_data in app_module.activities.items():
        activity_data["participants"] = original_participants[activity_name].copy()


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0
        assert "Soccer Team" in activities
        assert "Basketball Club" in activities
    
    def test_get_activities_has_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_successful(self, clear_participants):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Soccer%20Team/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        
        result = response.json()
        assert "message" in result
        assert "test@mergington.edu" in result["message"]
        assert "Soccer Team" in result["message"]
    
    def test_signup_adds_participant_to_list(self, clear_participants):
        """Test that signup actually adds participant to activity"""
        client.post("/activities/Soccer%20Team/signup?email=newstudent@mergington.edu")
        
        response = client.get("/activities")
        activities = response.json()
        
        assert "newstudent@mergington.edu" in activities["Soccer Team"]["participants"]
    
    def test_signup_nonexistent_activity_returns_404(self):
        """Test signup for nonexistent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        
        result = response.json()
        assert "Activity not found" in result["detail"]
    
    def test_signup_duplicate_returns_400(self, clear_participants):
        """Test that duplicate signup returns 400 error"""
        # First signup
        response1 = client.post(
            "/activities/Soccer%20Team/signup?email=duplicate@mergington.edu"
        )
        assert response1.status_code == 200
        
        # Try duplicate signup
        response2 = client.post(
            "/activities/Soccer%20Team/signup?email=duplicate@mergington.edu"
        )
        assert response2.status_code == 400
        
        result = response2.json()
        assert "already signed up" in result["detail"]


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_successful(self, clear_participants):
        """Test successful unregistration from an activity"""
        # First signup
        client.post("/activities/Soccer%20Team/signup?email=removeme@mergington.edu")
        
        # Then unregister
        response = client.delete(
            "/activities/Soccer%20Team/unregister?email=removeme@mergington.edu"
        )
        assert response.status_code == 200
        
        result = response.json()
        assert "message" in result
        assert "Unregistered" in result["message"]
    
    def test_unregister_removes_participant_from_list(self, clear_participants):
        """Test that unregister actually removes participant from activity"""
        email = "toremove@mergington.edu"
        
        # Signup
        client.post(f"/activities/Soccer%20Team/signup?email={email}")
        
        # Verify they're in the list
        response = client.get("/activities")
        assert email in response.json()["Soccer Team"]["participants"]
        
        # Unregister
        client.delete(f"/activities/Soccer%20Team/unregister?email={email}")
        
        # Verify they're removed
        response = client.get("/activities")
        assert email not in response.json()["Soccer Team"]["participants"]
    
    def test_unregister_nonexistent_activity_returns_404(self):
        """Test unregister from nonexistent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent%20Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
    
    def test_unregister_nonexistent_participant_returns_400(self):
        """Test unregister of student not signed up returns 400"""
        response = client.delete(
            "/activities/Soccer%20Team/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        
        result = response.json()
        assert "not signed up" in result["detail"]


class TestRoot:
    """Tests for root endpoint"""
    
    def test_root_redirects_to_static(self):
        """Test that root endpoint redirects to static page"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
