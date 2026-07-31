import uuid
from pydantic import BaseModel , EmailStr

class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str = "seller"


class UserCreate(UserBase):
    password: str


class UserUpdate(UserBase):
    password: str | None = None
    status: str | None = None

class ResponseUser(UserBase):
    id: uuid.UUID
    status: str


class LoginRequest(BaseModel):
    email: str
    password: str