# app/core/connection_manager.py
import random
import uuid
from typing import Union

from pydantic import ValidationError

from ..models import ChannelPublic, User
from .channel import Channel
from .connection import MorseConnection


class ChannelFull(Exception):
    pass


class UserAlreadyActive(Exception):
    pass


class ConnectionManager:
    def __init__(self) -> None:
        self.channels: dict[str, Channel] = {}
        # Track which channel each user is in for faster lookups
        self._user_channels: dict[str, str] = {}  # user_id -> channel_id

    @property
    def active_users(self) -> list[User]:
        """Returns a list of all currently connected users."""
        users: set[User] = set()
        for channel in self.channels.values():
            users.update(channel.users)
        return list(users)

    def get_user_channel(self, user_id: Union[uuid.UUID, str]) -> Channel | None:
        """Get the channel a user is currently in"""
        if isinstance(user_id, uuid.UUID):
            user_id = str(user_id)

        channel_id = self._user_channels.get(user_id)
        if channel_id and channel_id in self.channels:
            return self.channels[channel_id]
        return None

    def is_user_active(self, user_id: Union[uuid.UUID, str]) -> bool:
        """Check if a user is already in any channel."""
        if isinstance(user_id, uuid.UUID):
            user_id = str(user_id)

        return user_id in self._user_channels

    def connect(self, connection: MorseConnection, channel_id: str) -> Channel:
        """Handles a new user connecting to a channel."""
        # Validate channel ID format (6 digits)
        try:
            target_channel = Channel(channel_id=channel_id, user_connections=[])
        except ValidationError as e:
            raise ValueError("Channel ID must be a 6-digit number string")


        # Check if user is already active
        if self.is_user_active(connection.user.id):
            raise UserAlreadyActive(f"User {connection.user.callsign} is already in a channel")

        # Create new channel only if it doesn't exist
        if channel_id not in self.channels:
            self.channels[channel_id] = Channel(channel_id=channel_id)

        channel = self.channels[channel_id]

        # Check if channel is full
        if channel.is_full:
            raise ChannelFull("Channel is full")

        # Add user to channel and track it
        channel.add_user(connection)
        self._user_channels[str(connection.user.id)] = channel_id

        return channel

    def disconnect(self, connection: MorseConnection, channel_id: str):
        """Handles a user disconnecting."""
        if channel_id in self.channels:
            channel = self.channels[channel_id]
            channel.remove_user(connection)

            # Remove user tracking
            self._user_channels.pop(str(connection.user.id), None)

            # Delete empty channels
            if channel.user_count == 0:
                del self.channels[channel_id]

    def find_random_waiting_channel(self) -> str | None:
        """Find a random channel with exactly one user waiting"""
        waiting_channels = [
            channel_id for channel_id, channel in self.channels.items()
            if channel.user_count == 1
        ]

        if waiting_channels:
            return random.choice(waiting_channels)
        return None

    def create_random_channel(self) -> str:
        """Create a new channel with a random 6-digit ID"""
        # Generate a unique 6-digit channel ID
        while True:
            channel_id = str(random.randint(100000, 999999))
            if channel_id not in self.channels:
                return channel_id

    async def broadcast_to_channel(self, message: dict, channel_id: str):
        """Sends a message to both users in a channel."""
        if channel_id not in self.channels:
            raise ValueError("Channel does not exist")

        channel = self.channels[channel_id]
        await channel.broadcast(message)

    async def relay_message(self, message: str, sender: MorseConnection, channel_id: str):
        """Relays a morse message to the other user."""
        if channel_id not in self.channels:
            raise ValueError("Channel does not exist")

        channel = self.channels[channel_id]
        await channel.relay_message(message, sender)

    def get_all_channels(self) -> list[ChannelPublic]:
        """Get all active channels as public models"""
        return [channel.to_public() for channel in self.channels.values()]


# Single instance for the app
manager = ConnectionManager()
