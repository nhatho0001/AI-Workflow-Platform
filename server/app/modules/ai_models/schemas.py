from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
import uuid
import datetime


class AIModelBase(BaseModel):
    provider: str = Field(..., description="The provider of the AI model")
    model_name: str = Field(..., description="The name of the AI model")
    display_name: Optional[str] = Field(None, description="The display name of the AI model")

class CreateAIModel(AIModelBase):
    default_params: Optional[dict] = Field(None, description="Default parameters for the AI model")

class UpdateAIModel(BaseModel):
    provider : str | None = Field(None, description="The provider of the AI model")
    model_name : str | None = Field(None, description="The name of the AI model")
    display_name : str | None = Field(None, description="The display name of the AI model")
    default_params: Optional[dict] | None = Field(None, description="Default parameters for the AI model")

class AIModelResponse(AIModelBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID = Field(..., description="The unique identifier of the AI model")
    default_params: Optional[dict] = Field(None, description="Default parameters for the AI model")
    created_at: datetime = Field(..., description="The creation timestamp of the AI model")
    updated_at: datetime = Field(..., description="The last update timestamp of the AI model")



    
    