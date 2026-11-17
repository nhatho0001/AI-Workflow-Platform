"""Test API `POST /api/v1/auth/login` (FastAPI app thật + SQLite in-memory)."""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.modules.auth import utils as auth_utils
from app.modules.auth.models import RefreshToken
from app.modules.auth.utils import decode_token, sha256
from app.modules.users.models import Status

LOGIN_URL = "/api/v1/auth/login"
EMAIL = "alice@example.com"
PASSWORD = "Secret123!"


async def _refresh_tokens(db_session, user_id: uuid.UUID) -> list[RefreshToken]:
    result = await db_session.execute(
        select(RefreshToken).where(RefreshToken.user_id == user_id)
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------- success


async def test_login_success_returns_token_pair(client, user_factory):
    user = await user_factory(email=EMAIL, password=PASSWORD)

    resp = await client.post(LOGIN_URL, json={"email": EMAIL, "password": PASSWORD})

    assert resp.status_code == 200
    body = resp.json()
    assert set(body) == {"access_token", "refresh_token"}

    access = decode_token(body["access_token"])
    refresh = decode_token(body["refresh_token"])
    assert access["sub"] == str(user.id)
    assert access["token_type"] == "access_token"
    assert refresh["sub"] == str(user.id)
    assert refresh["token_type"] == "refresh_token"


async def test_login_stores_sha256_of_refresh_token_not_plaintext(
    client, user_factory, db_session
):
    user = await user_factory(email=EMAIL, password=PASSWORD)

    resp = await client.post(LOGIN_URL, json={"email": EMAIL, "password": PASSWORD})
    refresh_token = resp.json()["refresh_token"]

    rows = await _refresh_tokens(db_session, user.id)
    assert len(rows) == 1
    assert rows[0].token_hash == sha256(refresh_token)
    assert rows[0].token_hash != refresh_token


async def test_access_token_from_login_is_accepted_by_protected_route(client, user_factory):
    await user_factory(email=EMAIL, password=PASSWORD)
    tokens = (await client.post(LOGIN_URL, json={"email": EMAIL, "password": PASSWORD})).json()

    # Refresh token không được dùng thay access token
    resp = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers={"Authorization": f"Bearer {tokens['refresh_token']}"},
    )
    assert resp.status_code == 401

    resp = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert resp.status_code == 200


@pytest.mark.xfail(
    strict=True,
    reason=(
        "BUG: 2 lần login cùng 1 giây sinh ra refresh token y hệt (payload chỉ có "
        "sub/token_type/exp, exp làm tròn theo giây) → trùng uq_user_token → 409. "
        "Fix: thêm claim duy nhất, vd 'jti': uuid4().hex."
    ),
)
async def test_login_twice_creates_two_distinct_sessions(
    client, user_factory, db_session, monkeypatch
):
    # Cố định "now" để 2 lần login chắc chắn rơi vào cùng 1 giây (test không flaky)
    fixed_now = datetime(2026, 1, 1, tzinfo=timezone.utc)

    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now

    monkeypatch.setattr(auth_utils, "datetime", FrozenDatetime)
    user = await user_factory(email=EMAIL, password=PASSWORD)

    first = await client.post(LOGIN_URL, json={"email": EMAIL, "password": PASSWORD})
    second = await client.post(LOGIN_URL, json={"email": EMAIL, "password": PASSWORD})

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["refresh_token"] != second.json()["refresh_token"]
    assert len(await _refresh_tokens(db_session, user.id)) == 2


# ---------------------------------------------------------------- invalid credentials


async def test_login_wrong_password(client, user_factory, db_session):
    user = await user_factory(email=EMAIL, password=PASSWORD)

    resp = await client.post(LOGIN_URL, json={"email": EMAIL, "password": "wrong-password"})

    assert resp.status_code == 401
    assert resp.json() == {"detail": "Invalid credentials"}
    assert await _refresh_tokens(db_session, user.id) == []


async def test_login_unknown_email(client, user_factory):
    await user_factory(email=EMAIL, password=PASSWORD)

    resp = await client.post(
        LOGIN_URL, json={"email": "nobody@example.com", "password": PASSWORD}
    )

    assert resp.status_code == 401
    assert resp.json() == {"detail": "Invalid credentials"}


async def test_login_wrong_password_and_unknown_email_look_identical(client, user_factory):
    """Không để lộ email nào đã tồn tại (user enumeration)."""
    await user_factory(email=EMAIL, password=PASSWORD)

    wrong_pw = await client.post(LOGIN_URL, json={"email": EMAIL, "password": "nope"})
    no_user = await client.post(
        LOGIN_URL, json={"email": "nobody@example.com", "password": "nope"}
    )

    assert wrong_pw.status_code == no_user.status_code == 401
    assert wrong_pw.json() == no_user.json()


async def test_login_password_is_case_sensitive(client, user_factory):
    await user_factory(email=EMAIL, password=PASSWORD)

    resp = await client.post(LOGIN_URL, json={"email": EMAIL, "password": PASSWORD.lower()})

    assert resp.status_code == 401


@pytest.mark.parametrize("status", [Status.Inactive, Status.Pending])
async def test_login_non_active_user_is_rejected(client, user_factory, db_session, status):
    user = await user_factory(email=EMAIL, password=PASSWORD, status=status)

    resp = await client.post(LOGIN_URL, json={"email": EMAIL, "password": PASSWORD})

    assert resp.status_code == 401
    assert resp.json() == {"detail": "Invalid credentials"}
    assert await _refresh_tokens(db_session, user.id) == []


# ---------------------------------------------------------------- request validation


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"email": EMAIL},
        {"password": PASSWORD},
        {"email": "not-an-email", "password": PASSWORD},
        {"email": None, "password": PASSWORD},
        {"email": EMAIL, "password": None},
    ],
    ids=["empty", "missing-password", "missing-email", "invalid-email", "null-email", "null-password"],
)
async def test_login_invalid_body_returns_422(client, payload):
    resp = await client.post(LOGIN_URL, json=payload)
    assert resp.status_code == 422


async def test_login_rejects_form_encoded_body(client, user_factory):
    """Endpoint nhận JSON, không phải OAuth2 form (username/password)."""
    await user_factory(email=EMAIL, password=PASSWORD)

    resp = await client.post(LOGIN_URL, data={"username": EMAIL, "password": PASSWORD})

    assert resp.status_code == 422


async def test_login_get_method_not_allowed(client):
    resp = await client.get(LOGIN_URL)
    assert resp.status_code == 405
