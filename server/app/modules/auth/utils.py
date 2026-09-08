from pwdlib import PasswordHash
import hashlib
from app.core.config import settings
from passlib.context import CryptContext
from app.modules.users.service import get_by_email
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate, UserUpdate , UserBase
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from schemes import LoginRequest ,  TokenResponse
from typing import Any, Literal

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """
    Hashes a password using the CryptContext.

    Args:
        password: The password to be hashed.

    Returns:
        The hashed password as a string.
    """
    return pwd_context.hash(password)

def sha256(text : str) -> str:
    """
    Hashes a text using SHA-256.

    Args:
        text: The text to be hashed.

    Returns:
        The hashed text as a string.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def verify_sha256(text: str, hashed_text: str) -> bool:
    """
    Verifies a text against a SHA-256 hashed text.

    Args:
        text: The plain text to verify.
        hashed_text: The SHA-256 hashed text to compare against.

    Returns:
        True if the texts match, False otherwise.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest() == hashed_text

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against a hashed password.

    Args:
        plain_password: The plain password to verify.
        hashed_password: The hashed password to compare against.

    Returns:
        True if the passwords match, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)

async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | bool:
    user = await get_by_email(db, email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    if user.status != "active":
        return False
    return user

def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
        Creates a JWT access token.
    
        Args:
            data: The data to encode in the token.
            expires_delta: Optional expiration time in seconds. If not provided, defaults to settings.ACCESS_TOKEN_EXPIRE_MINUTES.
            token_type: The type of token to create. Must be either "access token" or "refresh token".

        Returns:
            The encoded JWT token as a string.
    """
    to_encode = data.copy()
    to_encode["token_type"] = "access_token"
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})          # claim "exp" — JWT tự reject khi hết hạn
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
        Creates a JWT refresh token.
    
        Args:
            data: The data to encode in the token.
            expires_delta: Optional expiration time in seconds. If not provided, defaults to settings.REFRESH_TOKEN_EXPIRE_MINUTES.

        Returns:
            The encoded JWT refresh token as a string.
    """
    to_encode = data.copy()
    to_encode["token_type"] = "refresh_token"
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.JWT_REFRESH_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})          # claim "exp" — JWT tự reject khi hết hạn
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str) -> dict[str, Any]:
    """
        Decodes a JWT token and returns the payload.

        Args:
            token: The JWT token to decode.

        Returns:
            The decoded payload as a dictionary.
    """
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])