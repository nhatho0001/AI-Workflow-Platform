import uuid
from app.modules.base import CRUDBase
from app.modules.ai_models.models import AIModel
from app.modules.ai_models.schemas import CreateAIModel, UpdateAIModel


ai_model_service = CRUDBase[AIModel, CreateAIModel, UpdateAIModel](AIModel)