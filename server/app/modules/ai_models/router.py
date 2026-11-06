import uuid

from fastapi import APIRouter, Query, status

from app.core.dependencies import AdminUser, CurrentUser, DBSession
from app.modules.ai_models import services
from app.modules.ai_models.schemas import AIModelPublic, AIModelResponse, CreateAIModel, UpdateAIModel

router = APIRouter()


@router.get("", response_model=list[AIModelPublic])
async def list_enabled_ai_models(_: CurrentUser, db: DBSession):
    """Danh sách model đang bật — frontend dùng để chọn model."""
    return await services.get_enabled(db)


@router.post("", response_model=AIModelResponse, status_code=status.HTTP_201_CREATED)
async def create_ai_model(payload: CreateAIModel, _: AdminUser, db: DBSession):
    """Tạo model mới. 409 nếu trùng (provider, model_name)."""
    return await services.create(db, payload)


# Khai báo /admin TRƯỚC /{model_id} để không bị match nhầm
@router.get("/admin", response_model=list[AIModelResponse])
async def list_all_ai_models(
    _: AdminUser,
    db: DBSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Tất cả model (kể cả đã tắt), có phân trang."""
    return await services.ai_model_service.get_multi(db, skip=(page - 1) * page_size, limit=page_size)


@router.get("/{model_id}", response_model=AIModelResponse)
async def get_ai_model(model_id: uuid.UUID, _: AdminUser, db: DBSession):
    return await services.get_or_404(db, model_id)


@router.patch("/{model_id}", response_model=AIModelResponse)
async def update_ai_model(model_id: uuid.UUID, payload: UpdateAIModel, _: AdminUser, db: DBSession):
    """Partial update — chỉ field được gửi mới bị ghi."""
    return await services.update(db, model_id, payload)


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ai_model(model_id: uuid.UUID, _: AdminUser, db: DBSession):
    """Soft delete: is_enabled=False (và bỏ default)."""
    await services.soft_delete(db, model_id)
