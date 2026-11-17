"""Unit test thuần cho `app.modules.auth.utils` — không cần DB hay HTTP."""

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from jose import ExpiredSignatureError, JWTError, jwt

from app.core.config import settings
from app.core.security import get_password_hash
from app.modules.auth import utils
from app.modules.auth.utils import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_token,
    sha256,
    verify_sha256,
)
from app.modules.users.models import Status


# ---------------------------------------------------------------- sha256


def test_sha256_matches_hashlib():
    assert sha256("abc") == hashlib.sha256(b"abc").hexdigest()


def test_sha256_is_deterministic_and_hex_64_chars():
    digest = sha256("some-refresh-token")
    assert digest == sha256("some-refresh-token")
    assert len(digest) == 64
    int(digest, 16)  # là chuỗi hex hợp lệ


def test_sha256_handles_unicode():
    assert sha256("mật khẩu") == hashlib.sha256("mật khẩu".encode("utf-8")).hexdigest()


def test_verify_sha256():
    hashed = sha256("token")
    assert verify_sha256("token", hashed) is True
    assert verify_sha256("other", hashed) is False


# ---------------------------------------------------------------- JWT


def test_access_token_contains_sub_type_and_exp():
    before = datetime.now(timezone.utc)
    token = create_access_token({"sub": "user-123"})
    payload = decode_token(token)

    assert payload["sub"] == "user-123"
    assert payload["token_type"] == "access_token"
    expected_exp = before + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    assert abs(payload["exp"] - expected_exp.timestamp()) < 5


def test_refresh_token_contains_sub_type_and_exp():
    before = datetime.now(timezone.utc)
    token = create_refresh_token({"sub": "user-123"})
    payload = decode_token(token)

    assert payload["sub"] == "user-123"
    assert payload["token_type"] == "refresh_token"
    expected_exp = before + timedelta(minutes=settings.JWT_REFRESH_TOKEN_EXPIRE_MINUTES)
    assert abs(payload["exp"] - expected_exp.timestamp()) < 5


def test_custom_expires_delta_is_respected():
    token = create_access_token({"sub": "u"}, expires_delta=timedelta(minutes=1))
    exp = decode_token(token)["exp"]
    assert abs(exp - (datetime.now(timezone.utc) + timedelta(minutes=1)).timestamp()) < 5


def test_create_token_does_not_mutate_input():
    data = {"sub": "u"}
    create_access_token(data)
    create_refresh_token(data)
    assert data == {"sub": "u"}


def test_decode_expired_token_raises():
    token = create_access_token({"sub": "u"}, expires_delta=timedelta(seconds=-1))
    with pytest.raises(ExpiredSignatureError):
        decode_token(token)


def test_decode_token_signed_with_other_secret_raises():
    forged = jwt.encode(
        {"sub": "u", "token_type": "access_token"},
        "attacker-secret",
        algorithm=settings.JWT_ALGORITHM,
    )
    with pytest.raises(JWTError):
        decode_token(forged)


def test_decode_garbage_raises():
    with pytest.raises(JWTError):
        decode_token("not-a-jwt")


# ---------------------------------------------------------------- authenticate_user
# Mock `get_by_email` để test logic thuần, không đụng DB.

PASSWORD = "Secret123!"
HASHED = get_password_hash(PASSWORD)


def _fake_user(status: Status = Status.Active):
    return SimpleNamespace(id=uuid.uuid4(), hashed_password=HASHED, status=status)


@pytest.fixture
def patch_get_by_email(monkeypatch):
    def _patch(user):
        async def fake_get_by_email(db, email):
            return user

        monkeypatch.setattr(utils, "get_by_email", fake_get_by_email)

    return _patch


async def test_authenticate_user_success(patch_get_by_email):
    user = _fake_user()
    patch_get_by_email(user)
    assert await authenticate_user(None, "a@example.com", PASSWORD) is user


async def test_authenticate_user_unknown_email(patch_get_by_email):
    patch_get_by_email(None)
    assert await authenticate_user(None, "nobody@example.com", PASSWORD) is None


async def test_authenticate_user_wrong_password(patch_get_by_email):
    patch_get_by_email(_fake_user())
    assert await authenticate_user(None, "a@example.com", "wrong-password") is None


@pytest.mark.parametrize("status", [Status.Inactive, Status.Pending])
async def test_authenticate_user_non_active(patch_get_by_email, status):
    patch_get_by_email(_fake_user(status=status))
    assert await authenticate_user(None, "a@example.com", PASSWORD) is None
