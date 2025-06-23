# tests/test_channel_core.py
import json
from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from app.core.channel import Channel
from app.core.connection import MorseConnection
from app.models import ChannelPublic, User


@pytest.fixture
def mock_user1():
    """Create a mock user 1"""
    return User(
        id="123e4567-e89b-12d3-a456-426614174000",
        callsign="USER1",
        hashed_password="hashed",
        created_at=datetime.utcnow(),
        last_seen=datetime.utcnow()
    )


@pytest.fixture
def mock_user2():
    """Create a mock user 2"""
    return User(
        id="223e4567-e89b-12d3-a456-426614174000",
        callsign="USER2",
        hashed_password="hashed",
        created_at=datetime.utcnow(),
        last_seen=datetime.utcnow()
    )


@pytest.fixture
def mock_websocket1():
    """Create a mock websocket"""
    ws = AsyncMock()
    ws.send_json = AsyncMock()
    ws.send_text = AsyncMock()
    return ws


@pytest.fixture
def mock_websocket2():
    """Create another mock websocket"""
    ws = AsyncMock()
    ws.send_json = AsyncMock()
    ws.send_text = AsyncMock()
    return ws


@pytest.fixture
def connection1(mock_user1, mock_websocket1):
    """Create a morse connection for user 1"""
    return MorseConnection(mock_websocket1, mock_user1)


@pytest.fixture
def connection2(mock_user2, mock_websocket2):
    """Create a morse connection for user 2"""
    return MorseConnection(mock_websocket2, mock_user2)


class TestChannel:
    """Test the Channel class"""

    def test_channel_creation_valid(self):
        """Test creating a channel with valid ID"""
        channel = Channel(channel_id="123456")
        assert channel.channel_id == "123456"
        assert channel.user_connections == []
        assert isinstance(channel.created_at, datetime)

    def test_channel_creation_invalid_id(self):
        """Test creating a channel with invalid ID"""
        # Too short
        with pytest.raises(ValueError):
            Channel(channel_id="12345")

        # Too long
        with pytest.raises(ValueError):
            Channel(channel_id="1234567")

        # Non-numeric
        with pytest.raises(ValueError):
            Channel(channel_id="ABCDEF")

    def test_add_user(self, connection1, connection2):
        """Test adding users to channel"""
        channel = Channel(channel_id="123456")

        # Add first user
        channel.add_user(connection1)
        assert channel.user_count == 1
        assert not channel.is_full
        assert connection1 in channel.user_connections

        # Add second user
        channel.add_user(connection2)
        assert channel.user_count == 2
        assert channel.is_full
        assert connection2 in channel.user_connections

    def test_add_user_when_full(self, connection1, connection2):
        """Test adding user when channel is full"""
        channel = Channel(channel_id="123456")
        channel.add_user(connection1)
        channel.add_user(connection2)

        # Try to add third user
        mock_user3 = User(
            id="323e4567-e89b-12d3-a456-426614174000",
            callsign="USER3",
            hashed_password="hashed"
        )
        connection3 = MorseConnection(AsyncMock(), mock_user3)

        with pytest.raises(ValueError, match="Channel is already full"):
            channel.add_user(connection3)

    def test_remove_user(self, connection1, connection2):
        """Test removing users from channel"""
        channel = Channel(channel_id="123456")
        channel.add_user(connection1)
        channel.add_user(connection2)

        # Remove user
        channel.remove_user(connection1)
        assert channel.user_count == 1
        assert connection1 not in channel.user_connections
        assert connection2 in channel.user_connections

    def test_remove_nonexistent_user(self, connection1):
        """Test removing user that's not in channel"""
        channel = Channel(channel_id="123456")
        # Should not raise error
        channel.remove_user(connection1)
        assert channel.user_count == 0

    def test_contains_operator(self, mock_user1, connection1):
        """Test __contains__ operator"""
        channel = Channel(channel_id="123456")
        channel.add_user(connection1)

        # Test with User object
        assert mock_user1 in channel

        # Test with MorseConnection object
        assert connection1 in channel

        # Test with non-existent user
        mock_user3 = User(id="999", callsign="USER3", hashed_password="hash")
        assert mock_user3 not in channel

    def test_get_other_connection(self, connection1, connection2):
        """Test getting the other connection in channel"""
        channel = Channel(channel_id="123456")

        # When only one user
        channel.add_user(connection1)
        assert channel.get_other_connection(connection1) is None

        # When two users
        channel.add_user(connection2)
        assert channel.get_other_connection(connection1) == connection2
        assert channel.get_other_connection(connection2) == connection1

    @pytest.mark.asyncio
    async def test_broadcast(self, connection1, connection2, mock_websocket1, mock_websocket2):
        """Test broadcasting message to all users"""
        channel = Channel(channel_id="123456")
        channel.add_user(connection1)
        channel.add_user(connection2)

        message = {"event": "test", "data": "hello"}
        await channel.broadcast(message)

        # Both websockets should receive the message
        mock_websocket1.send_json.assert_called_once_with(message)
        mock_websocket2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_with_error(self, connection1, connection2, mock_websocket1, mock_websocket2):
        """Test broadcasting when one websocket fails"""
        channel = Channel(channel_id="123456")
        channel.add_user(connection1)
        channel.add_user(connection2)

        # Make first websocket fail
        mock_websocket1.send_json.side_effect = Exception("Connection lost")

        message = {"event": "test", "data": "hello"}
        await channel.broadcast(message)

        # Second websocket should still receive the message
        mock_websocket2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_relay_message_json(self, connection1, connection2, mock_websocket2):
        """Test relaying JSON message to other user"""
        channel = Channel(channel_id="123456")
        channel.add_user(connection1)
        channel.add_user(connection2)

        message = json.dumps({"type": "morse", "signal": "dot"})
        await channel.relay_message(message, connection1)

        # Only the other websocket should receive it
        expected = {"type": "morse", "signal": "dot"}
        mock_websocket2.send_json.assert_called_once_with(expected)

    @pytest.mark.asyncio
    async def test_relay_message_text(self, connection1, connection2, mock_websocket2):
        """Test relaying plain text message"""
        channel = Channel(channel_id="123456")
        channel.add_user(connection1)
        channel.add_user(connection2)

        message = "plain text message"
        await channel.relay_message(message, connection1)

        # Should send as text since it's not valid JSON
        mock_websocket2.send_text.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_relay_message_no_other_user(self, connection1):
        """Test relaying message when no other user"""
        channel = Channel(channel_id="123456")
        channel.add_user(connection1)

        message = "test message"
        # Should not raise error
        await channel.relay_message(message, connection1)

    def test_to_public(self, connection1, connection2, mock_user1, mock_user2):
        """Test converting channel to public representation"""
        channel = Channel(channel_id="123456")
        channel.add_user(connection1)
        channel.add_user(connection2)

        public = channel.to_public()

        assert isinstance(public, ChannelPublic)
        assert public.channel_id == "123456"
        assert public.is_full is True
        assert len(public.users) == 2
        assert public.users[0].callsign == "USER1"
        assert public.users[1].callsign == "USER2"
        assert isinstance(public.created_at, datetime)

    def test_users_property(self, connection1, connection2, mock_user1, mock_user2):
        """Test users property"""
        channel = Channel(channel_id="123456")
        channel.add_user(connection1)
        channel.add_user(connection2)

        users = channel.users
        assert len(users) == 2
        assert mock_user1 in users
        assert mock_user2 in users
