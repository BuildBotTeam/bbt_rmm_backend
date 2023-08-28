from pydantic import BaseModel
from typing import Union


class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    token: str


class Account(BaseModel):
    username: str
    hash_password: str
    token: Union[str, None] = None
    active: bool
