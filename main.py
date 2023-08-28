import routeros_api
from routeros_api.api import RouterOsApi
from pysnmp.hlapi import *
from fastapi import FastAPI, Request, Response
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from secrets import token_bytes
from base64 import b64encode
from passlib.context import CryptContext

from models.auth import LoginRequest, Token, Account

online_user = []

middleware = Middleware(CORSMiddleware,
                        allow_origins=["http://localhost:3000", "http://localhost:4000"],
                        allow_methods=["*"],
                        allow_headers=["*"],
                        )

app = FastAPI(middleware=[middleware])
auth_app = FastAPI()
secure_app = FastAPI()
app.mount('/auth', auth_app)
app.mount('/api', secure_app)

IP_MIKROTIK = '192.168.252.134'
OIDS = {
    '1.3.6.1.2.1.31.1.1.1.6.1': 'bytes-in',
    '1.3.6.1.2.1.31.1.1.1.10.1': 'bytes-out',
}

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def is_authenticate(request: Request):
    authorization = request.headers.get('Authorization')
    print(authorization)
    print(request.headers)
    if not authorization:
        return False
    token = authorization.split(' ')[1]
    for user in online_user:
        if user.active and user.token == token:
            return True
    return False


@secure_app.middleware("http")
async def check_authentication(request: Request, call_next):
    if is_authenticate(request):
        return await call_next(request)
    return Response(status_code=401)


@secure_app.get('/')
async def index():
    return get_oid_data()


@auth_app.post('/check_token/')
async def check_token(request: Request):
    return Response(status_code=200 if is_authenticate(request) else 400)


@auth_app.post('/logout/')
async def logout(request, token: Token):
    for user in online_user:
        if user.token == token.token:
            user.token = None
    return Response(status_code=200)


@auth_app.post('/login/')
async def login(auth: LoginRequest):
    acc = Account(username=auth.username, hash_password=get_password_hash(auth.password),
                  token=b64encode(token_bytes(32)).decode(), active=True)
    online_user.append(acc)
    return {'token': acc.token, 'username': acc.username}


class Script:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.name = kwargs.get('name')
        self.owner = kwargs.get('owner')
        self.policy = kwargs.get('policy')
        self.dont_require_permissions = kwargs.get('dont-require-permissions')
        self.run_count = kwargs.get('run-count')
        self.source = kwargs.get('source')
        self.invalid = kwargs.get('invalid')

    def __str__(self):
        return f"{self.__dict__}"


def connect(username: str, password: str) -> RouterOsApi:
    connection = routeros_api.RouterOsApiPool(IP_MIKROTIK, username=username, password=password, port=8728,
                                              use_ssl=False,
                                              ssl_verify=True,
                                              plaintext_login=True,
                                              ssl_verify_hostname=True, )
    api = connection.get_api()
    return api


def get_oid_data():
    iterator = getCmd(
        SnmpEngine(),
        CommunityData('public', mpModel=1),
        UdpTransportTarget((IP_MIKROTIK, 161)),
        ContextData(),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.31.1.1.1.6.1')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.31.1.1.1.10.1')),
        lookupMib=False,
        lexicographicMode=False
    )

    error_indication, error_status, error_index, var_binds = next(iterator)
    if error_indication:
        print(error_indication)
    elif error_status:
        print('%s at %s' % (error_status.prettyPrint(), error_index and var_binds[int(error_index) - 1][0] or '?'))
    else:
        for var_bind in var_binds:
            oid, data = [x.prettyPrint() for x in var_bind]
            print(' = '.join([OIDS[oid], data]))
            return ' = '.join([OIDS[oid], data])

# api = connect('admin', 'admin')
# list = api.get_resource('/system/script')
# for l in list.get():
#     s = Script(**l)
#     print(s)
