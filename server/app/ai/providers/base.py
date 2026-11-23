"""
Kiểu dữ liệu & lỗi dùng chung cho tầng provider.

`ModelConfig` là ranh giới giữa DB và AI Engine: `modules/ai_models/services.to_model_config()`
chuyển bản ghi `AIModel` thành object này. AI Engine không bao giờ import SQLAlchemy model.
"""
import re
from collections.abc import Callable, Iterator
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


# ── Phân loại lỗi từ SDK provider ──────────────────────
# Chỉ dùng getattr + regex, không import SDK của từng provider → thêm provider mới không phải sửa ở đây.

_STATUS_IN_MESSAGE = re.compile(r"^\s*(\d{3})\s+[A-Z_]+")

_AUTH_ERROR = ("provider_auth_error", "API key của provider không hợp lệ hoặc không có quyền truy cập model này.")

_STATUS_ERRORS: dict[int, tuple[str, str]] = {
    401: _AUTH_ERROR,
    403: _AUTH_ERROR,
    404: ("model_not_found", "Provider không tìm thấy model này — kiểm tra model_name trong trang AI models."),
    429: ("rate_limited", "Đã vượt hạn mức gọi model (rate limit / quota). Vui lòng thử lại sau hoặc dùng API key khác."),
    503: ("model_overloaded", "Model AI đang quá tải, vui lòng thử lại sau ít phút hoặc chọn model khác."),
    529: ("model_overloaded", "Model AI đang quá tải, vui lòng thử lại sau ít phút hoặc chọn model khác."),  # Anthropic "overloaded"
}

_TIMEOUT_ERROR = ("provider_timeout", "Model AI phản hồi quá lâu, vui lòng thử lại.")


def _exception_chain(exc: BaseException) -> Iterator[BaseException]:
    """exc rồi tới các lỗi gốc (__cause__/__context__) — SDK hay bọc lỗi HTTP trong lỗi của chính nó."""
    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        yield current
        current = current.__cause__ or current.__context__


def _as_http_status(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and 100 <= value <= 599 else None


def _http_status(exc: BaseException) -> int | None:
    for err in _exception_chain(exc):
        # openai/anthropic: .status_code · google-genai: .code (int) · httpx: .response.status_code
        for candidate in (
            getattr(err, "status_code", None),
            getattr(err, "code", None),
            getattr(getattr(err, "response", None), "status_code", None),
        ):
            if (status := _as_http_status(candidate)) is not None:
                return status
        # langchain_google_genai.GoogleAPIError chỉ có message dạng "503 UNAVAILABLE. {...}"
        if match := _STATUS_IN_MESSAGE.match(str(err)):
            return int(match.group(1))
    return None


def classify_provider_error(exc: BaseException) -> tuple[str, str] | None:
    """
    Chuyển lỗi SDK provider thành (code, message an toàn cho user). None = không nhận diện được,
    caller dùng thông báo chung.
    """
    chain = list(_exception_chain(exc))
    if any(isinstance(err, TimeoutError) or "Timeout" in type(err).__name__ for err in chain):
        return _TIMEOUT_ERROR

    status = _http_status(exc)
    if status in _STATUS_ERRORS:
        return _STATUS_ERRORS[status]
    # Gemini trả 400 INVALID_ARGUMENT "API key not valid" khi sai key
    if status == 400 and any("api key" in str(err).lower() for err in chain):
        return _AUTH_ERROR
    return None
