from typing import Union

from starlette.websockets import WebSocket

from main import app


@app.websocket("/ws")
async def websocket_endpoint(
        websocket: WebSocket,
):
    print(websocket)
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        print('connect')
        await websocket.send_text(f"Connect")
        if q is not None:
            await websocket.send_text(f"Query parameter q is: {q}")
        await websocket.send_text(f"Message text was: {data}")
