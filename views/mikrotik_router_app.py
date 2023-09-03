import asyncio
from typing import Union, Annotated
from fastapi import FastAPI, Request, Response, Query, Depends
from starlette import status
from starlette.exceptions import WebSocketException
from starlette.websockets import WebSocket
from models.mikrotik import MikrotikRouter, MikrotikLogs
from views.ws_app import manager

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
    return [r.model_dump(exclude='password') for r in routers]


@mikrotik_router_app.get('/{uid}/')
async def get_mikrotik_router(req: Request, uid: str):
    data = MikrotikRouter.get(uid, user_id=req.user.id)
    return data.model_dump(exclude='password')


@mikrotik_router_app.post('/')
async def create_mikrotik_routers(req: Request, data: MikrotikRouter):
    data.user_id = req.user.id
    data = data.create()
    asyncio.create_task(data.get_logs())
    if data:
        return data.model_dump(exclude='password')
    return Response(status_code=500)


@mikrotik_router_app.put('/')
async def update_mikrotik_router(data: MikrotikRouter):
    data = data.save()
    return data.model_dump(exclude='password')


@mikrotik_router_app.delete('/{uid}/')
async def delete_mikrotik_router(req: Request, uid: str):
    data = MikrotikRouter.get(uid, user_id=req.user.id).delete()
    return Response(status_code=202 if data else 404)


@mikrotik_router_app.get('/{uid}/logs/')
async def get_mikrotik_router_logs(uid: str):
    data = MikrotikLogs.filter(router_id=uid)
    return data


@mikrotik_router_app.post('/command/send_script/')
async def mirotik_send_script(req: Request):
    data = await req.json()
    ids: list[str] = data.get('ids', [])
    is_success, result = await MikrotikRouter.try_send_script(ids)
    return {'is_success': is_success, 'result': result}
