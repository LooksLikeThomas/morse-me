# tests/test_channel_routes.py
import json
import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.connection_manager import manager as real_manager
from app.models import User
from app.routes.user import hash_password


@pytest.fixture
def user1(session: Session):
    """Create first test user"""
    user = User(
        callsign="CHANNEL1",
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
        callsign="CHANNEL2",
        hashed_password=hash_password("password123")
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def auth_token1(client: TestClient, user1):
    """Get auth token for user1"""
    response = client.post("/auth/login", json={
        "callsign": "CHANNEL1",
        "password": "password123"
    })
    return response.json()["access_token"]


@pytest.fixture
def auth_token2(client: TestClient, user2):
    """Get auth token for user2"""
    response = client.post("/auth/login", json={
        "callsign": "CHANNEL2",
        "password": "password123"
    })
    return response.json()["access_token"]


@pytest.fixture
def auth_headers1(auth_token1):
    """Get auth headers for user1"""
    return {"Authorization": f"Bearer {auth_token1}"}


@pytest.fixture(autouse=True)
def clear_manager():
    """Clear the connection manager before each test"""
    real_manager.channels.clear()
    real_manager._user_channels.clear()
    yield
    # Clean up after test
    real_manager.channels.clear()
    real_manager._user_channels.clear()


class TestChannelList:
    """Test the channel list endpoint"""

    def test_list_channels_empty(self, client: TestClient, auth_headers1):
        """Test listing channels when none exist"""
        response = client.get("/channel/list", headers=auth_headers1)

        assert response.status_code == 200
        data = response.json()
        assert data["channels"] == []
        assert data["count"] == 0

    def test_list_channels_unauthorized(self, client: TestClient):
        """Test listing channels without auth"""
        response = client.get("/channel/list")
        assert response.status_code == 403

    @patch('app.core.connection_manager.manager.get_all_channels')
    def test_list_channels_with_data(self, mock_get_channels, client: TestClient, auth_headers1):
        """Test listing channels with active channels"""
        from datetime import datetime

        from app.models import ChannelPublic, UserPublic

        # Mock channel data
        mock_channels = [
            ChannelPublic(
                channel_id="123456",
                users=[
                    UserPublic(
                        id=uuid.uuid4(),
                        callsign="USER1",
                        created_at=datetime.utcnow(),
                        status="waiting"
                    )
                ],
                is_full=False,
                created_at=datetime.utcnow()
            ),
            ChannelPublic(
                channel_id="654321",
                users=[
                    UserPublic(
                        id=uuid.uuid4(),
                        callsign="USER2",
                        created_at=datetime.utcnow(),
                        status="busy"
                    ),
                    UserPublic(
                        id=uuid.uuid4(),
                        callsign="USER3",
                        created_at=datetime.utcnow(),
                        status="busy"
                    )
                ],
                is_full=True,
                created_at=datetime.utcnow()
            )
        ]

        mock_get_channels.return_value = mock_channels

        response = client.get("/channel/list", headers=auth_headers1)

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["channels"]) == 2
        assert data["channels"][0]["channel_id"] == "123456"
        assert data["channels"][0]["is_full"] is False
        assert data["channels"][1]["channel_id"] == "654321"
        assert data["channels"][1]["is_full"] is True


