"""
Runner = chiến lược thực thi một lượt AI. Mọi runner cùng nhận (RunContext, PreparedPrompt) và
phát ra chuỗi AIEvent, kết thúc bằng đúng một `RunCompleted` khi thành công.

- `ChatRunner` (chat.py): 1 lần gọi LLM, stream text.
- Sau này: `AgentRunner` (LangGraph + tool calling), `WorkflowRunner` (chạy graph do user thiết kế)…
  Đăng ký qua `ai_service.register_runner(name, runner)`; lỗi cứ raise, AIService sẽ chuyển thành RunFailed.
"""
from collections.abc import AsyncIterator
from typing import Protocol

from app.ai.context import PreparedPrompt, RunContext
from app.ai.events import AIEvent


class Runner(Protocol):
    def run(self, ctx: RunContext, prompt: PreparedPrompt) -> AsyncIterator[AIEvent]: ...
