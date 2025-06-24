# core/connection.py
from fastapi import WebSocket
from ..models import User

class MorseConnection:
    """A wrapper class that holds the WebSocket and the associated User."""
    def __init__(self, websocket: WebSocket, user: User):
        self.websocket = websocket
        self.user = user

    # We can define equality to make it easier to find and remove connections
    def __eq__(self, other):
        if isinstance(other, MorseConnection):
            return self.websocket == other.websocket
        return False