class TestWebSocketChannels:
    """Test WebSocket channel endpoints"""

    def test_join_channel_missing_token(self, client: TestClient):
        """Test joining channel without token"""
        with client.websocket_connect("/channel/123456") as websocket:
            # Should be closed immediately
            with pytest.raises(Exception):
                websocket.receive_json()

    def test_join_channel_invalid_token(self, client: TestClient):
        """Test joining channel with invalid token"""
        with pytest.raises(Exception):
            with client.websocket_connect("/channel/123456?token=invalid-token") as websocket:
                websocket.receive_json()

    def test_join_channel_invalid_channel_id(self, client: TestClient, auth_token1):
        """Test joining channel with invalid ID format"""
        with pytest.raises(Exception):
            with client.websocket_connect(f"/channel/ABC123?token={auth_token1}") as websocket:
                websocket.receive_json()

    def test_join_channel_success(self, client: TestClient, auth_token1, user1):
        """Test successfully joining a channel"""
        channel_id = "123456"

        with client.websocket_connect(f"/channel/{channel_id}?token={auth_token1}") as websocket:
            # Should receive user_joined event
            data = websocket.receive_json()
            assert data["event"] == "user_joined"
            assert data["user"]["callsign"] == user1.callsign
            assert data["channel_id"] == channel_id

    def test_join_channel_full(self, client: TestClient, auth_token1, auth_token2, user1, user2):
        """Test joining a full channel"""
        channel_id = "123456"

        # First two users join successfully
        with client.websocket_connect(f"/channel/{channel_id}?token={auth_token1}") as ws1:
            ws1.receive_json()  # user_joined event

            with client.websocket_connect(f"/channel/{channel_id}?token={auth_token2}") as ws2:
                ws2.receive_json()  # user_joined event

                # Third user tries to join
                user3 = User(
                    callsign="CHANNEL3",
                    hashed_password=hash_password("password123")
                )
                client.app.state.db.add(user3)
                client.app.state.db.commit()

                response = client.post("/auth/login", json={
                    "callsign": "CHANNEL3",
                    "password": "password123"
                })
                token3 = response.json()["access_token"]

                # Should fail to connect
                with pytest.raises(Exception):
                    with client.websocket_connect(f"/channel/{channel_id}?token={token3}") as ws3:
                        ws3.receive_json()

    def test_message_relay(self, client: TestClient, auth_token1, auth_token2):
        """Test message relay between users"""
        channel_id = "123456"

        with client.websocket_connect(f"/channel/{channel_id}?token={auth_token1}") as ws1:
            ws1.receive_json()  # user_joined event

            with client.websocket_connect(f"/channel/{channel_id}?token={auth_token2}") as ws2:
                # Both receive user_joined events
                ws2.receive_json()
                ws1.receive_json()

                # User1 sends a message
                morse_message = {"type": "morse", "signal": "dot"}
                ws1.send_text(json.dumps(morse_message))

                # User2 should receive it
                received = ws2.receive_json()
                assert received == morse_message

                # User2 sends a message
                morse_message2 = {"type": "morse", "signal": "dash"}
                ws2.send_text(json.dumps(morse_message2))

                # User1 should receive it
                received = ws1.receive_json()
                assert received == morse_message2

    def test_user_disconnect_notification(self, client: TestClient, auth_token1, auth_token2, user1):
        """Test that remaining user is notified when partner disconnects"""
        channel_id = "123456"

        with client.websocket_connect(f"/channel/{channel_id}?token={auth_token1}") as ws1:
            ws1.receive_json()  # user_joined event

            with client.websocket_connect(f"/channel/{channel_id}?token={auth_token2}") as ws2:
                # Both receive user_joined events
                ws2.receive_json()
                ws1.receive_json()

                # User1 disconnects
                ws1.close()

                # User2 should receive user_left event
                data = ws2.receive_json()
                assert data["event"] == "user_left"
                assert data["user"]["callsign"] == user1.callsign

    def test_join_random_channel_creates_new(self, client: TestClient, auth_token1):
        """Test joining random channel when none exist"""
        with client.websocket_connect(f"/channel/random?token={auth_token1}") as ws:
            # Should receive user_joined event with a channel_id
            data = ws.receive_json()
            assert data["event"] == "user_joined"
            assert "channel_id" in data
            assert len(data["channel_id"]) == 6
            assert data["channel_id"].isdigit()

    def test_join_random_channel_joins_waiting(self, client: TestClient, auth_token1, auth_token2, user1, user2):
        """Test joining random channel finds waiting user"""
        # First user creates a channel by joining random
        with client.websocket_connect(f"/channel/random?token={auth_token1}") as ws1:
            data1 = ws1.receive_json()
            channel_id = data1["channel_id"]

            # Second user joins random, should join same channel
            with client.websocket_connect(f"/channel/random?token={auth_token2}") as ws2:
                # Both should receive user_joined events
                data2 = ws2.receive_json()
                assert data2["event"] == "user_joined"
                assert data2["channel_id"] == channel_id

                # First user should be notified of second user joining
                notification = ws1.receive_json()
                assert notification["event"] == "user_joined"
                assert notification["user"]["callsign"] == user2.callsign

    def test_user_already_in_channel(self, client: TestClient, auth_token1):
        """Test user cannot join multiple channels"""
        channel_id1 = "123456"
        channel_id2 = "654321"

        # Join first channel
        with client.websocket_connect(f"/channel/{channel_id1}?token={auth_token1}") as ws1:
            ws1.receive_json()  # user_joined event

            # Try to join second channel with same user
            with pytest.raises(Exception):
                with client.websocket_connect(f"/channel/{channel_id2}?token={auth_token1}") as ws2:
                    ws2.receive_json()

    def test_plain_text_message_relay(self, client: TestClient, auth_token1, auth_token2):
        """Test relaying plain text (non-JSON) messages"""
        channel_id = "123456"

        with client.websocket_connect(f"/channel/{channel_id}?token={auth_token1}") as ws1:
            ws1.receive_json()  # user_joined event

            with client.websocket_connect(f"/channel/{channel_id}?token={auth_token2}") as ws2:
                # Both receive user_joined events
                ws2.receive_json()
                ws1.receive_json()

                # User1 sends plain text
                plain_message = "Hello, this is plain text"
                ws1.send_text(plain_message)

                # User2 should receive it as text
                received = ws2.receive_text()
                assert received == plain_message
