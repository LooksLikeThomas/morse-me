# tests/test_users.py
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models import User
from app.routes.user import hash_password


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "callsign": "TEST123",
        "password": "securepassword123"
    }


@pytest.fixture
def created_user(session: Session, sample_user_data):
    """Create a user in the database for testing"""
    user = User(
        callsign=sample_user_data["callsign"],
        hashed_password=hash_password(sample_user_data["password"])
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


class TestCreateUser:
    """Test user creation endpoint"""

    def test_create_user_success(self, client: TestClient, sample_user_data):
        """Test successful user creation"""
        response = client.post("/users/", json=sample_user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["callsign"] == sample_user_data["callsign"]
        assert "id" in data
        assert "created_at" in data
        # Password should not be in response
        assert "password" not in data
        assert "hashed_password" not in data

    def test_create_user_duplicate_callsign(self, client: TestClient, sample_user_data, created_user):
        """Test creating user with existing callsign fails"""
        response = client.post("/users/", json=sample_user_data)

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_create_user_invalid_data(self, client: TestClient):
        """Test user creation with invalid data"""
        # Test short callsign
        response = client.post("/users/", json={
            "callsign": "AB",  # Too short
            "password": "validpassword123"
        })
        assert response.status_code == 422

        # Test short password
        response = client.post("/users/", json={
            "callsign": "VALID123",
            "password": "short"  # Too short
        })
        assert response.status_code == 422

        # Test missing fields
        response = client.post("/users/", json={
            "callsign": "VALID123"
            # Missing password
        })
        assert response.status_code == 422


class TestGetUsers:
    """Test get users endpoint"""

    def test_get_users_empty(self, client: TestClient):
        """Test getting users when none exist"""
        response = client.get("/users/")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["data"] == []

    def test_get_users_with_data(self, client: TestClient, created_user):
        """Test getting users when data exists"""
        response = client.get("/users/")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert len(data["data"]) == 1
        assert data["data"][0]["callsign"] == created_user.callsign

    def test_get_users_with_search(self, client: TestClient, session: Session):
        """Test searching users"""
        # Create multiple users
        users = [
            User(callsign="ALPHA123", hashed_password=hash_password("password")),
            User(callsign="BETA456", hashed_password=hash_password("password")),
            User(callsign="GAMMA789", hashed_password=hash_password("password")),
        ]
        for user in users:
            session.add(user)
        session.commit()

        # Search for users containing "ALPHA"
        response = client.get("/users/?q=ALPHA")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["data"][0]["callsign"] == "ALPHA123"

        # Search for users containing "A" (should match ALPHA, BETA, and GAMMA - all have 'A')
        response = client.get("/users/?q=A")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3  # All three users have 'A' in their callsign
        callsigns = [user["callsign"] for user in data["data"]]
        assert "ALPHA123" in callsigns
        assert "BETA456" in callsigns
        assert "GAMMA789" in callsigns

    def test_get_users_pagination(self, client: TestClient, session: Session):
        """Test user pagination"""
        # Create multiple users
        for i in range(5):
            user = User(
                callsign=f"USER{i:03d}",
                hashed_password=hash_password("password")
            )
            session.add(user)
        session.commit()

        # Test limit
        response = client.get("/users/?limit=3")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 5
        assert len(data["data"]) == 3

        # Test offset
        response = client.get("/users/?offset=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 5
        assert len(data["data"]) == 2

    def test_get_users_ordering(self, client: TestClient, session: Session):
        """Test user ordering"""
        # Create users with specific callsigns
        users = [
            User(callsign="CHARLIE", hashed_password=hash_password("password")),
            User(callsign="ALPHA", hashed_password=hash_password("password")),
            User(callsign="BETA", hashed_password=hash_password("password")),
        ]
        for user in users:
            session.add(user)
        session.commit()

        # Test ascending order
        response = client.get("/users/?order=asc")
        assert response.status_code == 200
        data = response.json()
        callsigns = [user["callsign"] for user in data["data"]]
        assert callsigns == ["ALPHA", "BETA", "CHARLIE"]

        # Test descending order (default)
        response = client.get("/users/?order=desc")
        assert response.status_code == 200
        data = response.json()
        callsigns = [user["callsign"] for user in data["data"]]
        assert callsigns == ["CHARLIE", "BETA", "ALPHA"]


class TestGetUser:
    """Test get single user endpoints"""

    def test_get_user_by_id_success(self, client: TestClient, created_user):
        """Test getting user by ID"""
        response = client.get(f"/users/{created_user.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(created_user.id)
        assert data["callsign"] == created_user.callsign

    def test_get_user_by_id_not_found(self, client: TestClient):
        """Test getting non-existent user by ID"""
        fake_id = uuid.uuid4()
        response = client.get(f"/users/{fake_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_user_by_id_invalid_uuid(self, client: TestClient):
        """Test getting user with invalid UUID format"""
        response = client.get("/users/invalid-uuid")

        assert response.status_code == 422  # Validation error

    def test_get_user_by_callsign_success(self, client: TestClient, created_user):
        """Test getting user by callsign"""
        response = client.get(f"/users/callsign/{created_user.callsign}")

        assert response.status_code == 200
        data = response.json()
        assert data["callsign"] == created_user.callsign
        assert data["id"] == str(created_user.id)

    def test_get_user_by_callsign_not_found(self, client: TestClient):
        """Test getting non-existent user by callsign"""
        response = client.get("/users/callsign/NONEXISTENT")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestUserDataIntegrity:
    """Test data integrity and edge cases"""

    def test_user_password_hashing(self, session: Session, sample_user_data):
        """Test that passwords are properly hashed"""
        user = User(
            callsign=sample_user_data["callsign"],
            hashed_password=hash_password(sample_user_data["password"])
        )
        session.add(user)
        session.commit()

        # Password should be hashed, not stored in plain text
        assert user.hashed_password != sample_user_data["password"]
        assert user.hashed_password.startswith("$2b$")  # bcrypt hash format

    def test_user_timestamps(self, client: TestClient, sample_user_data):
        """Test that created_at timestamp is set"""
        response = client.post("/users/", json=sample_user_data)

        assert response.status_code == 201
        data = response.json()
        assert "created_at" in data
        # Should be a valid ISO timestamp
        from datetime import datetime
        datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))

    def test_user_id_generation(self, client: TestClient):
        """Test that user IDs are unique UUIDs"""
        user_data_1 = {"callsign": "USER001", "password": "password123"}
        user_data_2 = {"callsign": "USER002", "password": "password123"}

        response1 = client.post("/users/", json=user_data_1)
        response2 = client.post("/users/", json=user_data_2)

        assert response1.status_code == 201
        assert response2.status_code == 201

        user1_id = response1.json()["id"]
        user2_id = response2.json()["id"]

        # IDs should be different
        assert user1_id != user2_id

        # IDs should be valid UUIDs
        uuid.UUID(user1_id)
        uuid.UUID(user2_id)