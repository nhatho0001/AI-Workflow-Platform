# Module `ai_models` — Chuẩn thiết kế & hướng dẫn

> Đọc file này trước khi sửa bất cứ thứ gì trong `app/modules/ai_models/`.
> Mục **"Trạng thái hiện tại"** ở cuối liệt kê những chỗ code đang lệch khỏi chuẩn — hãy sửa theo chuẩn, đừng copy pattern sai.

## 1. Vai trò

`ai_models` là **catalog các model LLM** mà nền tảng cho phép dùng. Nó trả lời câu hỏi: *"Conversation này chạy bằng model nào, của provider nào, với tham số mặc định gì?"*

Nó **không** gọi LLM. Việc gọi LLM thuộc AI Engine (`app/ai/`). Quan hệ:

```
modules/chat_core  ──(conversation.model_id)──►  modules/ai_models  ──(ModelConfig)──►  app/ai/providers/factory.py
     (HTTP, DB)                                    (catalog, DB)                          (gọi LLM thật)
```

- `chat_core.Conversation.model_id` và `Message.model_id` trỏ tới `ai_models.id`.
- `ai_models` chuyển một bản ghi DB thành `ModelConfig` (dataclass/pydantic thuần) để AI Engine dùng — AI Engine **không** import SQLAlchemy model `AIModel`.
- Frontend lấy danh sách model qua API của module này (thay cho biến `VITE_DEFAULT_MODEL_ID` đang hardcode).

## 2. Cấu trúc file

Theo đúng 4-file shape của các module khác:

| File          | Trách nhiệm                                                                 |
|---------------|------------------------------------------------------------------------------|
| `models.py`   | SQLAlchemy model `AIModel`, enum `ProviderEnum`                              |
| `schemas.py`  | Pydantic: `AIModelCreate`, `AIModelUpdate`, `AIModelResponse`, `AIModelPublic` |
| `services.py` | `ai_model_service = CRUDBase[...]` + hàm query riêng + `to_model_config()`   |
| `router.py`   | `APIRouter`, mount trong `app/router.py` với `prefix="/ai-models"`           |

Import luôn dùng gốc `app.` (`from app.modules.ai_models.models import AIModel`). **Không** dùng `server.app...` hay import tương đối kiểu `from models import ...`.

## 3. Data model chuẩn

Bảng `ai_models`:

| Cột              | Kiểu                     | Ràng buộc                    | Ghi chú |
|------------------|--------------------------|------------------------------|---------|
| `id`             | `UUID`                   | PK, `default=uuid.uuid4`     | Cùng kiểu với `conversations.model_id` |
| `provider`       | `ProviderEnum`           | NOT NULL                     | Key để `factory` chọn adapter |
| `model_name`     | `String(255)`            | NOT NULL                     | Tên gửi lên API provider, vd `gpt-4o-mini`, `claude-sonnet-4-5`, `llama3.1:8b` |
| `display_name`   | `String(255)`            | NOT NULL                     | Tên hiển thị UI |
| `default_params` | `JSON`                   | NULL                         | Xem §4 |
| `context_window` | `Integer`                | NULL                         | Số token tối đa — dùng để cắt history |
| `capabilities`   | `JSON` (list[str])       | NOT NULL, default `[]`       | vd `["tools", "vision", "streaming"]` — graph dùng để quyết định có `bind_tools` hay không |
| `is_enabled`     | `Boolean`                | NOT NULL, default `True`     | Tắt model thay vì xoá |
| `is_default`     | `Boolean`                | NOT NULL, default `False`    | Tối đa **1** bản ghi `True` (enforce ở service) |
| `created_at`     | `datetime`               | `server_default=func.now()`  | |
| `updated_at`     | `datetime`               | `server_default`, `onupdate` | |

Unique: `(provider, model_name)` — tên constraint `uq_ai_models_provider_model_name`.

`ProviderEnum` (str Enum) — giá trị phải khớp 1-1 với key trong registry của `app/ai/providers/factory.py`:

```python
class ProviderEnum(str, Enum):
    openai = "openai"
    anthropic = "anthropic"
    openrouter = "openrouter"
    ollama = "ollama"
```

