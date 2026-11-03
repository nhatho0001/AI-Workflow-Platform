from app.core.database import Base
from sqlalchemy import String, Enum as SAEnum , ForeignKey , func , JSON , UniqueConstraint
from sqlalchemy.orm import relationship , Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from enum import Enum
import uuid


class AIModel(Base):
    __tablename__ = "ai_models"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider : Mapped[str] = mapped_column(String(255) , nullable = False)
    model_name : Mapped[str] = mapped_column(String(255) , nullable = False)
    display_name : Mapped[str] = mapped_column(String(255) , nullable = False)
    default_params : Mapped[dict] = mapped_column("default_params" , JSON, nullable=True)
    created_at : Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at : Mapped[datetime] = mapped_column(nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('provider', 'model_name', name='uq_provider_model_name'),
    )
    # Relationships
    