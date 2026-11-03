import uuid
from fastapi import APIRouter, Depends, HTTPException ,  status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.modules.ai_models.services import ai_model_service
from app.core.dependencies import CurrentUser ,  AdminUser , DBSession
from app.modules.ai_models.schemas import CreateAIModel , UpdateAIModel , AIModelResponse
router = APIRouter()

@router.post("/ai-models" , response_model=AIModelResponse , status_code=status.HTTP_201_CREATED)
async def create_ai_model(ai_model_data: CreateAIModel, admin: AdminUser, db: DBSession):
    """
    Create a new AI model.
    """
    ai_model = await ai_model_service.create(db, obj_in=ai_model_data)
    return ai_model

@router.get("/ai-models", response_model=list[AIModelResponse])
async def get_ai_models(admin: AdminUser, db: DBSession):
    """
    Get a list of all AI models.
    """
    ai_models = await ai_model_service.get_multi(db)
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