from app.core.database import Base
from sqlalchemy import Column, Integer, String , DateTime, ForeignKey, UniqueConstraint, func , Enum as SAEnum
from sqlalchemy.orm import relationship , mapped_column , Mapped
from datetime import datetime
from app.modules.users.models import User
from sqlalchemy.dialects.postgresql import UUID
import uuid
from enum import Enum

class Role(str , Enum):
    Admin = "admin"
    Member = "member"
    Guest = "guest"

class Group(Base):
    __tablename__ = "groups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable = False)
    code: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    group_members: Mapped[list["GroupMember"]] =  relationship(
        "GroupMember" , back_populates="group",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

class GroupMember(Base):
    __tablename__ = "group_members"

    group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False ,  primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False , primary_key=True , index = True)
    role: Mapped[Role] = mapped_column(SAEnum(Role), nullable=False, default=Role.Member)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    group: Mapped["Group"] = relationship("Group" , back_populates="group_members")
    user: Mapped["User"] = relationship("User")
    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_group_members_group_id_user_id"),
    )