from fastapi import FastAPI, Request, Response
from starlette.authentication import AuthenticationBackend, AuthenticationError, AuthCredentials, SimpleUser

from models.auth import LoginRequest, Account, SecretRequest

auth_app = FastAPI()


def is_authenticate(request: Request):
    authorization = request.headers.get('Authorization')
    if not authorization:
        return None
    token = authorization.split(' ')[1]
    user = Account.get(token=token)
    return user if user and user.active else None


class TokenAuthBackend(AuthenticationBackend):
    async def authenticate(self, request, **kwargs):
        user = is_authenticate(request)
        if user:
            return AuthCredentials(["authenticated"]), user
        raise AuthenticationError('Invalid Token.')


@auth_app.post('/check_token/')
async def check_token(request: Request):
    return Response(status_code=200 if is_authenticate(request) else 401)


@auth_app.post('/login/')
async def login(auth: LoginRequest):
    acc = Account.get(username=auth.username)
    if acc and acc.check_access(auth.password) and acc.active:
        return {'username': acc.username}
    return Response(status_code=401)


@auth_app.post('/check_secret/')
async def check_secret(secret: SecretRequest):
    acc = Account.get(username=secret.username)
    if acc and acc.check_secret(secret.secret):
        return {'token': acc.token}
    return Response(status_code=401)

