import uuid
from pydantic import BaseModel , EmailStr
from app.modules.users.models import Status , Role

class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: Role = Role.User
    status: Status = Status.Active
    avatar_url: str | None = None


class UserCreate(UserBase):
    password: str
    


class UserUpdate(UserBase):
    password: str | None = None

class ResponseUser(UserBase):
    id: uuid.UUID
    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: str
    password: str