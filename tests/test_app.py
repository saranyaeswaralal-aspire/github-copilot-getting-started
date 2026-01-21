"""
Tests for the Mergington High School API endpoints
"""

import pytest


class TestActivities:
    """Tests for the /activities endpoint"""

    def test_get_activities(self, client, reset_activities):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        
        # Check that all activities are returned
        assert len(activities) == 9
        assert "Basketball Team" in activities
        assert "Chess Club" in activities
        assert "Programming Class" in activities

    def test_get_activities_structure(self, client, reset_activities):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        activities = response.json()
        
        activity = activities["Basketball Team"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)

    def test_activities_with_participants(self, client, reset_activities):
        """Test that activities with existing participants are returned correctly"""
        response = client.get("/activities")
        activities = response.json()
        
        # Chess Club should have 2 participants initially (from conftest setup would be 0)
        chess = activities["Chess Club"]
        assert isinstance(chess["participants"], list)


class TestSignup:
    """Tests for the /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client, reset_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball Team/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test@mergington.edu" in data["message"]

    def test_signup_adds_participant(self, client, reset_activities):
        """Test that signup actually adds participant to the list"""
        # First signup
        client.post("/activities/Basketball Team/signup?email=student1@mergington.edu")
        
        # Check that participant was added
        response = client.get("/activities")
        activities = response.json()
        assert "student1@mergington.edu" in activities["Basketball Team"]["participants"]

    def test_signup_multiple_participants(self, client, reset_activities):
        """Test signing up multiple participants to same activity"""
        client.post("/activities/Basketball Team/signup?email=student1@mergington.edu")
        client.post("/activities/Basketball Team/signup?email=student2@mergington.edu")
        client.post("/activities/Basketball Team/signup?email=student3@mergington.edu")
        
        response = client.get("/activities")
        activities = response.json()
        assert len(activities["Basketball Team"]["participants"]) == 3

    def test_signup_duplicate_student(self, client, reset_activities):
        """Test that duplicate signup is rejected"""
        # First signup
        client.post("/activities/Basketball Team/signup?email=test@mergington.edu")
        
        # Attempt duplicate signup
        response = client.post(
            "/activities/Basketball Team/signup?email=test@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_nonexistent_activity(self, client, reset_activities):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_signup_different_activities(self, client, reset_activities):
        """Test signing up same student to multiple activities"""
        email = "versatile@mergington.edu"
        client.post(f"/activities/Basketball Team/signup?email={email}")
        client.post(f"/activities/Art Club/signup?email={email}")
        
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Basketball Team"]["participants"]
        assert email in activities["Art Club"]["participants"]


class TestUnregister:
    """Tests for the /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client, reset_activities):
        """Test successful unregister from an activity"""
        # First signup
        client.post("/activities/Basketball Team/signup?email=test@mergington.edu")
        
        # Then unregister
        response = client.post(
            "/activities/Basketball Team/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]

    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister removes participant from list"""
        email = "test@mergington.edu"
        
        # Signup
        client.post(f"/activities/Basketball Team/signup?email={email}")
        
        # Verify signup
        response = client.get("/activities")
        assert email in response.json()["Basketball Team"]["participants"]
        
        # Unregister
        client.post(f"/activities/Basketball Team/unregister?email={email}")
        
        # Verify removal
        response = client.get("/activities")
        assert email not in response.json()["Basketball Team"]["participants"]

    def test_unregister_not_registered(self, client, reset_activities):
        """Test unregister for student not in activity"""
        response = client.post(
            "/activities/Basketball Team/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]

    def test_unregister_nonexistent_activity(self, client, reset_activities):
        """Test unregister from non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_unregister_and_resignup(self, client, reset_activities):
        """Test that student can re-signup after unregistering"""
        email = "flexible@mergington.edu"
        
        # Signup
        client.post(f"/activities/Basketball Team/signup?email={email}")
        
        # Unregister
        client.post(f"/activities/Basketball Team/unregister?email={email}")
        
        # Re-signup should succeed
        response = client.post(f"/activities/Basketball Team/signup?email={email}")
        assert response.status_code == 200
        
        # Verify re-signup
        response = client.get("/activities")
        assert email in response.json()["Basketball Team"]["participants"]


class TestRoot:
    """Tests for the root endpoint"""

    def test_root_redirect(self, client):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestEdgeCases:
    """Tests for edge cases and special scenarios"""

    def test_signup_email_case_sensitive(self, client, reset_activities):
        """Test that emails are treated case-sensitively"""
        # Sign up with lowercase
        client.post("/activities/Basketball Team/signup?email=test@mergington.edu")
        
        # Try to sign up with uppercase - should succeed since emails are case-sensitive
        response = client.post("/activities/Basketball Team/signup?email=TEST@MERGINGTON.EDU")
        assert response.status_code == 200

    def test_activity_name_case_sensitive(self, client, reset_activities):
        """Test that activity names are case-sensitive"""
        response = client.post("/activities/basketball team/signup?email=test@mergington.edu")
        assert response.status_code == 404

    def test_max_participants_not_enforced_in_signup(self, client, reset_activities):
        """Test that max_participants is not enforced (only reflected in UI)"""
        # Math Club has max_participants of 10
        for i in range(15):
            response = client.post(
                f"/activities/Math Club/signup?email=student{i}@mergington.edu"
            )
            assert response.status_code == 200
        
        # Check that all were added
        response = client.get("/activities")
        assert len(response.json()["Math Club"]["participants"]) == 15
