# AI Engine (`app/ai/`) — Kiến trúc & hướng dẫn mở rộng

> Đọc file này trước khi sửa `app/ai/`. Mục tiêu thiết kế: **thêm tính năng mới (RAG, second brain,
> agent, workflow, provider…) = thêm file mới + đăng ký 1 dòng**, không phải sửa router, frontend hay code cũ.

## 1. Luồng chạy

```
chat_core (HTTP + DB)                         app/ai (không biết DB/HTTP)
─────────────────────                         ──────────────────────────────────────────────────────
ChatService.build_run_context  ──RunContext──► AIService.stream(ctx, runner="chat")
  • ai_models.to_model_config                    │
  • MessageService.get_thread                    ├─► ContextBuilder.build(ctx)
                                                 │     ├─ ContextSource.gather() × N  (song song, lỗi/timeout bị bỏ qua)
                                                 │     ├─ system prompt + <context> blocks
                                                 │     └─ cắt history theo context_window
                                                 │            ▼ PreparedPrompt
                                                 └─► Runner.run(ctx, prompt)
                                                        └─ providers/factory.create_chat_model(ModelConfig)
ChatService.stream_reply  ◄──AsyncIterator[AIEvent]──┘
  • RunCompleted → lưu assistant message, SSE `message_done`
  • RunFailed    → lưu phần đã stream (nếu có), SSE `error`
  • event khác   → SSE nguyên văn (`event.to_payload()`)
```

## 2. Cấu trúc

| File / thư mục          | Vai trò | Điểm mở rộng |
|-------------------------|---------|--------------|
| `providers/base.py`     | `ModelConfig` (frozen, hashable), lỗi `AIEngineError`… | — |
| `providers/factory.py`  | Registry `provider key → builder`, `create_chat_model()` (có cache) | `@register_provider("key")` |
| `providers/<key>.py`    | Adapter từng provider (openai, anthropic, openrouter, ollama) | thêm file |
| `context.py`            | `RunContext`, `ChatMessage`, `ContextBlock`, `ContextSource`, `ContextBuilder` | `ContextSource` |
| `runners/`              | Chiến lược thực thi: `ChatRunner` (1 lần gọi LLM, stream) | `Runner` |
| `events.py`             | Giao thức output: `TextDelta`, `ContextRetrieved`, `RunCompleted`, `RunFailed` | thêm event |
| `service.py`            | `AIService` + singleton `ai_service` — nơi lắp ráp mọi thứ | `add_source`, `register_runner` |

## 3. Quy tắc

1. **`app.ai` không import `app.modules.*`.** Dữ liệu đi vào qua `RunContext`/`ModelConfig` (kiểu thuần). Chiều ngược lại thì được (`ai_models` import `ModelConfig`).
2. **Merge tham số model chỉ ở `ai_models.services.to_model_config()`** (request > conversation > `default_params`).
3. **API key chỉ nằm trong `Settings`** (`.env`), không lưu DB. Key để trống = provider tắt; chỉ báo lỗi (`provider_not_configured`) khi có model dùng provider đó được gọi.
4. **Runner/ContextSource cứ raise khi lỗi**: `AIService` chuyển thành `RunFailed`, `ContextBuilder` log và bỏ qua source lỗi. Không nuốt lỗi bên trong.
5. **Mọi runner kết thúc bằng đúng 1 `RunCompleted`** khi thành công — `chat_core` dựa vào đó để lưu DB.
6. Mọi thứ phải test được **không cần mạng**: `ChatRunner(model_factory=...)` nhận fake model.

## 4. Checklist: thêm provider

Ví dụ thêm Gemini:

1. `uv add langchain-google-genai` (hoặc dùng `ChatOpenAI` nếu provider có API tương thích OpenAI — như `openrouter.py`, `ollama.py`).
2. Tạo `providers/gemini.py`:
   ```python
   @register_provider("gemini")
   def build_gemini(config: ModelConfig) -> BaseChatModel:
       return ChatGoogleGenerativeAI(
           model=config.model_name,
           api_key=require_setting(settings.GEMINI_API_KEY, "GEMINI_API_KEY", "gemini"),
           **config.sampling_params(),   # đổi tên tham số nếu SDK dùng tên khác
       )
   ```
3. Import trong `providers/__init__.py`.
4. `GEMINI_API_KEY: str | None = None` trong `core/config.py` + `server/.env.example`.
5. Thêm `GEMINI = "gemini"` vào `AIModelProvider` + migration viết tay `ALTER TYPE ai_model_provider ADD VALUE 'gemini'`.
6. Tạo bản ghi model: `POST /api/v1/ai-models`.

