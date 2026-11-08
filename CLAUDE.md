# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

AI Workflow Platform is an open-source backend + SPA for building AI Agents and multi-step AI Workflows for businesses (in spirit similar to Copilot Studio, n8n AI, or LangGraph Platform). It's also an explicit learning project pairing **AI Engineering** (LLM integration, RAG, tool calling, multi-agent, MCP) with **Backend Engineering** (FastAPI, async SQLAlchemy, PostgreSQL, Celery, clean architecture) — see `README.md` (Vietnamese) for the vision and roadmap. Code comments and docstrings are frequently in Vietnamese.

The project is in **Phase 1** of the roadmap (Auth, PostgreSQL, Docker, User Management, Chat API skeleton, AI model catalog). There is no Celery/Redis/vector DB, no RAG, and **no LLM provider wired in** — `server/app/ai/` exists as an empty placeholder for the future AI Engine. Treat `README.md`'s architecture diagram (Workflow Engine, Tool Engine, MCP, workers…) as a design target, not a description of the code.

## Commands

### Full stack (Docker)

From the repo root: `docker compose --env-file server/.env up -d --build`
- `db` (Postgres 16, port 5432), `server` (port 8000), `web` (nginx, port 3000, proxies `/api` → `server:8000`).
- The `server` container runs `alembic upgrade head` before uvicorn, and bind-mounts `server/app` and `server/alembic` with `--reload`, so code edits hot-reload without rebuilding.
- `--env-file` is required so Postgres gets the same `DB_USER`/`DB_PASSWORD`/`DB_NAME` as the server. Inside compose, `DB_HOST`/`DB_PORT` are overridden to `db`/`5432`.

### Backend (`server/`, managed by `uv`)

Run everything from `server/` — imports use `app.` as the root (`from app.core.config import settings`), and `Settings` reads `.env` relative to the cwd.

- Setup: `cp .env.example .env`, then `uv sync`
- Dev server: `uv run uvicorn app.main:app --reload` (needs a reachable Postgres; OpenAPI docs at `/docs`)
- Migrations (Alembic, async engine, URL taken from `settings.DATABASE_URL`):
  - Apply: `uv run alembic upgrade head`
  - New: `uv run alembic revision --autogenerate -m "..."` — file names are timestamp-prefixed (`alembic.ini:file_template`)
  - A new model module **must be imported in `alembic/env.py`**, otherwise autogenerate won't see its tables.
  - Postgres enums: new enum *values* need a hand-written `ALTER TYPE ... ADD VALUE`, and downgrades must drop the enum type explicitly (see the existing migrations).

There is no test suite, linter, or formatter configured for the backend (`server/tests/` is empty, and `pyproject.toml` has no pytest/ruff config). If you add them, add the config too.

### Frontend (`web/`)

- `npm install`, `npm run dev` (Vite on 5173, proxies `/api` and `/health` to `VITE_API_PROXY_TARGET`, default `http://localhost:8000`)
- `npm run build` (`tsc -b && vite build`), `npm run lint`, `npm run typecheck`, `npm run format` (Prettier + tailwind plugin)
- No test suite.

## Backend architecture (`server/app/`)

Organized **by feature module**, not by technical layer. Ignore the `api/`/`repositories/`/`services/` layout sketched in the README; it was never built.

