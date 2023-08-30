from fastapi import FastAPI, Request, Response

from models.mikrotik import MikrotikRouter
from views.auth_app import is_authenticate

secure_app = FastAPI()
connection = None


@secure_app.middleware("http")
async def check_authentication(request: Request, call_next):
    if is_authenticate(request):
        return await call_next(request)
    return Response(status_code=401)


@secure_app.post('/mikrotik_routers/')
async def create_mikrotik_routers(data: MikrotikRouter):
    print(data)
    return data.model_dump()


@secure_app.get('/mikrotik_routers/')
async def get_mikrotik_routers():
    routers = MikrotikRouter.filter()
    global connection
    if not connection:
        connection = MikrotikRouter(host='192.168.252.134', username='admin', password='admin', ).connect()
    else:
        api = connection.get_api()
        print(api.get_resource('/log').get())
    return routers


@secure_app.get('/')
async def index():
    return 'hello world'
