import uuid

from sqlalchemy import Sequence, select
from app.modules.base import CRUDBase
from app.modules.ai_models.models import AIModel
from app.modules.ai_models.schemas import CreateAIModel, UpdateAIModel
from fastapi import HTTPException


ai_model_service = CRUDBase[AIModel, CreateAIModel, UpdateAIModel](AIModel)
async def get_ai_enabled_models(db) -> Sequence[AIModel]:
    model_list = await db.execute(
        select(AIModel).where(AIModel.is_enabled == True).order_by(AIModel.updated_at.asc())
    )
    return model_list.scalars().all()

async def delete_soft_ai_model(db, model_id: uuid.UUID):
    ai_model = await ai_model_service.get(db, model_id)
    if not ai_model:
        raise HTTPException(status_code=404, detail="AI model not found")
    ai_model.is_enabled = False
    await db.commit()

async def get_ai_model_default(db) -> AIModel | None:  
    model = await db.execute(
        select(AIModel).where(AIModel.is_default == True, AIModel.is_enabled == True)
    )
    return model.scalar_one_or_none()

async def create_ai_model_service(db, model: CreateAIModel) -> AIModel:
    if model.is_default == True:
        if model.is_enabled == False:
            raise HTTPException(status_code=400, detail="Cannot set a disabled model as default")
        result = await db.execute(select(AIModel).where(AIModel.is_default == True)).with_for_update()
        for default_model in result.scalars():
            default_model.is_default = False
        
    return await ai_model_service.create(db, obj_in=model)