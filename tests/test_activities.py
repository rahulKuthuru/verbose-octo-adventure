import pytest


class TestGetActivities:
    """Test the GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that /activities returns all available activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Basketball" in data
        assert "Tennis Club" in data
        assert "Drama Club" in data
        assert len(data) == 9

    def test_activities_have_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        for activity_name, activity in data.items():
            assert "description" in activity
            assert "schedule" in activity
            assert "max_participants" in activity
            assert "participants" in activity
            assert isinstance(activity["participants"], list)

    def test_activities_initial_participants(self, client):
        """Test that activities have expected initial participants"""
        response = client.get("/activities")
        data = response.json()
        assert "james@mergington.edu" in data["Basketball"]["participants"]
        assert "alex@mergington.edu" in data["Tennis Club"]["participants"]
        assert len(data["Drama Club"]["participants"]) == 2


class TestSignupForActivity:
    """Test the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_student_for_activity(self, client, reset_activities):
        """Test signing up a new student for an activity"""
        response = client.post(
            "/activities/Basketball/signup",
            params={"email": "newemail@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newemail@mergington.edu" in data["message"]

    def test_signup_adds_student_to_participants(self, client, reset_activities):
        """Test that signup actually adds student to participants list"""
        # Check initial state
        response = client.get("/activities")
        initial_count = len(response.json()["Basketball"]["participants"])

        # Sign up new student
        client.post(
            "/activities/Basketball/signup",
            params={"email": "newstudent@mergington.edu"}
        )

        # Check updated state
        response = client.get("/activities")
        updated_count = len(response.json()["Basketball"]["participants"])
        assert updated_count == initial_count + 1
        assert "newstudent@mergington.edu" in response.json()["Basketball"]["participants"]

    def test_signup_nonexistent_activity_returns_404(self, client, reset_activities):
        """Test that signing up for nonexistent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_already_signed_up_returns_400(self, client, reset_activities):
        """Test that signing up twice returns 400"""
        # First signup
        response1 = client.post(
            "/activities/Basketball/signup",
            params={"email": "duplicate@mergington.edu"}
        )
        assert response1.status_code == 200

        # Attempt duplicate signup
        response2 = client.post(
            "/activities/Basketball/signup",
            params={"email": "duplicate@mergington.edu"}
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"]

    def test_signup_with_existing_participant(self, client, reset_activities):
        """Test that existing participants are still there after signup"""
        response = client.post(
            "/activities/Basketball/signup",
            params={"email": "another@mergington.edu"}
        )
        assert response.status_code == 200

        # Verify original participant is still there
        response = client.get("/activities")
        participants = response.json()["Basketball"]["participants"]
        assert "james@mergington.edu" in participants
        assert "another@mergington.edu" in participants


class TestRootEndpoint:
    """Test the root endpoint"""

    def test_root_redirects_to_static(self, client):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307


class TestDataIntegrity:
    """Test data integrity across operations"""

    def test_multiple_signups_dont_interfere(self, client, reset_activities):
        """Test that signups for different activities don't interfere"""
        # Sign up for different activities
        client.post("/activities/Basketball/signup", params={"email": "user1@mergington.edu"})
        client.post("/activities/Tennis Club/signup", params={"email": "user2@mergington.edu"})
        client.post("/activities/Drama Club/signup", params={"email": "user3@mergington.edu"})

        # Verify all signups were successful
        response = client.get("/activities")
        data = response.json()
        assert "user1@mergington.edu" in data["Basketball"]["participants"]
        assert "user2@mergington.edu" in data["Tennis Club"]["participants"]
        assert "user3@mergington.edu" in data["Drama Club"]["participants"]

    def test_signup_preserves_existing_data(self, client, reset_activities):
        """Test that signup preserves all existing activity data"""
        client.post("/activities/Chess Club/signup", params={"email": "newuser@mergington.edu"})

        response = client.get("/activities")
        chess_club = response.json()["Chess Club"]

        # Verify original participants are still there
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]
        # Verify new participant was added
        assert "newuser@mergington.edu" in chess_club["participants"]
        # Verify metadata is preserved
        assert chess_club["description"] == "Learn strategies and compete in chess tournaments"
        assert chess_club["max_participants"] == 12
