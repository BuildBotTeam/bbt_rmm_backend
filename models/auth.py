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


class Token(BaseModel):
    token: str


class Account(MongoDBModel):
    username: str
    password: Union[str, None] = None
    token: Union[str, None] = None
    google_secret: Union[str, None] = None
    active: bool

    class Meta:
        collection_name = 'users'

    def change_token(self):
        new_token = b64encode(token_bytes(32)).decode()
        if not self.token:
            self.google_secret = new_token
        self.token = new_token
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
        totp = pyotp.TOTP(self.google_secret)
        return totp.verify(secret)

    @classmethod
    def filter(cls):
        users = db[cls.Meta.collection_name].find({'admin': False})
        return [cls(**user) for user in users]

    def to_bot_message_repr(self):
        return f'email: <code>{self.email}</code>\n' \
               f'username: <code>{self.username}</code>\n' \
               f'password: <code>{self.password}</code>'
