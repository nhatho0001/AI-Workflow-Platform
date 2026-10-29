# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

AI Workflow Platform is an open-source Python/FastAPI backend for building AI Agents and multi-step AI Workflows for businesses (in spirit similar to Microsoft Copilot Studio, n8n AI, or LangGraph Platform). It's also an explicit learning project pairing **AI Engineering** (LLM integration, RAG, tool calling, multi-agent, MCP) with **Backend Engineering** (FastAPI, async SQLAlchemy, PostgreSQL, Celery, clean architecture) — see `README.md` (in Vietnamese) for the full vision and roadmap.

The repo currently contains only the backend, in `server/`. There is no frontend, no Celery/Redis/vector-DB integration, no RAG, and no LLM provider wired in yet — the project is early in **Phase 1** of the roadmap (Auth, PostgreSQL, Docker, User Management, Chat API skeleton). Treat `README.md`'s architecture diagram and module list (Workflow Engine, AI Engine, Tool Engine, MCP, Celery workers, etc.) as a design target, not a description of what exists in code today.

## Commands

Run from `server/` (the FastAPI project root, dependency-managed with `uv`, lockfile `uv.lock`):

- Install/sync dependencies: `uv sync`
- Run the dev server: `uv run uvicorn app.main:app --reload` — see the import-path caveat below; this may need `--app-dir` or a different cwd depending on which files you've touched.
- Docker build: `docker build -t ai-workflow-server .` from `server/` — currently **broken**, see below.

There is no test suite, linter, or formatter configured (`server/tests/` and `server/alembic/` exist as empty scaffold directories; `pyproject.toml` has no `[tool.pytest]`/`[tool.ruff]`/`[tool.black]` sections; no `.github/workflows`). Don't assume `pytest`/`ruff` commands work — if you add them, wire up the config too.

## Architecture

Backend code lives under `server/app/`, organized **by feature module**, not by technical layer:

```
app/
├── main.py              # FastAPI() app, mounts api_router, defines /health
├── router.py            # root APIRouter; includes each module's router under /api/v1
├── core/
│   ├── config.py          # pydantic-settings Settings, loaded from server/.env
│   ├── database.py        # async SQLAlchemy engine, Base, get_session() dependency
│   ├── dependencies.py    # get_current_user → get_current_active_user → get_current_admin
│   │                       # + Annotated shortcuts: DBSession, CurrentUser, AdminUser
│   └── exceptions.py      # NotFoundException / ForbiddenException (HTTPException subclasses)
└── modules/
    ├── base.py             # generic CRUDBase[Model, CreateSchema, UpdateSchema] repository
    ├── auth/                # login/register/refresh/logout, RefreshToken model
    ├── users/               # User model (Role/Status enums), user CRUD endpoints
    └── chat_core/           # Conversation/Message/Attachment models, SSE chat streaming
```

Each feature module (`modules/<name>/`) follows the same four-file shape: `models.py` (SQLAlchemy `Base` subclasses), `schemas.py`/`schemes.py` (Pydantic request/response models), `service(s).py` (business logic + queries), `router.py` (`APIRouter`, wired into `app/router.py`). Follow this layout for new features rather than the layered `api/`/`repositories/`/`services/` structure sketched in the README — that structure was never built.

Patterns worth reusing:

- **Generic CRUD** — `modules/base.py:CRUDBase` provides `get`/`get_multi`/`create`/`update`/`remove` for any model. Feature services instantiate it directly (e.g. `user_service = CRUDBase[User, UserCreate, UserUpdate](User)` in `modules/users/service.py`) and add bespoke query functions (e.g. `get_by_email`) alongside it, rather than subclassing it.
- **Auth dependency chain** — `core/dependencies.py` layers `get_current_user → get_current_active_user → get_current_admin` on top of `oauth2_scheme` + JWT decoding. Prefer the `DBSession` / `CurrentUser` / `AdminUser` `Annotated` aliases in new routes instead of repeating `Depends(...)`.
- **JWT auth** — access + refresh tokens are signed via `pyjwt`/`python-jose` (`modules/auth/utils.py`). Refresh tokens are stored **hashed** (`passlib`/`pwdlib`) in the `refresh_tokens` table (`modules/auth/models.py`) and validated by scanning a user's tokens and verifying the hash (`modules/auth/services.py:get_refresh_token_by_hash_token`), not by an indexed lookup.
- **Chat/message tree** — `chat_core` models a branching conversation: `Message.parent_message_id` self-references `messages`, and `chat_core/services.py:MessageService.get_thread` walks parents back to the root. Its router streams responses as SSE (`text/event-stream`) with the actual LLM call left as a placeholder comment — no provider is wired in yet despite the README listing OpenAI/Claude/Gemini/Ollama/OpenRouter. **Note: `chat_core.router` is not mounted in `app/router.py` yet** (only `auth_router` and `user_router` are included), so none of its endpoints are actually reachable today.

