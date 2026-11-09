"""
AIService — cửa ngõ duy nhất của AI Engine.

    RunContext ──► ContextBuilder (history + ContextSource: RAG, memory…) ──► PreparedPrompt
                                                                                 │
    AsyncIterator[AIEvent] ◄── Runner ("chat" | "agent" | "workflow"…) ◄──────────┘

AIService không ném lỗi ra ngoài: mọi lỗi được chuyển thành event `RunFailed`, nên caller chỉ cần
duyệt stream. (Riêng CancelledError khi client ngắt kết nối vẫn được để lan ra như bình thường.)
"""
import dataclasses
import logging
from collections.abc import AsyncIterator, Mapping

from app.ai.context import ContextBuilder, RunContext
from app.ai.events import AIEvent, ContextRetrieved, RunCompleted, RunFailed, TextDelta
from app.ai.providers.base import AIEngineError
from app.ai.runners import ChatRunner, Runner
from app.core.config import settings

logger = logging.getLogger(__name__)


class UnknownRunnerError(AIEngineError):
    code = "unknown_runner"


class AIService:
    def __init__(
        self,
        context_builder: ContextBuilder | None = None,
        runners: Mapping[str, Runner] | None = None,
        default_runner: str = "chat",
    ) -> None:
        self.context_builder = context_builder or ContextBuilder()
        self._runners: dict[str, Runner] = dict(runners) if runners is not None else {"chat": ChatRunner()}
        self.default_runner = default_runner

    def register_runner(self, name: str, runner: Runner) -> None:
        if name in self._runners:
            raise ValueError(f"Runner '{name}' đã được đăng ký")
        self._runners[name] = runner

    async def stream(self, ctx: RunContext, *, runner: str | None = None) -> AsyncIterator[AIEvent]:
        partial: list[str] = []
        try:
            selected = self._get_runner(runner or self.default_runner)
            prompt = await self.context_builder.build(ctx)
            sources = [block.to_source() for block in prompt.blocks]
            if sources:
                yield ContextRetrieved(sources=sources)

            async for event in selected.run(ctx, prompt):
                if isinstance(event, TextDelta):
                    partial.append(event.content)
                elif isinstance(event, RunCompleted) and sources:
                    event = dataclasses.replace(event, metadata={**event.metadata, "sources": sources})
                yield event
        except AIEngineError as exc:
            yield RunFailed(message=str(exc), code=exc.code, partial_content="".join(partial))
        except Exception as exc:
            # Lỗi từ SDK provider (sai key, rate limit, timeout…) — log đầy đủ, trả message gọn cho user
            logger.exception("AI run failed (provider=%s, model=%s)", ctx.model.provider, ctx.model.model_name)
            detail = f": {exc}" if settings.DEBUG else ""
            yield RunFailed(
                message=f"Không thể nhận phản hồi từ model AI ({type(exc).__name__}){detail}",
                code="provider_error",
                partial_content="".join(partial),
            )

    def _get_runner(self, name: str) -> Runner:
        try:
            return self._runners[name]
        except KeyError:
            raise UnknownRunnerError(f"Runner '{name}' chưa được hỗ trợ") from None


# Singleton dùng chung. Đăng ký thêm ContextSource / Runner tại đây khi có tính năng mới, vd:
#   ai_service.context_builder.add_source(RAGSource(...))
#   ai_service.register_runner("agent", AgentRunner(...))
ai_service = AIService()
