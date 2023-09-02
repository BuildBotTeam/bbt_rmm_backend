import asyncio
from typing import Annotated, Union

from fastapi import FastAPI, Query, Cookie, Depends
from starlette import status
from starlette.exceptions import WebSocketException
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocket, WebSocketDisconnect

from controllers.router_controller import get_logs, get_status
from models.auth import Account
from views.mikrotik_router_app import mikrotik_router_app
from views.auth_app import auth_app, TokenAuthBackend
from views.bot_app import dp, bot
from views.ws_app import get_token, manager

middleware = Middleware(CORSMiddleware,
                        allow_origins=["ws://localhost:3000", "http://localhost:3000", "https://localhost:3000"],
                        allow_credentials=True,
                        allow_methods=["*"],
                        allow_headers=["*"],
                        )

app = FastAPI(middleware=[middleware])
app.mount('/auth', auth_app)
secure_app = FastAPI(middleware=[Middleware(AuthenticationMiddleware, backend=TokenAuthBackend())])
app.mount('/api', secure_app)
secure_app.mount('/mikrotik_routers', mikrotik_router_app)


@app.on_event('startup')
async def start_services():
    asyncio.create_task(get_logs())
    asyncio.create_task(get_status())
    asyncio.create_task(dp.start_polling(bot))


@app.on_event("shutdown")
async def shutdown_bot():
    await dp.stop_polling()


@app.websocket("/ws")
async def websocket_endpoint(
        *,
        websocket: WebSocket,
        user: Annotated[Account, Depends(get_token)],
):
    await manager.connect(user.id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(user.id, f"Client #{user.username} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(user.id)
        await manager.broadcast(user.id, f"Client #{user.username} left the chat")