## Known issues in the current code

The codebase is early-stage with some real rough edges — worth knowing so you don't mistake pre-existing breakage for something your change caused:

- **Mixed import roots.** Most files import with `server/` as the root (`from app.core.config import settings`, `from app.modules.auth.models import ...`), but `app/main.py`, `app/router.py`, `modules/auth/router.py`, and `modules/auth/services.py` import as if `app/` itself were the root (`from core.config import settings`, `from schemes import ...`, `from modules.auth.router import router`, `from utils import ...`). These two styles can't both resolve from a single `cwd`/`PYTHONPATH` — check the actual import style used in whichever file you're editing before adding new imports.
- **`chat_core` isn't fully wired.** `modules/chat_core/router.py` imports `get_db` from `app.core.database` (only `get_session` is defined there) and imports `User` from `app.modules.auth.models` (the `User` model actually lives in `app.modules.users.models`).
- **`auth/services.py` imports a class that doesn't exist.** `authentication_service = BaseService[RefreshToken, ...](RefreshToken)` imports `BaseService` from `app.modules.base`, but that module only defines `CRUDBase` — this `ImportError`s, breaking the whole auth router that depends on it.
- **`users/router.py` calls a method `CRUDBase` doesn't have.** `GET /users/` calls `crud.get_users(db, skip=skip, limit=limit)`, but `CRUDBase` only defines `get_multi`, not `get_users`.
- **`User.id` type is inconsistent across modules.** `modules/users/models.py` defines `User.id` as an `int`, but `modules/chat_core/models.py` targets `ForeignKey("users.id")` from a Postgres `UUID` column — these can't both be right against the same table.
- **Missing settings.** `core/database.py` reads `settings.DATABASE_URL`, and `modules/auth/utils.py` reads `settings.JWT_REFRESH_TOKEN_EXPIRE_MINUTES` — neither field exists on the `Settings` class in `core/config.py` (only the discrete `DB_*` fields and `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` are defined).
- **Duplicate schema definitions.** `LoginRequest` is defined in both `modules/auth/schemes.py` and `modules/users/schemas.py` — check both when touching login/auth request shapes.
- **Dependency list is incomplete.** `core/config.py` imports `pydantic-settings`, but it isn't listed in `server/pyproject.toml`'s `dependencies`. Separately, `pwdlib[argon2]` is installed but unused — password hashing actually goes through `passlib`'s bcrypt `CryptContext`.
- **`CORS_ORIGINS` setting exists but isn't used.** `main.py` never calls `app.add_middleware(CORSMiddleware, ...)`, so the setting currently has no effect.
- **`server/Dockerfile` is stale.** It `COPY requirements.txt` and `pip install`s from it, but the project has no `requirements.txt` — dependencies are managed via `uv` (`pyproject.toml` + `uv.lock`). The Dockerfile will fail to build as-is.
- **`server/.env` is present but empty**, and there's no `.env.example`. Required vars (all non-optional, per `core/config.py`): `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`, `SECRET_KEY`. Optional: `APP_NAME`, `APP_VERSION`, `DEBUG`, `CORS_ORIGINS`.
- **No migrations.** `server/alembic/` exists but is empty (no `env.py`/versions) — the DB schema currently exists only as SQLAlchemy model definitions, not as tracked migrations.
