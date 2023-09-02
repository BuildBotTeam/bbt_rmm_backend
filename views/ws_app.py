from typing import Annotated, Union

from fastapi import Query
from starlette import status
from starlette.exceptions import WebSocketException
from starlette.websockets import WebSocket

from models.auth import Account


class ConnectionManager:
    def __init__(self):
        self.active_connections = {}

    async def connect(self, user_id, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id):
        self.active_connections.pop(user_id)

    async def broadcast(self, user_id, message: str):
        ws = self.active_connections[user_id]
        await ws.send_text(message)


manager = ConnectionManager()


async def get_token(
        websocket: WebSocket,
        token: Annotated[Union[str, None], Query()] = None,
):
    if token is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    user = Account.get(token=token)
    if user and user.active:
        return user
    raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
