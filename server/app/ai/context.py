"""
Ngữ cảnh của một lượt chạy AI và nơi lắp ráp prompt.

- `RunContext`: đầu vào của AI Engine (do `chat_core` dựng từ DB). Chỉ chứa kiểu thuần, không ORM.
- `ContextSource`: điểm mở rộng cho RAG, second brain / long-term memory, hồ sơ user, tài liệu
  workspace… Mỗi source trả về các `ContextBlock`; `ContextBuilder` gom song song và chèn vào system prompt.
- `ContextBuilder`: gom block + cắt history theo context window → `PreparedPrompt` cho runner.
"""
import asyncio
import logging
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol, runtime_checkable
from uuid import UUID

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.ai.providers.base import ModelConfig

logger = logging.getLogger(__name__)

Role = Literal["system", "user", "assistant", "tool"]


@dataclass(frozen=True, slots=True)
class ChatMessage:
    role: Role
    content: str


@dataclass(frozen=True, slots=True)
class ContextBlock:
    """Một mẩu kiến thức đưa vào prompt."""
    source: str  # tên ContextSource tạo ra block, vd "rag", "memory"
    content: str
    title: str | None = None
    score: float | None = None  # độ liên quan (nếu có) — dùng để sắp xếp
    metadata: dict[str, Any] = field(default_factory=dict)  # vd document_id, url, chunk_index

    def to_source(self) -> dict[str, Any]:
        """Thông tin trích dẫn gửi cho client — không kèm nội dung."""
        return {"source": self.source, "title": self.title, "score": self.score, "metadata": self.metadata}


@dataclass(slots=True)
class RunContext:
    model: ModelConfig
    messages: list[ChatMessage]  # thread root → hiện tại; phần tử cuối là tin nhắn mới của user
    system_prompt: str | None = None
    user_id: UUID | None = None
    conversation_id: UUID | None = None
    metadata: dict[str, Any] = field(default_factory=dict)  # dữ liệu tự do cho source/runner (vd workspace_id)

    @property
    def query(self) -> str:
        """Tin nhắn user mới nhất — đầu vào tự nhiên cho truy vấn RAG/memory."""
        for message in reversed(self.messages):
            if message.role == "user":
                return message.content
        return ""


@runtime_checkable
class ContextSource(Protocol):
    name: str

    async def gather(self, ctx: RunContext) -> Sequence[ContextBlock]: ...


@dataclass(frozen=True, slots=True)
class PreparedPrompt:
    messages: list[BaseMessage]
    blocks: list[ContextBlock]


def estimate_tokens(text: str) -> int:
    # Ước lượng thô, thiên về dư (tiếng Việt tốn token hơn tiếng Anh). Thay bằng tokenizer thật khi cần.
    return len(text) // 3 + 4


_LC_MESSAGE = {"user": HumanMessage, "assistant": AIMessage}

_CONTEXT_INSTRUCTION = (
    "Use the reference context below when it is relevant to the user's request. "
    "If it does not contain the answer, say so instead of inventing facts."
)


class ContextBuilder:
    def __init__(
        self,
        sources: Iterable[ContextSource] = (),
        *,
        source_timeout: float = 10.0,
        max_history_messages: int = 50,
        default_output_reserve: int = 1024,
    ) -> None:
        self._sources: list[ContextSource] = list(sources)
        self.source_timeout = source_timeout
        self.max_history_messages = max_history_messages
        self.default_output_reserve = default_output_reserve

    def add_source(self, source: ContextSource) -> None:
        if any(s.name == source.name for s in self._sources):
            raise ValueError(f"ContextSource '{source.name}' đã được đăng ký")
        self._sources.append(source)

    async def build(self, ctx: RunContext) -> PreparedPrompt:
        blocks = await self._gather(ctx)
        system = self._render_system(ctx.system_prompt, blocks)
        history = self._trim_history(ctx, reserved=estimate_tokens(system.content) if system else 0)
        messages: list[BaseMessage] = [system] if system else []
        messages += [_LC_MESSAGE[m.role](content=m.content) for m in history]
        return PreparedPrompt(messages=messages, blocks=blocks)

    async def _gather(self, ctx: RunContext) -> list[ContextBlock]:
        if not self._sources:
            return []
        results = await asyncio.gather(
            *(asyncio.wait_for(source.gather(ctx), self.source_timeout) for source in self._sources),
            return_exceptions=True,
        )
        blocks: list[ContextBlock] = []
        for source, result in zip(self._sources, results):
            # Một source lỗi (vector DB down, timeout…) không được làm hỏng cả lượt chat
            if isinstance(result, BaseException):
                logger.warning("ContextSource %s failed: %r", source.name, result)
                continue
            blocks.extend(result)
        blocks.sort(key=lambda b: b.score if b.score is not None else 0.0, reverse=True)
        return blocks

    @staticmethod
    def _render_system(system_prompt: str | None, blocks: Sequence[ContextBlock]) -> SystemMessage | None:
        parts = [system_prompt.strip()] if system_prompt and system_prompt.strip() else []
        if blocks:
            rendered = "\n\n".join(
                f'<context source="{b.source}"' + (f' title="{b.title}"' if b.title else "") + f">\n{b.content}\n</context>"
                for b in blocks
            )
            parts.append(f"{_CONTEXT_INSTRUCTION}\n\n{rendered}")
        return SystemMessage(content="\n\n".join(parts)) if parts else None

    def _trim_history(self, ctx: RunContext, reserved: int) -> list[ChatMessage]:
        # Bỏ message rỗng (vd assistant reply lỗi) và role chưa hỗ trợ (system lấy từ system_prompt, tool chưa có)
        usable = [m for m in ctx.messages if m.role in _LC_MESSAGE and m.content.strip()]
        usable = usable[-self.max_history_messages:]

        if ctx.model.context_window:
            budget = ctx.model.context_window - reserved - (ctx.model.max_tokens or self.default_output_reserve)
            kept: list[ChatMessage] = []
            for message in reversed(usable):
                cost = estimate_tokens(message.content)
                # Luôn giữ tin nhắn mới nhất, kể cả khi vượt budget — để provider báo lỗi rõ ràng
                if kept and cost > budget:
                    break
                kept.append(message)
                budget -= cost
            usable = list(reversed(kept))

        # Một số provider (Anthropic) yêu cầu lượt đầu tiên là của user
        while len(usable) > 1 and usable[0].role != "user":
            usable.pop(0)
        return usable
