from app.core.database import Base
from sqlalchemy import Integer, String, Enum as SAEnum , func , JSON , UniqueConstraint
from sqlalchemy.orm import relationship , Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from enum import Enum
import uuid

class AIModelProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"
    OTHER = "other"

class AIModel(Base):
    __tablename__ = "ai_models"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider : Mapped[AIModelProvider] = mapped_column(SAEnum(AIModelProvider), nullable = False , default=AIModelProvider.OPENAI)
    model_name : Mapped[str] = mapped_column(String(255) , nullable = False)
    display_name : Mapped[str] = mapped_column(String(255) , nullable = False)
    default_params : Mapped[dict] = mapped_column("default_params" , JSON, nullable=True)
    context_window : Mapped[int] = mapped_column(Integer, nullable=True)
    capabilities : Mapped[dict] = mapped_column("capabilities" , JSON, default=[], nullable=True)
    is_enabled : Mapped[bool] = mapped_column(nullable=False, default=True)
    is_default : Mapped[bool] = mapped_column(nullable=False, default=False)
    created_at : Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at : Mapped[datetime] = mapped_column(nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('provider', 'model_name', name='uq_provider_model_name'),
    )
    # Relationships
    