# tests/test_follow.py
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models import Follow, User
from app.routes.user import hash_password


@pytest.fixture
def user1(session: Session):
    """Create first test user"""
    user = User(
        callsign="FOLLOWER1",
        hashed_password=hash_password("password123")
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def user2(session: Session):
    """Create second test user"""
    user = User(
        callsign="FOLLOWER2",
        hashed_password=hash_password("password123")
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def user3(session: Session):
    """Create third test user"""
    user = User(
        callsign="FOLLOWER3",
        hashed_password=hash_password("password123")
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def auth_headers_user1(client: TestClient, user1):
    """Get auth headers for user1"""
    response = client.post("/auth/login", json={
        "callsign": "FOLLOWER1",
        "password": "password123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_user2(client: TestClient, user2):
    """Get auth headers for user2"""
    response = client.post("/auth/login", json={
        "callsign": "FOLLOWER2",
        "password": "password123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestFollowUser:
    """Test following functionality"""

    def test_follow_user(self, client: TestClient, user1, user2, auth_headers_user1):
        """Test following another user"""
        response = client.post(
            f"/follow/{user2.id}/",
            headers=auth_headers_user1
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == str(user2.id)
        assert data["callsign"] == "FOLLOWER2"

    def test_cannot_follow_self(self, client: TestClient, user1, auth_headers_user1):
        """Test that users cannot follow themselves"""
        response = client.post(
            f"/follow/{user1.id}/",
            headers=auth_headers_user1
        )

        assert response.status_code == 400

    def test_cannot_follow_nonexistent_user(self, client: TestClient, auth_headers_user1):
        """Test following non-existent user"""
        import uuid
        fake_id = uuid.uuid4()

        response = client.post(
            f"/follow/{fake_id}/",
            headers=auth_headers_user1
        )

        assert response.status_code == 404

    def test_follow_twice_returns_not_modified(self, client: TestClient, user1, user2, auth_headers_user1, session):
        """Test that following twice returns 304"""
        # First follow
        client.post(f"/follow/{user2.id}/", headers=auth_headers_user1)

        # Refresh user to get updated follows
        session.refresh(user1)

        # Try to follow again
        response = client.post(
            f"/follow/{user2.id}/",
            headers=auth_headers_user1
        )

        assert response.status_code == 304

    def test_follow_is_one_way(self, client: TestClient, user1, user2, auth_headers_user1, auth_headers_user2):
        """Test that follow relationships are one-way"""
        # User1 follows User2
        client.post(f"/follow/{user2.id}/", headers=auth_headers_user1)

        # Check User1's follows
        response = client.get("/follow/", headers=auth_headers_user1)
        assert len(response.json()) == 1
        assert response.json()[0]["callsign"] == "FOLLOWER2"

        # Check User2's follows (should be empty)
        response = client.get("/follow/", headers=auth_headers_user2)
        assert len(response.json()) == 0


class TestGetFollows:
    """Test getting follows list"""

    def test_get_empty_follows(self, client: TestClient, user1, auth_headers_user1):
        """Test getting follows when user follows nobody"""
        response = client.get("/follow/", headers=auth_headers_user1)

        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_get_follows_list(self, client: TestClient, user1, user2, user3, auth_headers_user1):
        """Test getting list of followed users"""
        # User1 follows User2 and User3
        client.post(f"/follow/{user2.id}/", headers=auth_headers_user1)
        client.post(f"/follow/{user3.id}/", headers=auth_headers_user1)

        response = client.get("/follow/", headers=auth_headers_user1)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        callsigns = [user["callsign"] for user in data]
        assert "FOLLOWER2" in callsigns
        assert "FOLLOWER3" in callsigns

    def test_follows_response_structure(self, client: TestClient, user1, user2, user3, auth_headers_user1, auth_headers_user2, session):
        """Test the structure of follows response with nested data"""
        # Create a follow chain: User1 -> User2 -> User3
        client.post(f"/follow/{user2.id}/", headers=auth_headers_user1)

        # User2 follows User3
        follow = Follow(follower_id=user2.id, followed_id=user3.id)
        session.add(follow)
        session.commit()

        response = client.get("/follow/", headers=auth_headers_user1)
        data = response.json()

        # Check structure
        assert len(data) == 1
        user2_data = data[0]
        assert user2_data["callsign"] == "FOLLOWER2"
        assert "id" in user2_data
        assert "created_at" in user2_data

        response2 = client.get("/follow/", headers=auth_headers_user2)
        data2 = response2.json()

        # Check structure
        assert len(data2) == 1
        user3_data = data2[0]
        assert user3_data["callsign"] == "FOLLOWER3"
        assert "id" in user3_data
        assert "created_at" in user3_data


class TestUnfollowUser:
    """Test unfollowing functionality"""

    def test_unfollow_user(self, client: TestClient, user1, user2, auth_headers_user1):
        """Test unfollowing a user"""
        # First follow
        client.post(f"/follow/{user2.id}/", headers=auth_headers_user1)

        # Then unfollow
        response = client.delete(
            f"/follow/{user2.id}/",
            headers=auth_headers_user1
        )

        assert response.status_code == 204

        # Verify unfollowed
        response = client.get("/follow/", headers=auth_headers_user1)
        assert len(response.json()) == 0

    def test_cannot_unfollow_not_followed(self, client: TestClient, user1, user2, auth_headers_user1):
        """Test unfollowing a user that isn't followed"""
        response = client.delete(
            f"/follow/{user2.id}/",
            headers=auth_headers_user1
        )

        assert response.status_code == 404

    def test_unfollow_nonexistent_user(self, client: TestClient, auth_headers_user1):
        """Test unfollowing non-existent user"""
        import uuid
        fake_id = uuid.uuid4()

        response = client.delete(
            f"/follow/{fake_id}/",
            headers=auth_headers_user1
        )

        assert response.status_code == 404


class TestAuthMeWithFollows:
    """Test /auth/me endpoint with follow data"""

    def test_me_endpoint_with_follows(self, client: TestClient, user1, user2, user3, auth_headers_user1, auth_headers_user2, session):
        """Test that /auth/me includes follow and follower data"""
        # User1 follows User2
        client.post(f"/follow/{user2.id}/", headers=auth_headers_user1)

        # User3 follows User1
        follow = Follow(follower_id=user3.id, followed_id=user1.id)
        session.add(follow)
        session.commit()

        response = client.get("/auth/me", headers=auth_headers_user1)

        assert response.status_code == 200
        data = response.json()

        # Check structure
        assert data["callsign"] == "FOLLOWER1"
        assert "follows" in data
        assert "followers" in data

        # Check follows
        assert len(data["follows"]) == 1
        assert data["follows"][0]["callsign"] == "FOLLOWER2"

        # Check followers
        assert len(data["followers"]) == 1
        assert data["followers"][0]["callsign"] == "FOLLOWER3"

    def test_me_endpoint_flat_structure(self, client: TestClient, user1, user2, user3, auth_headers_user2, session):
        """Test that nested follows/followers only contain basic info"""
        # Create follow chain: User1 -> User2 -> User3
        follow1 = Follow(follower_id=user1.id, followed_id=user2.id)
        follow2 = Follow(follower_id=user2.id, followed_id=user3.id)
        session.add_all([follow1, follow2])
        session.commit()

        response = client.get("/auth/me", headers=auth_headers_user2)
        data = response.json()

        # User2 follows User3
        assert len(data["follows"]) == 1
        user3_data = data["follows"][0]

        # Check UserPublicFlat structure (no follows/followers arrays)
        assert "id" in user3_data
        assert "callsign" in user3_data
        assert "created_at" in user3_data
        # UserPublicFlat should not have follows/followers
        assert "follows" not in user3_data
        assert "followers" not in user3_data# tests/test_follow.py