Quy tắc:
- **Không lưu API key / secret trong bảng này.** Key nằm trong `Settings` (`app/core/config.py`, đọc từ `.env`), adapter tự lấy theo `provider`.
- **Không xoá cứng** model đã được conversation dùng — set `is_enabled=False`. (`Conversation.model_id` hiện không có FK, nên xoá cứng sẽ để lại id mồ côi.)
- Mọi thay đổi schema phải đi kèm migration Alembic (`alembic revision --autogenerate -m "..."`) trong `server/alembic/versions/`, và model phải được import ở nơi `alembic/env.py` gom `Base.metadata`.

## 4. `default_params`

JSON tự do nhưng chỉ được dùng các key sau (validate trong schema bằng một Pydantic model `ModelParams`, `extra="forbid"`):

| Key                 | Kiểu    | Ví dụ  |
|---------------------|---------|--------|
| `temperature`       | float 0–2 | `0.7` |
| `max_tokens`        | int > 0 | `2048` |
| `top_p`             | float 0–1 | `1.0` |
| `stop`              | list[str] | `["\n\n"]` |

Thứ tự ưu tiên khi chạy (cao → thấp): tham số request → cấu hình conversation (`Conversation.temperature`, `system_prompt`) → `AIModel.default_params` → mặc định của adapter. Việc merge thực hiện **một chỗ duy nhất**: `services.to_model_config()`.

## 5. Schemas chuẩn

```python
class AIModelBase(BaseModel):
    provider: ProviderEnum
    model_name: str = Field(..., min_length=1, max_length=255)
    display_name: str = Field(..., min_length=1, max_length=255)
    default_params: ModelParams | None = None
    context_window: int | None = Field(None, gt=0)
    capabilities: list[str] = []

class AIModelCreate(AIModelBase):
    is_enabled: bool = True
    is_default: bool = False

class AIModelUpdate(BaseModel):            # PATCH: mọi field Optional
    display_name: str | None = None
    default_params: ModelParams | None = None
    context_window: int | None = None
    capabilities: list[str] | None = None
    is_enabled: bool | None = None
    is_default: bool | None = None
    # provider/model_name không cho sửa — muốn đổi thì tạo bản ghi mới

class AIModelResponse(AIModelBase):        # cho admin
    id: uuid.UUID
    is_enabled: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AIModelPublic(BaseModel):            # cho user thường — không lộ cấu hình nội bộ
    id: uuid.UUID
    display_name: str
    provider: ProviderEnum
    capabilities: list[str]
    is_default: bool
    model_config = ConfigDict(from_attributes=True)
```

Lưu ý: `UpdateSchema` **không** kế thừa `Base` (nếu kế thừa thì PATCH bị bắt buộc gửi đủ field). `CRUDBase.update` đã dùng `exclude_unset=True` nên chỉ field được gửi mới bị ghi.

## 6. API

Router mount: `api_router.include_router(ai_model_router, prefix="/ai-models", tags=["AI Models"])`.
Path trong `router.py` vì vậy bắt đầu từ `""` / `"/{model_id}"`, **không** lặp lại `/ai-models`.

| Method | Path                         | Quyền         | Response            | Mô tả |
|--------|------------------------------|---------------|---------------------|-------|
| GET    | `/api/v1/ai-models`          | `CurrentUser` | `list[AIModelPublic]` | Chỉ model `is_enabled=True` — frontend dùng để chọn model |
| GET    | `/api/v1/ai-models/admin`    | `AdminUser`   | `list[AIModelResponse]` | Tất cả, kèm phân trang `skip/limit` |
| GET    | `/api/v1/ai-models/{id}`     | `AdminUser`   | `AIModelResponse`   | 404 nếu không có |
| POST   | `/api/v1/ai-models`          | `AdminUser`   | `AIModelResponse` (201) | 409 nếu trùng `(provider, model_name)` (CRUDBase đã xử lý `IntegrityError`) |
| PATCH  | `/api/v1/ai-models/{id}`     | `AdminUser`   | `AIModelResponse`   | Partial update |
| DELETE | `/api/v1/ai-models/{id}`     | `AdminUser`   | 204                 | Soft delete: set `is_enabled=False` |

Khai báo route `/admin` **trước** `/{model_id}` để không bị match nhầm.

Dùng alias `Annotated` từ `app/core/dependencies.py`, **không** bọc thêm `Depends`:

