import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.modules.ai_models.models import AIModelProvider


class ModelParams(BaseModel):
    """Các tham số mặc định được phép trong AIModel.default_params (README §4)."""
    model_config = ConfigDict(extra="forbid")

    temperature: float | None = Field(None, ge=0, le=2)
    max_tokens: int | None = Field(None, gt=0)
    top_p: float | None = Field(None, ge=0, le=1)
    stop: list[str] | None = None


def _dump_params(params: ModelParams | None) -> dict | None:
    # Chỉ lưu các key thực sự được đặt, không lưu {"max_tokens": null, ...} vào DB
    return params.model_dump(exclude_none=True) if params is not None else None


class AIModelBase(BaseModel):
    provider: AIModelProvider
    model_name: str = Field(..., min_length=1, max_length=255)
    display_name: str = Field(..., min_length=1, max_length=255)
    default_params: ModelParams | None = None
    context_window: int | None = Field(None, gt=0)
    capabilities: list[str] = []

    @field_serializer("default_params")
    def _serialize_params(self, params: ModelParams | None) -> dict | None:
        return _dump_params(params)


class CreateAIModel(AIModelBase):
    is_enabled: bool = Field(default=True, description="Indicates if the AI model is enabled")
    is_default: bool = Field(default=False, description="Indicates if the AI model is the default model")


class UpdateAIModel(BaseModel):
    """PATCH: chỉ field được gửi mới bị ghi. provider/model_name không cho sửa — muốn đổi thì tạo bản ghi mới."""
    display_name: str | None = Field(None, min_length=1, max_length=255)
    default_params: ModelParams | None = None  # gửi null = xoá tham số mặc định
    context_window: int | None = Field(None, gt=0)  # gửi null = bỏ giới hạn
    capabilities: list[str] | None = None
    is_enabled: bool | None = None
    is_default: bool | None = None

    @field_validator("display_name", "capabilities", "is_enabled", "is_default")
    @classmethod
    def _not_null(cls, value):
        # Các cột này NOT NULL trong DB: không gửi thì bỏ qua, gửi null thì báo 422
        if value is None:
            raise ValueError("Field cannot be null")
        return value

    @field_serializer("default_params")
    def _serialize_params(self, params: ModelParams | None) -> dict | None:
        return _dump_params(params)


class AIModelResponse(AIModelBase):
    """Cho admin — đầy đủ cấu hình."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    is_enabled: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime


class AIModelPublic(BaseModel):
    """Cho user thường — không lộ model_name/default_params."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    provider: AIModelProvider
    display_name: str
    capabilities: list[str]
    is_default: bool
