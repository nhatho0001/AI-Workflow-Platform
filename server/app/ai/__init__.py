"""
AI Engine. Đọc `app/ai/README.md` trước khi sửa.

Quy tắc phụ thuộc: `app.ai` không import `app.modules.*` (không biết DB/HTTP). Các module nghiệp vụ
dựng `RunContext` rồi gọi `ai_service.stream(...)`.
"""
from app.ai.context import ChatMessage, ContextBlock, ContextBuilder, ContextSource, RunContext
from app.ai.events import AIEvent, ContextRetrieved, RunCompleted, RunFailed, TextDelta, Usage
from app.ai.providers import ModelConfig
from app.ai.service import AIService, ai_service

__all__ = [
    "AIEvent",
    "AIService",
    "ChatMessage",
    "ContextBlock",
    "ContextBuilder",
    "ContextRetrieved",
    "ContextSource",
    "ModelConfig",
    "RunCompleted",
    "RunContext",
    "RunFailed",
    "TextDelta",
    "Usage",
    "ai_service",
]
