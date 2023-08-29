from fastapi import FastAPI, Request, Response

from models.auth import LoginRequest, Account

auth_app = FastAPI()


def is_authenticate(request: Request):
    authorization = request.headers.get('Authorization')
    if not authorization:
        return Response(status_code=401)
    token = authorization.split(' ')[1]
    user = Account.get(token=token)
    return user and user.active


@auth_app.post('/check_token/')
async def check_token(request: Request):
    return Response(status_code=200 if is_authenticate(request) else 401)


# @auth_app.post('/logout/')
# async def logout(request: Request):
#     authorization = request.headers.get('Authorization')
#     if not authorization:
#         return Response(status_code=401)
#     token = authorization.split(' ')[1]
#     user = Account.get(token=token)
#     user.token = None
#     user.save()
#     return Response(status_code=401)


@auth_app.post('/login/')
async def login(auth: LoginRequest):
    acc = Account.get(username=auth.username)
    if acc.check_password(auth.password):
        return {'token': acc.token, 'username': acc.username}
    return Response(status_code=401)
