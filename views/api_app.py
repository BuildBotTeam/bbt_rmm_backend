from fastapi import FastAPI, Request, Response

from views.auth_app import is_authenticate

secure_app = FastAPI()


@secure_app.middleware("http")
async def check_authentication(request: Request, call_next):
    if is_authenticate(request):
        return await call_next(request)
    return Response(status_code=401)


@secure_app.get('/')
async def index():
    return 'hello world'
