from app.core.database import Base
from sqlalchemy import Column, String, Enum , ForeignKey , DateTime, func , JSON
from sqlalchemy.orm import relationship , Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from enum import Enum
import uuid

class RoleEnum(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"
    tool = "tool"


class Conversation(Base):
    __tablename__ = "conversations"

    id : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    model_id : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("models.id"), nullable=False)
    folder_id : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("folders.id"), nullable=True)
    title : Mapped[str] = mapped_column(String(255), nullable=True)
    system_prompt : Mapped[str] = mapped_column(String(1000), nullable=True)
    temperature : Mapped[float] = mapped_column(nullable=True, default=0.7)
    is_archived : Mapped[bool] = mapped_column(nullable=False, default=False)
    is_pinned : Mapped[bool] = mapped_column(nullable=False, default=False)
    created_at : Mapped[DateTime] = mapped_column(nullable=False, server_default=func.now())
    updated_at : Mapped[DateTime] = mapped_column(nullable=False, server_default=func.now(), onupdate=func.now())

class Message(Base):
    __tablename__ = "messages"

    id : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    parent_message_id : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=True)
    role : Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), nullable=False)
    content : Mapped[str] = mapped_column(String(2000), nullable=False)
    token_count : Mapped[int] = mapped_column(nullable=False, default=0)
    model_id : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("models.id"), nullable=True)
    finish_reason : Mapped[str] = mapped_column(String(255), nullable=True)
    metadata : Mapped[dict] = mapped_column(JSON, nullable=True)
    created_at : Mapped[DateTime] = mapped_column(nullable=False, server_default=func.now())

class Attachment(Base):
    __tablename__ = "attachments"

    id : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=False)
    file_name : Mapped[str] = mapped_column(String(255), nullable=False)
    file_type : Mapped[str] = mapped_column(String(100), nullable=False)
    file_size : Mapped[int] = mapped_column(nullable=False)
    file_url : Mapped[str] = mapped_column(String(500), nullable=False)
    created_at : Mapped[DateTime] = mapped_column(nullable=False, server_default=func.now())
