from collections.abc import AsyncIterator, Callable

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessageChunk

from app.ai.context import PreparedPrompt, RunContext
from app.ai.events import AIEvent, RunCompleted, TextDelta, Usage
from app.ai.providers.base import ModelConfig
from app.ai.providers.factory import create_chat_model

# Chuẩn hoá lý do dừng của các provider về bộ giá trị chung (theo OpenAI)
_FINISH_REASONS = {
    "end_turn": "stop",
    "stop_sequence": "stop",
    "max_tokens": "length",
    "tool_use": "tool_calls",
}


class ChatRunner:
    """Một lần gọi LLM, stream text. Không tool, không graph."""

    def __init__(self, model_factory: Callable[[ModelConfig], BaseChatModel] = create_chat_model) -> None:
        # Inject được model_factory → test bằng fake model, không gọi mạng
        self._model_factory = model_factory

    async def run(self, ctx: RunContext, prompt: PreparedPrompt) -> AsyncIterator[AIEvent]:
        model = self._model_factory(ctx.model)
        full: AIMessageChunk | None = None

        async for chunk in model.astream(prompt.messages):
            # Cộng dồn chunk: LangChain tự merge content, usage_metadata và response_metadata
            full = chunk if full is None else full + chunk
            if chunk.text:
                yield TextDelta(content=chunk.text)

        if full is None:
            yield RunCompleted(content="", finish_reason="stop")
            return

        usage = full.usage_metadata or {}
        raw_reason = full.response_metadata.get("finish_reason") or full.response_metadata.get("stop_reason")
        yield RunCompleted(
            content=full.text,
            finish_reason=_FINISH_REASONS.get(raw_reason, raw_reason or "stop"),
            usage=Usage(
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
            ),
        )
