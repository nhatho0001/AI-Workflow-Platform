import uuid
from fastapi import APIRouter, Depends, HTTPException, Query ,  status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.modules.ai_models.services import ai_model_service , get_ai_enabled_models
from app.core.dependencies import CurrentUser ,  AdminUser , DBSession , get_current_admin
from app.modules.ai_models.schemas import CreateAIModel , UpdateAIModel , AIModelResponse , AIModelPublic
router = APIRouter()

@router.post("/ai-models" , response_model=AIModelResponse , status_code=status.HTTP_201_CREATED)
async def create_ai_model(ai_model_data: CreateAIModel, admin: AdminUser, db: DBSession):
    """
    Create a new AI model.
    """
    ai_model = await ai_model_service.create(db, obj_in=ai_model_data)
    return ai_model

@router.get("/ai-models", response_model=list[AIModelPublic])
async def get_enabled_ai_models(current_user: CurrentUser, db: DBSession):
    """
    Get a list of all enabled AI models.
    """
    ai_models = await get_ai_enabled_models(db)
    return ai_models

@router.get("/ai-models/admin", response_model=list[AIModelResponse])
async def get_ai_models(page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: AdminUser = Depends(get_current_admin), 
    db: DBSession = Depends(get_session)):
    """
    Get a list of all AI models.
    """
    ai_models = await ai_model_service.get_multi(db, skip=page * page_size, limit=page_size)
    return ai_models

@router.get("/ai-models/{model_id}", response_model=AIModelResponse)
async def get_ai_model(model_id: uuid.UUID, admin: AdminUser, db: DBSession):
    """
    Get details of a specific AI model by its ID.
    """
    ai_model = await ai_model_service.get(db, model_id)
    if not ai_model:
        raise HTTPException(status_code=404, detail="AI model not found")
    return ai_model

@router.patch("/ai-models/{model_id}" , response_model=AIModelResponse , status_code=status.HTTP_200_OK)
async def update_ai_model(model_id: uuid.UUID, ai_model_data: UpdateAIModel, admin: AdminUser, db: DBSession):
    """
    Update an existing AI model.
    """
    ai_model = await ai_model_service.get(db, model_id)
    if not ai_model:
        raise HTTPException(status_code=404, detail="AI model not found")
    updated_ai_model = await ai_model_service.update(db, db_obj=ai_model, obj_in=ai_model_data)
    return updated_ai_model