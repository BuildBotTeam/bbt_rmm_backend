from typing import Union

import asyncio
from fastapi import FastAPI, Request, Response
from models.mikrotik import MikrotikRouter

mikrotik_router_app = FastAPI()


@mikrotik_router_app.get('/')
async def get_mikrotik_routers(req: Request, q: Union[dict, None] = None):
    if isinstance(q, dict):
        routers = MikrotikRouter.filter(user_id=req.user.id, **q)
    else:
        routers = MikrotikRouter.filter(user_id=req.user.id)
    return [r.model_dump(exclude={'password'}) for r in routers]


@mikrotik_router_app.get('/{uid}/')
async def get_mikrotik_router(req: Request, uid: str):
    data = MikrotikRouter.get(uid, user_id=req.user.id)
    return data.model_dump(exclude={'password'})


@mikrotik_router_app.post('/')
async def create_mikrotik_routers(req: Request, data: MikrotikRouter):
    data.user_id = req.user.id
    data = data.create()
    if data:
        asyncio.create_task(data.get_oids())
        asyncio.create_task(data.get_logs())
        return data.model_dump(exclude={'password'})
    return Response(status_code=500)


@mikrotik_router_app.put('/')
async def update_mikrotik_router(data: MikrotikRouter):
    data = data.save()
    if data:
        asyncio.create_task(data.get_oids())
        asyncio.create_task(data.get_logs())
        return data.model_dump(exclude={'password'})
    return Response(status_code=500)


@mikrotik_router_app.delete('/{uid}/')
async def delete_mikrotik_router(req: Request, uid: str):
    data = MikrotikRouter.get(uid, user_id=req.user.id).delete()
    return Response(status_code=202 if data else 404)


# @mikrotik_router_app.get('/{uid}/logs/')
# async def get_mikrotik_router_logs(uid: str):
#     data = MikrotikLogs.filter(router_id=uid)
#     return data


commands = {
    'ping': MikrotikRouter.ping,
    'send_script': MikrotikRouter.send_script,
    'get_scripts': MikrotikRouter.get_scripts,
    'remove_script': MikrotikRouter.remove_script,
    'raw_command': MikrotikRouter.try_send_command,
}


@mikrotik_router_app.post('/command/send_command/')
async def mikrotik_ping(req: Request):
    data = await req.json()
    command = data.pop('command')
    func = commands.get(command)
    if not command or not func:
        return Response('command is required!', status_code=400)
    await func(**data)
    return Response(status_code=200)
