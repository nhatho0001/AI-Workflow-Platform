"""
Kiểu dữ liệu & lỗi dùng chung cho tầng provider.

`ModelConfig` là ranh giới giữa DB và AI Engine: `modules/ai_models/services.to_model_config()`
chuyển bản ghi `AIModel` thành object này. AI Engine không bao giờ import SQLAlchemy model.
"""
from collections.abc import Callable
from typing import Any

from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, ConfigDict


class ModelConfig(BaseModel):
    """Cấu hình đã merge xong (request → conversation → AIModel.default_params). Bất biến & hashable."""
    model_config = ConfigDict(frozen=True)

    provider: str  # khớp key trong registry của factory.py và giá trị AIModelProvider
    model_name: str  # tên gửi lên API provider, vd "gpt-4o-mini"
    temperature: float | None = None
    max_tokens: int | None = None
    top_p: float | None = None
    stop: tuple[str, ...] | None = None
    context_window: int | None = None
    capabilities: frozenset[str] = frozenset()

    def supports(self, capability: str) -> bool:
        return capability in self.capabilities

    def sampling_params(self) -> dict[str, Any]:
        """Tham số sinh text đã bỏ giá trị None — adapter truyền thẳng vào constructor LangChain."""
        params = {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "stop": list(self.stop) if self.stop else None,
        }
        return {k: v for k, v in params.items() if v is not None}


# Adapter: nhận ModelConfig, trả về chat model LangChain đã cấu hình sẵn key/base_url.
ProviderBuilder = Callable[[ModelConfig], BaseChatModel]


# ── Lỗi ────────────────────────────────────────────────

class AIEngineError(Exception):
    """Lỗi nghiệp vụ của AI Engine — message an toàn để hiển thị cho user."""
    code = "ai_error"


class UnknownProviderError(AIEngineError):
    code = "unknown_provider"


class ProviderNotConfiguredError(AIEngineError):
    code = "provider_not_configured"


def require_setting(value: str | None, env_name: str, provider: str) -> str:
    """Lấy API key/URL bắt buộc; thiếu thì báo lỗi rõ ràng thay vì để SDK trả 401 khó hiểu."""
    if not value:
        raise ProviderNotConfiguredError(f"Provider '{provider}' chưa được cấu hình: thiếu {env_name}")
    return value
