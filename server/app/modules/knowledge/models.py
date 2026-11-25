from app.core.database import Base
from sqlalchemy import ForeignKey, Integer, String, Text, func, UniqueConstraint, text , DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import uuid
from enum import Enum
from sqlalchemy import Enum as SAEnum

class Classification(str , Enum):
    Public = "public"
    Internal = "internal"
    Department = "department"
    Restricted = "restricted"
    Confidential = "confidential"

class Status(str , Enum):
    Active = "active"
    Pending = "pending"
    Ready = "ready"
    Failed = "failed"

class SubjectType(str , Enum):
    User = "user"
    Group = "group"


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    classification: Mapped[Classification] = mapped_column(SAEnum(Classification), nullable=False, default=Classification.Internal)
    owner_group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    embedding_model_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ai_models.id", ondelete="SET NULL"), nullable=True)
    chunk_size: Mapped[int] = mapped_column(nullable=False, default=1000)
    chunk_overlap: Mapped[int] = mapped_column(nullable=False, default=200)
    is_enabled: Mapped[bool] = mapped_column(nullable=False, default=True, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("name", name="uq_knowledge_bases_name"),
    )

class KnowledgeBaseGrants(Base):
    __tablename__ = "knowledge_base_grants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kb_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False)
    subject_type: Mapped[SubjectType] = mapped_column(SAEnum(SubjectType), nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("kb_id", "subject_type", "subject_id", name="uq_knowledge_base_grants_kb_id_subject_type_subject_id"),
    )

class Documents(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(Text, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    chunk_count: Mapped[int] = mapped_column(nullable=False, default=0)
    token_count: Mapped[int] = mapped_column(nullable=False, default=0)
    status: Mapped[Status] = mapped_column(SAEnum(Status), nullable=False, default=Status.Pending)
    error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("knowledge_base_id", "file_name", name="uq_documents_knowledge_base_id_file_name"),
        UniqueConstraint("knowledge_base_id", "checksum_sha256", name="uq_documents_knowledge_base_id_checksum_sha256"),
    )

class DocumentChunks(Base):
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    kb_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(nullable=False)
    page: Mapped[int | None] = mapped_column(nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime,nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_document_chunks_document_id_chunk_index"),
    )

class ConversationKnowledgeBases(Base):
    __tablename__ = "conversation_knowledge_bases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    kb_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())