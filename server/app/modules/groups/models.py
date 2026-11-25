from app.core.database import BaseModel
from sqlalchemy import Column, Integer, String , DateTime, ForeignKey, UniqueConstraint, func , Enum as SAEnum
from sqlalchemy.orm import relationship , mapped_column , Mapped
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from enum import Enum

class Role(str , Enum):
    Admin = "admin"
    Member = "member"
    Guest = "guest"

class Group(BaseModel):
    __tablename__ = "groups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True  , default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable = False)
    code: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String, nullable=True)
    create_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    update_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

class GroupMember(BaseModel):
    __tablename__ = "group_members"

    group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[Role] = mapped_column(SAEnum(Role), nullable=False, default=Role.Member)
    create_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    update_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    __tag_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_group_members_group_id_user_id"),
    )