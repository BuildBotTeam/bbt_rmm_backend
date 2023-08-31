from typing import Union
from fastapi import FastAPI, Request, Response

from controllers.router_api_controller import convert_log
from models.mikrotik import MikrotikRouter, MikrotikLogs

mikrotik_router_app = FastAPI()
connection = None


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
    api = data.connect()
    if not api:
        return Response('No route to host', status_code=500)
    data = data.create()
    MikrotikLogs.bulk_create(convert_log(api.get_api().get_resource('/log').get(), data.id))
    return data.model_dump()


@mikrotik_router_app.put('/')
async def update_mikrotik_router(data: MikrotikRouter):
    data = data.save()
    return data.model_dump()


@mikrotik_router_app.delete('/{uid}/')
async def delete_mikrotik_router(req: Request, uid: str):
    data = MikrotikRouter.get(uid, user_id=req.user.id).delete()
    MikrotikLogs.bulk_delete([log.id for log in MikrotikLogs.filter(router_id=uid)])
    return Response(status_code=202 if data else 404)


@mikrotik_router_app.get('/{uid}/logs/')
async def get_mikrotik_router_logs(uid: str):
    data = MikrotikLogs.filter(router_id=uid)
    return data
