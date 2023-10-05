import base64
import random
import string

import pyotp
from pydantic import BaseModel, field_validator
from typing import Union
from secrets import token_bytes
from base64 import b64encode
from controllers.mongo_controller import db, MongoDBModel


def get_random_password():
    random_source = string.ascii_letters + string.digits + '@!#$%&*'
    return ''.join(random.choice(random_source) for i in range(8))


class LoginRequest(BaseModel):
    username: str
    password: str


class SecretRequest(BaseModel):
    username: str
    secret: str


class Token(BaseModel):
    token: str


class Account(MongoDBModel):
    username: str
    password: Union[str, None] = None
    token: Union[str, None] = None
    google_secret: Union[str, None] = None
    active: bool
    admin: bool = False

    class Meta:
        collection_name = 'users'

    def create_secret(self):
        secret = self.username + '456' + self.password
        self.google_secret = base64.b32encode(secret.encode("UTF-8")).decode('utf-8')
        return self

    def change_token(self):
        self.token = b64encode(token_bytes(32)).decode()
        return self

    def check_token(self, token: str) -> bool:
        return self.token == token

    @field_validator('password')
    def validate_password(cls, pw: str) -> str:
        if pw:
            return pw
        return get_random_password()

    def check_access(self, password: str) -> bool:
        return self.password == password

    def qr_code_url_gen(self):
        return pyotp.totp.TOTP(self.google_secret).provisioning_uri(name='BBT RMM', issuer_name='Secure App')

    def check_secret(self, secret: str) -> bool:
        if not self.google_secret:
            return False
        totp = pyotp.TOTP(self.google_secret)
        return totp.verify(secret)

    @classmethod
    def filter(cls):
        users = db[cls.Meta.collection_name].find({'admin': False})
        return [cls(**user) for user in users]

    def to_bot_message_repr(self):
        return f'username: <code>{self.username}</code>\n' \
               f'password: <code>{self.password}</code>\n' \
               f'secret: <code>{self.google_secret}</code>'
