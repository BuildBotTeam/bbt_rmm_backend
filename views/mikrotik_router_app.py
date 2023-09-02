from typing import Union, Annotated
from fastapi import FastAPI, Request, Response, Query, Depends
from starlette import status
from starlette.exceptions import WebSocketException
from starlette.websockets import WebSocket

from models.mikrotik import MikrotikRouter, MikrotikLogs

mikrotik_router_app = FastAPI()


@mikrotik_router_app.get('/')
async def get_mikrotik_routers(req: Request, q: Union[dict, None] = None):
    if isinstance(q, dict):
        routers = MikrotikRouter.filter(user_id=req.user.id, **q)
    else:
        routers = MikrotikRouter.filter(user_id=req.user.id)
    # global connection
    # if not connection:
    #     connection = MikrotikRouter(host='192.168.252.134', username='admin', password='admin', ).connect()
    # else:
    #     api = connection.get_api()
    #     print(api.get_resource('/log').get())
    return [r.model_dump() for r in routers]


@mikrotik_router_app.get('/{uid}/')
async def get_mikrotik_router(req: Request, uid: str):
    data = MikrotikRouter.get(uid, user_id=req.user.id)
    return data.model_dump()


@mikrotik_router_app.post('/')
async def create_mikrotik_routers(req: Request, data: MikrotikRouter):
    data.user_id = req.user.id
    is_online = await data.get_logs()
    if is_online:
        data = data.create()
        return data.model_dump()
    return Response(status_code=500)


@mikrotik_router_app.put('/')
async def update_mikrotik_router(data: MikrotikRouter):
    data = data.save()
    return data.model_dump()


@mikrotik_router_app.delete('/{uid}/')
async def delete_mikrotik_router(req: Request, uid: str):
    data = MikrotikRouter.get(uid, user_id=req.user.id).delete()
    return Response(status_code=202 if data else 404)


@mikrotik_router_app.get('/{uid}/logs/')
async def get_mikrotik_router_logs(uid: str):
    data = MikrotikLogs.filter(router_id=uid)
    return data


# async def get_token(
#         websocket: WebSocket,
#         token: Annotated[Union[str, None], Query()] = None,
# ):
#     if token is None:
#         raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
#     return token
