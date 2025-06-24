# app/core/channel.py
import json
import logging
from datetime import datetime
from typing import Union, List

from anyio import ClosedResourceError
from pydantic import BaseModel, Field, ConfigDict
from pydantic.dataclasses import dataclass

from ..models import ChannelPublic, UserPublic, User
from .connection import MorseConnection

logger = logging.getLogger('uvicorn.error')

@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class Channel:
    channel_id: str = Field(pattern=r'^\d{6}$')  # Validates 6-digit string
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user_connections: List[MorseConnection] = Field(default_factory=list, max_length=2)


    def __contains__(self, user_or_connection: Union[User, MorseConnection]) -> bool:
        if isinstance(user_or_connection, User):
            return user_or_connection in self.users

        if isinstance(user_or_connection, MorseConnection):
            return user_or_connection in self.user_connections

        return False

    @property
    def users(self) -> list[User]:
        return [conn.user for conn in self.user_connections]

    @property
    def is_full(self) -> bool:
        return len(self.user_connections) == 2

    @property
    def user_count(self) -> int:
        return len(self.user_connections)

    def add_user(self, connection: MorseConnection):
        if len(self.user_connections) >= 2:
            raise ValueError("Channel is already full")
        self.user_connections.append(connection)

    def remove_user(self, connection: MorseConnection):
        if connection in self.user_connections:
            self.user_connections.remove(connection)

    def get_other_connection(self, connection: MorseConnection) -> MorseConnection | None:
        if not self.is_full:
            return None

        if self.user_connections[0] == connection:
            return self.user_connections[1]
        else:
            return self.user_connections[0]

    async def broadcast(self, message: dict):
        """Broadcast a message to all users in the channel"""
        for user_connection in self.user_connections:
            try:
                await user_connection.websocket.send_json(message)
            except ClosedResourceError as _:
                continue
            except Exception as e:
                logger.error(f"Failed to send message to {user_connection.user.callsign}: {type(e).__name__}: {e}")

    async def relay_message(self, message: str, sender: MorseConnection):
        """Relay a message from one user to another"""
        dest_user_connection = self.get_other_connection(sender)

        if not dest_user_connection:
            logger.debug(f"No other user to relay message to in channel {self.channel_id}")
            return

        try:
            # Parse the message if it's JSON, otherwise send as text
            try:
                parsed_message = json.loads(message)
                await dest_user_connection.websocket.send_json(parsed_message)
                logger.debug(f"Relayed JSON message in channel {self.channel_id}")
            except json.JSONDecodeError:
                # If it's not JSON, send as text
                await dest_user_connection.websocket.send_text(message)
                logger.debug(f"Relayed text message in channel {self.channel_id}")
        except Exception as e:
            logger.error(f"Failed to relay message to {dest_user_connection.user.callsign}: {type(e).__name__}: {e}")

    def to_public(self) -> ChannelPublic:
        """Convert to public representation"""
        users: list[UserPublic] = []
        for user_connection in self.user_connections:
            users.append(UserPublic(**user_connection.user.model_dump()))

        return ChannelPublic(
            channel_id=self.channel_id,
            users=users,
            is_full=self.is_full,
            created_at=self.created_at
        )