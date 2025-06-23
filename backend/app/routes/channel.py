# app/routes/channel.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from ..core.connection import MorseConnection
from ..core.connection_manager import ChannelFull, UserAlreadyActive, manager
from ..dep import CurrentUser, CurrentWsUser
from ..models import ChannelsPublic, UserPublic

router = APIRouter(prefix="/channel", tags=["channels"])


@router.get("/list", response_model=ChannelsPublic)
async def list_channels(current_user: CurrentUser):
    """Get all active channels"""
    channels = manager.get_all_channels()
    return ChannelsPublic(channels=channels, count=len(channels))


@router.websocket("/random")
async def join_random_channel(
        websocket: WebSocket,
        user: CurrentWsUser
):
    """Join a random channel with someone waiting, or create a new one"""
    if user is None:
        return

    # Find a channel with someone waiting or create new
    channel_id = manager.find_random_waiting_channel() or manager.create_random_channel()

    # Now join that channel using the main join_channel logic
    morse_connection = MorseConnection(websocket, user)

    try:
        # Atomically check and connect the user
        channel = manager.connect(morse_connection, channel_id)

    except ValueError as e:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason=str(e)
        )
        return

    except UserAlreadyActive:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason=f"User '{user.callsign}' is already in a channel"
        )
        return

    except ChannelFull:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Channel is full"
        )
        return

    # Only accept connection after successful join
    await websocket.accept()

    try:
        # Notify the channel that a user has joined
        user_public_dict = UserPublic(**user.model_dump()).model_dump()
        await channel.broadcast(
            {"event": "user_joined", "user": user_public_dict, "channel_id": channel_id}
        )

        # Main loop to listen for morse signals
        while True:
            data = await websocket.receive_text()
            # Relay morse signal to the other user
            await channel.relay_message(data, morse_connection)

    except WebSocketDisconnect:
        # Normal disconnect
        pass

    except Exception as e:
        # Unexpected error
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason=f"Internal error: {e}")

    finally:
        # Always clean up on disconnect
        manager.disconnect(morse_connection, channel_id)

        # Notify remaining user that partner left
        user_public_dict = UserPublic(**user.model_dump()).model_dump()
        await channel.broadcast(
            {"event": "user_left", "user": user_public_dict}
        )


@router.websocket("/{channel_id}")
async def join_channel(
        websocket: WebSocket,
        channel_id: str,
        user: CurrentWsUser
):
    """
    Handles a user joining a specific channel via WebSocket.

    The client must connect with a valid token in query params:
    ws://localhost/channel/some-channel-id?token=YOUR_JWT_TOKEN
    """
    if user is None:
        return

    morse_connection = MorseConnection(websocket, user)

    try:
        # Atomically check and connect the user
        channel = manager.connect(morse_connection, channel_id)

    except ValueError as e:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason=str(e)
        )
        return

    except UserAlreadyActive:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason=f"User '{user.callsign}' is already in a channel"
        )
        return

    except ChannelFull:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Channel is full"
        )
        return

    # Only accept connection after successful join
    await websocket.accept()

    try:
        # Notify the channel that a user has joined
        user_public_dict = UserPublic(**user.model_dump()).model_dump()
        await channel.broadcast(
            {"event": "user_joined", "user": user_public_dict, "channel_id": channel_id}
        )

        # Main loop to listen for morse signals
        while True:
            data = await websocket.receive_text()
            # Relay morse signal to the other user
            await channel.relay_message(data, morse_connection)

    except WebSocketDisconnect:
        # Normal disconnect
        pass

    except Exception as e:
        # Unexpected error
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason=f"Internal error: {e}")

    finally:
        # Always clean up on disconnect
        manager.disconnect(morse_connection, channel_id)

        # Notify remaining user that partner left
        user_public_dict = UserPublic(**user.model_dump()).model_dump()
        await channel.broadcast(
            {"event": "user_left", "user": user_public_dict}
        )
