from datetime import datetime
from enum import Enum
import uuid

from sqlalchemy import JSON, Enum as SAEnum, Index, Integer, String, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AIModelProvider(str, Enum):
    """Giá trị phải khớp 1-1 với key trong registry của AI Engine (app/ai/providers/factory.py)."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"


class AIModel(Base):
    __tablename__ = "ai_models"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # values_callable: lưu giá trị ("openai") thay vì tên member ("OPENAI") vào Postgres enum
    provider: Mapped[AIModelProvider] = mapped_column(
        SAEnum(
            AIModelProvider,
            name="ai_model_provider",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    default_params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    context_window: Mapped[int | None] = mapped_column(Integer, nullable=True)
    capabilities: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list, server_default=text("'[]'"))
    is_enabled: Mapped[bool] = mapped_column(nullable=False, default=True, server_default=text("true"))
    is_default: Mapped[bool] = mapped_column(nullable=False, default=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("provider", "model_name", name="uq_ai_models_provider_model_name"),
        # Partial unique index: DB đảm bảo tối đa 1 bản ghi is_default = true
        Index("uq_ai_models_single_default", "is_default", unique=True, postgresql_where=text("is_default")),
    )
