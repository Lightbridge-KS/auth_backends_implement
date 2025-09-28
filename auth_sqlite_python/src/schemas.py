from pydantic import BaseModel
from typing import Optional


class UserCreate(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class User(BaseModel):
    id: int
    username: str
    full_name: Optional[str]
    created_at: str
    last_login: Optional[str]
    is_active: bool