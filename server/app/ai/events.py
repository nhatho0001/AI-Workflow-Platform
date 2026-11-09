"""
Giao thức sự kiện giữa AI Engine và tầng HTTP.

Mọi runner (chat, agent, workflow…) đều phát ra một chuỗi `AIEvent`. `chat_core` chỉ xử lý riêng
`RunCompleted` (lưu DB) và `RunFailed`; mọi event khác được chuyển thẳng xuống client qua
`to_payload()`. Nhờ vậy thêm event mới (tool call, bước workflow, trích dẫn RAG…) không phải sửa router.

Thêm event mới: tạo dataclass có `event: ClassVar[str]` và thêm vào union `AIEvent`.
"""
from dataclasses import asdict, dataclass, field
from typing import Any, ClassVar


@dataclass(frozen=True, slots=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def to_dict(self) -> dict[str, int]:
        return {**asdict(self), "total_tokens": self.total_tokens}


@dataclass(frozen=True, slots=True)
class _Event:
    event: ClassVar[str]

    def to_payload(self) -> dict[str, Any]:
        """Định dạng SSE chung của dự án: {"event": ..., "data": ...}."""
        return {"event": self.event, "data": asdict(self)}


@dataclass(frozen=True, slots=True)
class TextDelta(_Event):
    event: ClassVar[str] = "delta"
    content: str


@dataclass(frozen=True, slots=True)
class ContextRetrieved(_Event):
    """Ngữ cảnh đã đưa vào prompt (RAG, memory…) — frontend dùng để hiển thị nguồn trích dẫn."""
    event: ClassVar[str] = "context"
    sources: list[dict[str, Any]]


@dataclass(frozen=True, slots=True)
class RunCompleted(_Event):
    event: ClassVar[str] = "completed"
    content: str
    finish_reason: str = "stop"
    usage: Usage = field(default_factory=Usage)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RunFailed(_Event):
    event: ClassVar[str] = "error"
    message: str
    code: str = "ai_error"
    partial_content: str = ""


AIEvent = TextDelta | ContextRetrieved | RunCompleted | RunFailed
