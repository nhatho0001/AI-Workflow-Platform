from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
import uuid
from datetime import datetime
from app.modules.ai_models.models import AIModelProvider


class AIModelBase(BaseModel):
    provider: AIModelProvider
    model_name: str = Field(..., min_length=1, max_length=255)
    display_name: str = Field(..., min_length=1, max_length=255)
    default_params: dict | None = None
    context_window: int | None = Field(None, gt=0)
    capabilities: list[str] = []

class CreateAIModel(AIModelBase):
    is_enabled: bool = Field(default=True, description="Indicates if the AI model is enabled")
    is_default: bool = Field(default=False, description="Indicates if the AI model is the default model")

class UpdateAIModel(BaseModel):
    display_name : str | None = Field(None, description="The display name of the AI model")
    default_params: Optional[dict] | None = Field(None, description="Default parameters for the AI model")
    context_window: int | None = Field(None, gt=0)
    capabilities: list[str] | None = None
    is_enabled: bool | None = Field(None, description="Indicates if the AI model is enabled")
    is_default: bool | None = Field(None, description="Indicates if the AI model is the default model")

class AIModelResponse(AIModelBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID = Field(..., description="The unique identifier of the AI model")
    is_enabled: bool
    is_default: bool
    created_at: datetime = Field(..., description="The creation timestamp of the AI model")
    updated_at: datetime = Field(..., description="The last update timestamp of the AI model")


class AIModelPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID = Field(..., description="The unique identifier of the AI model")
    provider: AIModelProvider
    display_name: str = Field(..., min_length=1, max_length=255)
    capabilities: list[str] = []
    is_default: bool = Field(..., description="Indicates if the AI model is the default model")
    
    