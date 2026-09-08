from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base, get_session
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship , Mapped, mapped_column
from datetime import datetime, timedelta


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id") , primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(255) , nullable=False)
    __table_args__ = (UniqueConstraint('user_id', 'token_hash', name='uq_user_token'),)
    