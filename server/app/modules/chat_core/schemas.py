from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum
import uuid
from app.modules.chat_core.models import RoleEnum


# ─────────────────────────────────────────────
# Attachment Schemas
# ─────────────────────────────────────────────

class AttachmentBase(BaseModel):
    file_name: str = Field(..., max_length=255)
    file_type: str = Field(..., max_length=100)
    file_size: int = Field(..., gt=0)
    file_url: str = Field(..., max_length=500)


class AttachmentCreate(AttachmentBase):
    message_id: uuid.UUID


class AttachmentResponse(AttachmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    message_id: uuid.UUID
    created_at: datetime


# ─────────────────────────────────────────────
# Message Schemas
# ─────────────────────────────────────────────

class MessageBase(BaseModel):
    role: RoleEnum
    content: str = Field(..., max_length=2000)
    metadata: Optional[dict[str, Any]] = None


class MessageCreate(MessageBase):
    conversation_id: uuid.UUID
    parent_message_id: Optional[uuid.UUID] = None
    model_id: Optional[uuid.UUID] = None


class MessageUpdate(BaseModel):
    content: Optional[str] = Field(None, max_length=2000)
    metadata: Optional[dict[str, Any]] = None


class MessageResponse(MessageBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    parent_message_id: Optional[uuid.UUID] = None
    model_id: Optional[uuid.UUID] = None
    token_count: int
    finish_reason: Optional[str] = None
    created_at: datetime
    attachments: List[AttachmentResponse] = []


# ─────────────────────────────────────────────
# Conversation Schemas
# ─────────────────────────────────────────────

class ConversationBase(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    system_prompt: Optional[str] = Field(None, max_length=1000)
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0)


class ConversationCreate(ConversationBase):
    model_id: uuid.UUID
    folder_id: Optional[uuid.UUID] = None


class ConversationUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    system_prompt: Optional[str] = Field(None, max_length=1000)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    folder_id: Optional[uuid.UUID] = None
    is_archived: Optional[bool] = None
    is_pinned: Optional[bool] = None
    model_id: Optional[uuid.UUID] = None


class ConversationResponse(ConversationBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    model_id: uuid.UUID
    folder_id: Optional[uuid.UUID] = None
    is_archived: bool
    is_pinned: bool
    created_at: datetime
    updated_at: datetime


class ConversationWithMessagesResponse(ConversationResponse):
    messages: List[MessageResponse] = []


# ─────────────────────────────────────────────
# Chat (Send Message) Schemas
# ─────────────────────────────────────────────

class ChatMessageInput(BaseModel):
    """Payload gửi tin nhắn trong conversation"""
    content: str = Field(..., min_length=1, max_length=2000)
    parent_message_id: Optional[uuid.UUID] = None
    metadata: Optional[dict[str, Any]] = None


class ChatRequest(BaseModel):
    """Tạo conversation mới + gửi tin nhắn đầu tiên"""
    model_id: uuid.UUID
    folder_id: Optional[uuid.UUID] = None
    title: Optional[str] = Field(None, max_length=255)
    system_prompt: Optional[str] = Field(None, max_length=1000)
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0)
    message: str = Field(..., min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    conversation: ConversationResponse
    user_message: MessageResponse
    assistant_message: MessageResponse


# ─────────────────────────────────────────────
# Pagination
# ─────────────────────────────────────────────

class PaginatedConversations(BaseModel):
    items: List[ConversationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class PaginatedMessages(BaseModel):
    items: List[MessageResponse]
    total: int
    page: int
    page_size: int
    total_pages: int