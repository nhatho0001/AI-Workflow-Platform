import uuid
from collections.abc import Sequence

from fastapi import HTTPException, status
from sqlalchemy import select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.modules.ai_models.models import AIModel
from app.modules.ai_models.schemas import CreateAIModel, UpdateAIModel
from app.modules.base import CRUDBase

ai_model_service = CRUDBase[AIModel, CreateAIModel, UpdateAIModel](AIModel)


# ── Query ──────────────────────────────────────────────

async def get_enabled(db: AsyncSession) -> Sequence[AIModel]:
    result = await db.execute(
        select(AIModel)
        .where(AIModel.is_enabled.is_(True))
        .order_by(AIModel.is_default.desc(), AIModel.display_name.asc())
    )
    return result.scalars().all()


async def get_or_404(db: AsyncSession, model_id: uuid.UUID) -> AIModel:
    ai_model = await ai_model_service.get(db, model_id)
    if ai_model is None:
        raise NotFoundException("AI model not found")
    return ai_model


async def get_enabled_or_404(db: AsyncSession, model_id: uuid.UUID) -> AIModel:
    """Dùng bởi chat_core để validate model_id khi tạo conversation."""
    ai_model = await get_or_404(db, model_id)
    if not ai_model.is_enabled:
        raise NotFoundException("AI model not found")
    return ai_model


async def get_default(db: AsyncSession) -> AIModel | None:
    result = await db.execute(
        select(AIModel).where(AIModel.is_default.is_(True), AIModel.is_enabled.is_(True))
    )
    return result.scalar_one_or_none()


# ── Mutations ──────────────────────────────────────────

async def _clear_default(db: AsyncSession, exclude_id: uuid.UUID | None = None) -> None:
    """Bỏ cờ default của các bản ghi khác — chạy trong cùng transaction với thao tác set default mới."""
    stmt = sa_update(AIModel).where(AIModel.is_default.is_(True)).values(is_default=False)
    if exclude_id is not None:
        stmt = stmt.where(AIModel.id != exclude_id)
    await db.execute(stmt)


def _bad_request(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


async def create(db: AsyncSession, payload: CreateAIModel) -> AIModel:
    if payload.is_default:
        if not payload.is_enabled:
            raise _bad_request("Cannot set a disabled model as default")
        await _clear_default(db)
    # CRUDBase.create commit cả _clear_default; nếu trùng (provider, model_name) thì rollback và trả 409
    return await ai_model_service.create(db, obj_in=payload)


async def update(db: AsyncSession, model_id: uuid.UUID, payload: UpdateAIModel) -> AIModel:
    ai_model = await get_or_404(db, model_id)
    data = payload.model_dump(exclude_unset=True)

    will_be_enabled = data.get("is_enabled", ai_model.is_enabled)
    if data.get("is_default") is True:
        if not will_be_enabled:
            raise _bad_request("Cannot set a disabled model as default")
        await _clear_default(db, exclude_id=ai_model.id)
    elif not will_be_enabled:
        # Tắt model thì không được giữ làm default
        payload.is_default = False

    return await ai_model_service.update(db, db_obj=ai_model, obj_in=payload)


async def soft_delete(db: AsyncSession, model_id: uuid.UUID) -> None:
    """Không xoá cứng: conversation cũ vẫn trỏ tới model_id này."""
    ai_model = await get_or_404(db, model_id)
    ai_model.is_enabled = False
    ai_model.is_default = False
    await db.commit()
