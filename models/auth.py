# from passlib.context import CryptContext
import random
import string

from bson import ObjectId as BsonObjectId
from pydantic import BaseModel, field_validator, Field
from typing import Union
from secrets import token_bytes
from base64 import b64encode

from controllers.mongo_controller import db, MongoDBModel
from models.settings import settings


# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
#
#
# def is_hash_password(password):
#     return pwd_context.identify(password)
#
#
# def get_password_hash(password):
#     return pwd_context.hash(password)
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
    active: bool

    class Meta:
        collection_name = 'users'

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

    def check_password(self, password: str) -> bool:
        return self.password == password

    # @field_validator('hash_password')
    # def hash_password(cls, pw: str) -> str:
    #     if is_hash_password(pw):
    #         return pw
    #     return pwd_context.hash(pw)

    # def check_password(self, password: str) -> bool:
    #     return pwd_context.verify(password, self.hash_password)
    # @model_validator(mode='before')
    # def _set_person_id(cls, data):
    #     document_id = data.get("_id")
    #     if document_id:
    #         data["person_id"] = document_id
    #     return data

    @classmethod
    def get(cls, id: Union[str, None] = None, username: Union[str, None] = None, token: Union[str, None] = None):
        user = None
        col = db[cls.Meta.collection_name]
        if id:
            user = col.find_one({'_id': BsonObjectId(id)})
        elif username:
            user = col.find_one({'username': username})
        elif token:
            user = col.find_one({'token': token})
        if user:
            return cls(**user)
        return None

    @classmethod
    def filter(cls):
        users = db[cls.Meta.collection_name].find({'username': {'$ne': settings.MONGO_INITDB_ROOT_USERNAME}})
        return [cls(**user) for user in users]

    def to_bot_message_repr(self):
        return f'username: <code>{self.username}</code>\npassword: <code>{self.password}</code>'