Key trong registry **phải trùng** giá trị `AIModelProvider` (test: `registered_providers() == sorted(p.value for p in AIModelProvider)`).

## 5. Checklist: thêm nguồn ngữ cảnh (RAG, second brain, memory…)

`ContextSource` là bất kỳ object nào có `name` và `async gather(ctx) -> Sequence[ContextBlock]`:

```python
# app/ai/rag/source.py
class RAGSource:
    name = "rag"

    def __init__(self, retriever: Retriever, top_k: int = 5):
        self.retriever, self.top_k = retriever, top_k

    async def gather(self, ctx: RunContext) -> list[ContextBlock]:
        chunks = await self.retriever.search(ctx.query, user_id=ctx.user_id, k=self.top_k)
        return [
            ContextBlock(source=self.name, content=c.text, title=c.document_title,
                         score=c.score, metadata={"document_id": str(c.document_id)})
            for c in chunks
        ]
```

Đăng ký trong `service.py`: `ai_service.context_builder.add_source(RAGSource(...))`.

Có sẵn, không cần code thêm:
- Các source chạy **song song**, mỗi source có timeout (`source_timeout`, mặc định 10s); lỗi chỉ bị log.
- Block được sắp theo `score`, chèn vào system prompt dạng `<context source=... title=...>`.
- Client nhận SSE `context` (danh sách nguồn — để hiển thị trích dẫn); nguồn cũng được lưu vào `messages.metadata.sources`.

Gợi ý tổ chức:
- **RAG**: `app/ai/rag/` (chunking, embedding, retriever, `RAGSource`). Phần quản lý tài liệu (upload, bảng `documents`, pgvector) là một module nghiệp vụ mới `modules/knowledge/`, retriever được inject vào `RAGSource`.
- **Second brain / long-term memory**: `app/ai/memory/` với `MemorySource` (đọc ký ức liên quan tới `ctx.query`). Phần *ghi* ký ức (trích xuất fact sau mỗi lượt) nên chạy nền sau `RunCompleted` (Celery khi có), không chặn stream.
- Source chỉ áp dụng cho một số conversation → đọc `ctx.metadata` (vd `knowledge_base_ids`) và trả `[]` nếu không liên quan.

## 6. Checklist: thêm runner (agent, workflow)

```python
# app/ai/runners/agent.py — LangGraph + tool calling
class AgentRunner:
    def __init__(self, tools, model_factory=create_chat_model): ...

    async def run(self, ctx, prompt):
        model = self._model_factory(ctx.model)
        graph = create_react_agent(model, self.tools)          # hoặc StateGraph tự dựng
        async for ev in graph.astream_events({"messages": prompt.messages}, version="v2"):
            ...  # map sang TextDelta / ToolCallStarted / ToolCallFinished
        yield RunCompleted(content=..., usage=...)
```

- Đăng ký: `ai_service.register_runner("agent", AgentRunner(...))`; gọi `ai_service.stream(ctx, runner="agent")`.
- Chỉ dùng tool khi `ctx.model.supports("tools")` (lấy từ `AIModel.capabilities`).
- **Workflow**: `WorkflowRunner` dựng LangGraph từ định nghĩa workflow (JSON lưu trong module `modules/workflows/`), truyền vào `ctx.metadata["workflow_id"]`. Mỗi node phát event `StepStarted/StepFinished` → client tự nhận qua SSE.

## 7. Checklist: thêm event

1. Dataclass trong `events.py`, `frozen=True, slots=True`, kế thừa `_Event`, có `event: ClassVar[str] = "<tên>"`.
2. Thêm vào union `AIEvent`.
3. Thêm kiểu vào `web/src/features/chat/types.ts` (`ChatStreamEvent`) nếu frontend cần hiển thị. Router không cần sửa.

## 8. Còn thiếu / việc tiếp theo

- Test tự động (pytest + pytest-asyncio): factory chọn đúng adapter, `to_model_config` (thứ tự ưu tiên), `ContextBuilder` (source lỗi, cắt history), `AIService` với fake model.
- Đếm token thật (tokenizer theo provider) thay cho `estimate_tokens` (ước lượng `len/3`).
- Tool Engine (`app/ai/tools/`: registry + MCP client) cho `AgentRunner`.
- Lưu history cho tool message (`role="tool"` hiện bị bỏ qua khi dựng prompt).
- Một số model (họ reasoning của OpenAI) không nhận `temperature` ≠ mặc định, trong khi conversation luôn gửi `temperature` (0.7). Nếu gặp lỗi này, thêm cờ capability (vd `"no_temperature"`) và bỏ tham số trong adapter.
