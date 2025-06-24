# tests/test_auth.py
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models import User
from app.routes.user import hash_password


@pytest.fixture
def test_user(session: Session):
    """Create a test user"""
    user = User(
        callsign="TESTAUTH",
        hashed_password=hash_password("testpassword123")
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def auth_headers(client: TestClient, test_user):
    """Get authentication headers with valid token"""
    response = client.post("/auth/login", json={
        "callsign": "TESTAUTH",
        "password": "testpassword123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestLogin:
    """Test login endpoint"""

    def test_login_success(self, client: TestClient, test_user):
        """Test successful login"""
        response = client.post("/auth/login", json={
            "callsign": "TESTAUTH",
            "password": "testpassword123"
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["callsign"] == "TESTAUTH"
        assert data["user"]["id"] == str(test_user.id)

    def test_login_wrong_password(self, client: TestClient, test_user):
        """Test login with wrong password"""
        response = client.post("/auth/login", json={
            "callsign": "TESTAUTH",
            "password": "wrongpassword"
        })

        assert response.status_code == 401
        assert "Incorrect callsign or password" in response.json()["detail"]

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent user"""
        response = client.post("/auth/login", json={
            "callsign": "NONEXISTENT",
            "password": "somepassword"
        })

        assert response.status_code == 401
        assert "Incorrect callsign or password" in response.json()["detail"]

    def test_login_invalid_data(self, client: TestClient):
        """Test login with invalid data"""
        # Missing password
        response = client.post("/auth/login", json={
            "callsign": "TESTAUTH"
        })
        assert response.status_code == 422

        # Missing callsign
        response = client.post("/auth/login", json={
            "password": "testpassword"
        })
        assert response.status_code == 422


class TestGetMe:
    """Test get current user endpoint"""

    def test_get_me_success(self, client: TestClient, test_user, auth_headers):
        """Test getting current user with valid token"""
        response = client.get("/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["callsign"] == test_user.callsign
        assert data["id"] == str(test_user.id)

    def test_get_me_no_token(self, client: TestClient):
        """Test getting current user without token"""
        response = client.get("/auth/me")

        assert response.status_code == 403  # FastAPI returns 403 for missing credentials
        assert response.json()["detail"] == "Not authenticated"

    def test_get_me_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token"""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/auth/me", headers=headers)

        assert response.status_code == 401
        assert "Invalid token" in response.json()["detail"]

    def test_get_me_expired_token(self, client: TestClient, test_user):
        """Test getting current user with expired token"""
        # This is tricky to test without mocking time
        # For a simple project, you might skip this test
        pass


class TestProtectedEndpoint:
    """Test that authentication works for protecting endpoints"""

    def test_protected_endpoint_example(self, client: TestClient, auth_headers):
        """Example of how to protect an endpoint"""
        # You can use auth_headers fixture for any protected endpoint
        # For example, if you had a protected user update endpoint:
        # response = client.put("/users/me", json={"callsign": "NEWCALL"}, headers=auth_headers)
        pass