- `main.py`: the FastAPI app with a `UTF8JSONResponse` default (`ensure_ascii=False`, so Vietnamese text isn't escaped), plus `/health`.
- `router.py`: the root `APIRouter(prefix="/api/v1")`. It mounts `auth` (`/auth`, public), `ai_models` (`/ai-models`), `users` (`/users`) and `chat_core` (`/chat`). Auth is enforced **inside** each feature router, not at mount time.
- `core/`: `config.py` (pydantic-settings; `DATABASE_URL` is a computed `postgresql+asyncpg://` property), `database.py` (async engine, `Base`, `get_session`), `security.py` (bcrypt via passlib), `dependencies.py`, `exceptions.py` (`NotFoundException`/`ForbiddenException`).
- `modules/<name>/`: each module has `models.py`, `schemas.py` (`schemes.py` in `auth`), `service(s).py`, `router.py`. Follow this shape for new features.

Patterns to reuse:

- **Generic CRUD**: `modules/base.py:CRUDBase[Model, Create, Update]` provides `get`/`get_multi`/`create`/`update`/`remove`. It commits inside each call and converts `IntegrityError` into HTTP 409. Services instantiate it directly (`ai_model_service = CRUDBase[AIModel, CreateAIModel, UpdateAIModel](AIModel)`) and put bespoke queries next to it as module-level functions; they don't subclass it. `update` uses `model_dump(exclude_unset=True)`, so PATCH schemas should be standalone all-optional models, not subclasses of the create schema.
- **Auth dependencies**: `core/dependencies.py` chains `get_current_user → get_current_active_user → get_current_admin`. In route signatures, use the `Annotated` aliases `DBSession`, `CurrentUser` and `AdminUser` directly. Don't wrap them in another `Depends(...)`.
- **JWT**: tokens are encoded with `python-jose` and carry a `token_type` claim (`access_token` / `refresh_token`) that the dependencies and `/auth/refresh` check. Refresh tokens are stored as a **SHA-256 hash** in `refresh_tokens`, looked up by `(user_id, token_hash)`, and rotated on every refresh (delete old, insert new).
- **All primary keys are UUIDs** (`UUID(as_uuid=True)`, `default=uuid.uuid4`).
- **AI model catalog** (`modules/ai_models/`): the registry of LLMs the platform may use. `GET /ai-models` returns only enabled models as `AIModelPublic` (no `model_name`/`default_params`); everything else is admin-only. DELETE is a **soft delete** (`is_enabled=False`) because conversations reference the id. The single default model is enforced both by a partial unique index (`uq_ai_models_single_default`) and by `_clear_default` in the same transaction. `AIModelProvider` values must match the keys of the future `app/ai/providers/factory.py` registry. **Read `modules/ai_models/README.md` before changing this module.** It is the design spec, including the planned `to_model_config()` boundary between the DB and the AI Engine and a checklist for adding a provider. Its "Trạng thái hiện tại" section lists issues as of 2026-11-03, most of which have since been fixed.
- **Chat** (`modules/chat_core/`): branching conversations. `Message.parent_message_id` references `messages` itself, and `MessageService.get_thread` walks back to the root. `/chat/start` and `/chat/conversations/{id}/messages` stream SSE (`data: {"event": ..., "data": ...}`, ending with `data: [DONE]`). The LLM call is a commented-out placeholder, so the assistant reply saved today is empty. Attachment storage is also a placeholder (`file_url = /uploads/<name>`). The service layer raises `NotFoundException`/`ForbiddenException`, and the router maps them through `_handle_service_error`.

## Frontend architecture (`web/src/`)

React 19 + Vite + TypeScript, organized by feature (`features/auth`, `features/chat`, `features/users`). Each feature has its own `api.ts`, `hooks.ts` (React Query), `pages/` and `components/`.

- **Auth state**: `features/auth/store.ts` is a zustand store whose `isAuthenticated` comes from `lib/token-storage.ts` (localStorage, pub/sub). Read `useAuthStore` rather than re-deriving auth state.
- **HTTP**: `lib/api-client.ts` is an axios instance that attaches the Bearer token. On a 401 it runs a single in-flight `POST /auth/refresh` and retries the original request once.
- **Streaming**: use `lib/sse.ts:streamSSE` (as `features/chat/api.ts` does) for any streaming endpoint. Don't add one-off `EventSource`/`fetch` code.
- **Routing**: `app/router.tsx` with the guards in `app/routes/guards.tsx` (`GuestRoute`, `ProtectedRoute`, `RequireRole(["admin"])` for `/admin/users`). Chat is lazy-loaded.
- `config/env.ts` is the single place that reads `import.meta.env`.

## Known gaps and rough edges

- **The frontend doesn't use `/ai-models` yet.** It still sends a hardcoded `VITE_DEFAULT_MODEL_ID` as the `model_id` when creating conversations.
- **`model_id` isn't validated or constrained.** `Conversation.model_id` and `Message.model_id` are plain UUID columns with no FK to `ai_models`, and `chat_core` doesn't call `ai_models.services.get_enabled_or_404` yet. The ai_models README says it should.
- **CORS isn't wired up.** The `CORS_ORIGINS` setting exists, but `main.py` never adds `CORSMiddleware`. The Vite dev proxy and the nginx proxy are what make the browser side work.
- **Role checks compare strings** (`current_user.role != "admin"`). That works because `Role`/`Status` are `str` enums. Note that the `users` enums are stored by member *name* in Postgres, while `ai_model_provider` stores *values* via `values_callable`.
- `modules/auth/dependencies.py` is an empty file.
