# tests/test_connection_manager.py
import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.core.connection import MorseConnection
from app.core.connection_manager import (
    ChannelFull,
    ConnectionManager,
    UserAlreadyActive,
)
from app.models import User


@pytest.fixture
def manager():
    """Create a fresh connection manager"""
    return ConnectionManager()


@pytest.fixture
def mock_user1():
    """Create a mock user 1"""
    return User(
        id=uuid.uuid4(),
        callsign="USER1",
        hashed_password="hashed",
    )


@pytest.fixture
def mock_user2():
    """Create a mock user 2"""
    return User(
        id=uuid.uuid4(),
        callsign="USER2",
        hashed_password="hashed",
    )


@pytest.fixture
def connection1(mock_user1):
    """Create a connection for user 1"""
    ws = AsyncMock()
    return MorseConnection(ws, mock_user1)


@pytest.fixture
def connection2(mock_user2):
    """Create a connection for user 2"""
    ws = AsyncMock()
    return MorseConnection(ws, mock_user2)


class TestConnectionManager:
    """Test the ConnectionManager class"""

    def test_manager_initialization(self, manager):
        """Test manager initializes correctly"""
        assert manager.channels == {}
        assert manager._user_channels == {}
        assert manager.active_users == []

    def test_connect_new_channel(self, manager, connection1):
        """Test connecting to a new channel"""
        channel_id = "123456"
        channel = manager.connect(connection1, channel_id)

        assert channel_id in manager.channels
        assert channel.channel_id == channel_id
        assert connection1 in channel
        assert str(connection1.user.id) in manager._user_channels
        assert manager._user_channels[str(connection1.user.id)] == channel_id

    def test_connect_existing_channel(self, manager, connection1, connection2):
        """Test connecting to existing channel"""
        channel_id = "123456"

        # First user creates channel
        channel1 = manager.connect(connection1, channel_id)

        # Second user joins same channel
        channel2 = manager.connect(connection2, channel_id)

        assert channel1 == channel2
        assert channel2.user_count == 2
        assert channel2.is_full

    def test_connect_invalid_channel_id(self, manager, connection1):
        """Test connecting with invalid channel ID"""
        # Invalid format
        with pytest.raises(ValueError, match="Channel ID must be a 6-digit number string"):
            manager.connect(connection1, "ABC123")

        # Too short
        with pytest.raises(ValueError):
            manager.connect(connection1, "12345")

        # Too long
        with pytest.raises(ValueError):
            manager.connect(connection1, "1234567")

    def test_connect_user_already_active(self, manager, connection1):
        """Test connecting when user is already in a channel"""
        # Connect to first channel
        manager.connect(connection1, "123456")

        # Try to connect to another channel
        with pytest.raises(UserAlreadyActive):
            manager.connect(connection1, "654321")

    def test_connect_channel_full(self, manager, connection1, connection2):
        """Test connecting to full channel"""
        channel_id = "123456"

        # Fill the channel
        manager.connect(connection1, channel_id)
        manager.connect(connection2, channel_id)

        # Third user tries to join
        mock_user3 = User(id=uuid.uuid4(), callsign="USER3", hashed_password="hash")
        connection3 = MorseConnection(AsyncMock(), mock_user3)

        with pytest.raises(ChannelFull):
            manager.connect(connection3, channel_id)

    def test_disconnect(self, manager, connection1, connection2):
        """Test disconnecting from channel"""
        channel_id = "123456"
        manager.connect(connection1, channel_id)
        manager.connect(connection2, channel_id)

        # Disconnect first user
        manager.disconnect(connection1, channel_id)

        assert str(connection1.user.id) not in manager._user_channels
        assert channel_id in manager.channels  # Channel still exists
        assert manager.channels[channel_id].user_count == 1

        # Disconnect second user
        manager.disconnect(connection2, channel_id)

        assert channel_id not in manager.channels  # Channel is deleted
        assert str(connection2.user.id) not in manager._user_channels

    def test_disconnect_nonexistent_channel(self, manager, connection1):
        """Test disconnecting from non-existent channel"""
        # Should not raise error
        manager.disconnect(connection1, "999999")

    def test_is_user_active(self, manager, connection1, mock_user1):
        """Test checking if user is active"""
        assert not manager.is_user_active(mock_user1.id)
        assert not manager.is_user_active(str(mock_user1.id))

        manager.connect(connection1, "123456")

        assert manager.is_user_active(mock_user1.id)
        assert manager.is_user_active(str(mock_user1.id))

    def test_get_user_channel(self, manager, connection1, mock_user1):
        """Test getting user's current channel"""
        assert manager.get_user_channel(mock_user1.id) is None

        channel_id = "123456"
        manager.connect(connection1, channel_id)

        channel = manager.get_user_channel(mock_user1.id)
        assert channel is not None
        assert channel.channel_id == channel_id

    def test_active_users(self, manager, connection1, connection2, mock_user1, mock_user2):
        """Test getting list of active users"""
        assert manager.active_users == []

        manager.connect(connection1, "123456")
        active = manager.active_users
        assert len(active) == 1
        assert mock_user1 in active

        manager.connect(connection2, "654321")
        active = manager.active_users
        assert len(active) == 2
        assert mock_user1 in active
        assert mock_user2 in active

    def test_find_random_waiting_channel(self, manager, connection1, connection2):
        """Test finding channel with one waiting user"""
        # No channels
        assert manager.find_random_waiting_channel() is None

        # Create channel with one user
        manager.connect(connection1, "123456")
        waiting = manager.find_random_waiting_channel()
        assert waiting == "123456"

        # Fill that channel
        manager.connect(connection2, "123456")
        assert manager.find_random_waiting_channel() is None

        # Create another channel with one user
        mock_user3 = User(id=uuid.uuid4(), callsign="USER3", hashed_password="hash")
        connection3 = MorseConnection(AsyncMock(), mock_user3)
        manager.connect(connection3, "654321")

        waiting = manager.find_random_waiting_channel()
        assert waiting == "654321"

    def test_create_random_channel(self, manager):
        """Test creating random channel ID"""
        channel_ids = set()

        # Create multiple random channels
        for _ in range(10):
            channel_id = manager.create_random_channel()
            assert len(channel_id) == 6
            assert channel_id.isdigit()
            assert channel_id not in channel_ids
            channel_ids.add(channel_id)

    @pytest.mark.asyncio
    async def test_broadcast_to_channel(self, manager, connection1, connection2):
        """Test broadcasting to a channel"""
        channel_id = "123456"
        manager.connect(connection1, channel_id)
        manager.connect(connection2, channel_id)

        message = {"event": "test", "data": "hello"}

        # Mock the channel's broadcast method
        with patch.object(manager.channels[channel_id], 'broadcast', new_callable=AsyncMock) as mock_broadcast:
            await manager.broadcast_to_channel(message, channel_id)
            mock_broadcast.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_to_nonexistent_channel(self, manager):
        """Test broadcasting to non-existent channel"""
        with pytest.raises(ValueError, match="Channel does not exist"):
            await manager.broadcast_to_channel({"test": "data"}, "999999")

    @pytest.mark.asyncio
    async def test_relay_message(self, manager, connection1, connection2):
        """Test relaying message between users"""
        channel_id = "123456"
        manager.connect(connection1, channel_id)
        manager.connect(connection2, channel_id)

        # Mock the channel's relay_message method
        with patch.object(manager.channels[channel_id], 'relay_message', new_callable=AsyncMock) as mock_relay:
            await manager.relay_message("test message", connection1, channel_id)
            mock_relay.assert_called_once_with("test message", connection1)

    @pytest.mark.asyncio
    async def test_relay_message_nonexistent_channel(self, manager, connection1):
        """Test relaying to non-existent channel"""
        with pytest.raises(ValueError, match="Channel does not exist"):
            await manager.relay_message("test", connection1, "999999")

    def test_get_all_channels(self, manager, connection1, connection2):
        """Test getting all channels as public models"""
        # No channels
        assert manager.get_all_channels() == []

        # Add channels
        manager.connect(connection1, "123456")

        channels = manager.get_all_channels()
        assert len(channels) == 1
        assert channels[0].channel_id == "123456"
        assert channels[0].is_full is False
        assert len(channels[0].users) == 1

        # Add second user
        manager.connect(connection2, "123456")

        channels = manager.get_all_channels()
        assert len(channels) == 1
        assert channels[0].is_full is True
        assert len(channels[0].users) == 2

    def test_manager_singleton(self):
        """Test that we can import the singleton instance"""
        from app.core.connection_manager import manager
        assert isinstance(manager, ConnectionManager)
