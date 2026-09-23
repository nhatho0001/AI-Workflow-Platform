import uuid
from pydantic import BaseModel , EmailStr
from app.modules.users.models import Status , Role

class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: Role = Role.User
    status: Status = Status.Active
    avatar_url: str | None = None


class UserRegister(BaseModel):
    """Schema đăng ký công khai — không cho phép client tự set role/status."""
    name: str
    email: EmailStr
    password: str


class UserCreate(UserBase):
    password: str



class UserUpdate(BaseModel):
    """Schema tự cập nhật thông tin — không cho phép đổi role/status qua đây."""
    name: str | None = None
    email: EmailStr | None = None
    avatar_url: str | None = None
    password: str | None = None

class ResponseUser(UserBase):
    id: uuid.UUID
    model_config = {"from_attributes": True}