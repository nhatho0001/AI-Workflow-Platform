"""Fixtures dùng chung cho test backend.

- Env vars được set TRƯỚC khi import `app.*`, vì `Settings()` đọc config lúc import.
  Env var thắng `.env`, nên test không phụ thuộc vào `.env` trên máy dev.
- DB là SQLite in-memory (aiosqlite) thay cho Postgres: mỗi test có engine riêng,
  chỉ tạo các bảng cần cho auth (`users`, `refresh_tokens`).
"""

import os

os.environ.update(
    {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_USER": "test",
        "DB_PASSWORD": "test",
        "DB_NAME": "test",
        "JWT_SECRET_KEY": "test-jwt-secret-key",
        "JWT_ALGORITHM": "HS256",
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "30",
        "JWT_REFRESH_TOKEN_EXPIRE_MINUTES": "10080",
        "SECRET_KEY": "test-secret-key",
        "DEBUG": "false",
    }
)

from collections.abc import AsyncIterator, Awaitable, Callable  # noqa: E402

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.database import Base, get_session  # noqa: E402
from app.main import app  # noqa: E402
from app.modules.auth.models import RefreshToken  # noqa: E402
from app.modules.users.models import Role, Status, User  # noqa: E402
from app.modules.users.service import create_user  # noqa: E402

AUTH_TABLES = [User.__table__, RefreshToken.__table__]


@pytest.fixture
async def session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    # StaticPool: mọi session dùng chung 1 connection → cùng 1 DB in-memory
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=AUTH_TABLES)

    yield async_sessionmaker(engine, expire_on_commit=False)

    await engine.dispose()


@pytest.fixture
async def db_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Session để test seed dữ liệu và kiểm tra DB sau khi gọi API."""
    async with session_factory() as session:
        yield session


@pytest.fixture
async def client(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncClient]:
    async def override_get_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


UserFactory = Callable[..., Awaitable[User]]


@pytest.fixture
def user_factory(db_session: AsyncSession) -> UserFactory:
    """Tạo user thật trong DB (password được hash bằng bcrypt như production)."""

    async def _create(
        *,
        email: str = "alice@example.com",
        password: str = "Secret123!",
        name: str = "Alice",
        role: Role = Role.User,
        status: Status = Status.Active,
    ) -> User:
        return await create_user(
            db_session, name=name, email=email, password=password, role=role, status=status
        )

    return _create
