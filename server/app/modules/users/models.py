from app.core.database import Base
from sqlalchemy import Column, Integer, String , Enum , DateTime ,  func
from sqlalchemy.orm import Mapped, mapped_column
import enum

class Status(enum.Enum):
    Active =  "active"
    Inactive = "inactive" 
    Pending =  "pending"

class Role(enum.Enum):
    Admin = "admin"
    Seller = "seller"
    Buyer = "buyer"
    User = "user"

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[Role] = mapped_column(Enum(Role), nullable=False, default=Role.User)
    status: Mapped[Status] = mapped_column(Enum(Status), nullable=False, default=Status.Active)
    created_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False, default=func.now())
    avatar_url: Mapped[str] = mapped_column(String(255), nullable=True)
