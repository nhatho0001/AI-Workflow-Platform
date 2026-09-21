from app.core.database import Base
from sqlalchemy import String , Enum , DateTime ,  func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import enum
import uuid

class Status(str, enum.Enum):
    Active =  "active"
    Inactive = "inactive"
    Pending =  "pending"

class Role(str, enum.Enum):
    Admin = "admin"
    Seller = "seller"
    Buyer = "buyer"
    User = "user"

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[Role] = mapped_column(Enum(Role), nullable=False, default=Role.User)
    status: Mapped[Status] = mapped_column(Enum(Status), nullable=False, default=Status.Active)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    avatar_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
