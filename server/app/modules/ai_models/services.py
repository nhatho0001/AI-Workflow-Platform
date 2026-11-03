import uuid

from sqlalchemy import select
from app.modules.base import CRUDBase
from app.modules.ai_models.models import AIModel
from app.modules.ai_models.schemas import CreateAIModel, UpdateAIModel


ai_model_service = CRUDBase[AIModel, CreateAIModel, UpdateAIModel](AIModel)
def get_ai_enabled_models(db) -> list[AIModel]:
    model_list = db.execute(
        select(AIModel).where(AIModel.is_enabled == True).order_by(AIModel.updated_at.asc())
    )
    return model_list.scalars().all()