```python
@router.get("", response_model=list[AIModelPublic])
async def list_enabled_models(db: DBSession, _: CurrentUser):
    return await services.get_enabled(db)

@router.post("", response_model=AIModelResponse, status_code=status.HTTP_201_CREATED)
async def create_ai_model(payload: AIModelCreate, db: DBSession, _: AdminUser):
    return await services.create(db, payload)
```

Lỗi nghiệp vụ: raise `NotFoundException` / `ForbiddenException` (`app/core/exceptions.py`) hoặc `HTTPException` — đồng bộ với `chat_core`.

## 7. Service

```python
ai_model_service = CRUDBase[AIModel, AIModelCreate, AIModelUpdate](AIModel)   # tái sử dụng, không subclass

async def get_enabled(db) -> Sequence[AIModel]: ...
async def get_default(db) -> AIModel | None: ...
async def get_enabled_or_404(db, model_id) -> AIModel: ...   # dùng bởi chat_core khi tạo conversation
async def create(db, payload) -> AIModel: ...                 # nếu is_default=True → bỏ default của bản ghi khác trong cùng transaction
async def set_default(db, model_id) -> AIModel: ...
def to_model_config(model: AIModel, overrides: dict | None = None) -> ModelConfig: ...
```

- `chat_core` khi tạo conversation phải gọi `get_enabled_or_404` để validate `model_id` (hiện tại chưa validate).
- `to_model_config` là **ranh giới duy nhất** giữa DB và AI Engine. `ModelConfig` định nghĩa ở `app/ai/providers/base.py`, không chứa object SQLAlchemy.

## 8. Thêm một provider mới — checklist

1. Thêm giá trị vào `ProviderEnum` + migration (Postgres enum cần `ALTER TYPE ... ADD VALUE`).
2. Viết adapter trong `app/ai/providers/<provider>.py` và đăng ký vào registry của `factory.py` với **cùng key**.
3. Thêm biến cấu hình (API key, base URL) vào `Settings` (Optional) và `server/.env.example`.
4. Seed ít nhất 1 bản ghi `AIModel` qua `POST /api/v1/ai-models` hoặc data migration.
5. Viết test cho factory chọn đúng adapter (không gọi mạng thật).

## 9. Testing

- Test service với DB thật (Postgres test) hoặc SQLite async nếu không dùng kiểu riêng của Postgres.
- Cần có test cho: tạo trùng → 409; PATCH partial không ghi đè field không gửi; user thường chỉ thấy model enabled; chỉ 1 `is_default`; user thường gọi API admin → 403.
- `to_model_config` là hàm thuần → unit test thứ tự ưu tiên tham số (§4).

## 10. Trạng thái hiện tại (cần sửa để đạt chuẩn)

Ghi nhận ngày 2026-11-03:

- [ ] `router.py` import `from server.app.modules.ai_models.schemas ...` → `ImportError` khi khởi động. Đổi thành `from app.modules.ai_models.schemas ...`.
- [ ] `admin: AdminUser = Depends(AdminUser)` — `AdminUser` đã là `Annotated[..., Depends(get_current_admin)]`, bọc thêm `Depends` là sai. Viết `admin: AdminUser`; tương tự dùng `db: DBSession`.
- [ ] Route khai báo `"/ai-models"` trong khi đã mount `prefix="/ai-models"` → URL thực tế thành `/api/v1/ai-models/ai-models`.
- [ ] `AIModelResponse.id` / `created_at` / `updated_at` kiểu `str` và thiếu `from_attributes=True` → lỗi validate khi trả ORM object. Dùng `uuid.UUID` / `datetime`.
- [ ] `UpdateAIModel` kế thừa `AIModelBase` nên PATCH bắt buộc gửi `provider`, `model_name`.
- [ ] `display_name` Optional ở schema nhưng `nullable=False` ở model → 409/500 khi không gửi.
- [ ] `provider` đang là `String` tự do — chuyển sang `ProviderEnum`.
- [ ] Chưa có `is_enabled`, `is_default`, `context_window`, `capabilities`; chưa có endpoint cho user thường; chưa có DELETE (soft).
- [ ] Chưa có migration Alembic cho bảng `ai_models`.
- [ ] Import thừa trong `models.py` (`SAEnum`, `ForeignKey`, `relationship`, `Enum`) và `services.py` (`uuid`).
