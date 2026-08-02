from datetime import datetime, timedelta, timezone
import uuid
from fastapi import APIRouter, Depends, HTTPException , status
from jose import JWTError
from schemes import LoginRequest
from app.modules.users.schemas import UserBase , UserCreate
from app.modules.users.service import get_by_email , user_service
from app.core.database import get_session
from utils import create_access_token, create_refresh_token, decode_token, get_password_hash,  authenticate_user
from schemes import TokenResponse , RefreshRequest
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.post("/login")
async def login(login_request: LoginRequest ,  db: AsyncSession = Depends(get_session)):
    user = await authenticate_user(db , login_request.email, login_request.password)
    if not user:
        return HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token({"sub": user.id})
    refresh_token = create_refresh_token({"sub": user.id})
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

@router.post("/register")
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_session)):
    existing_user = await get_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user_in.password)
    user_in.hashed_password = hashed_password
    user_create = await user_service.create(obj_in=user_in)
    access_token = create_access_token({"sub": user_create.id})
    refresh_token = create_refresh_token({"sub": user_create.id})
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

@router.post("/logout")
async def logout():
    # Implement logout logic here (e.g., invalidate tokens, clear session, etc.)
    return {"message": "Logged out successfully"}

@router.post("/refresh_access_token")
async def refresh_access_token(refresh_token: str):
    # Implement logic to validate the refresh token and issue a new access token
    # For example, decode the refresh token, check its validity, and create a new access token
    try:
        payload = decode_token(refresh_token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        if payload.get("token_type") != "refresh token":
            raise HTTPException(status_code=401, detail="Invalid token type")
        new_access_token = create_access_token({"sub": user_id})
        return TokenResponse(access_token=new_access_token, refresh_token=refresh_token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_session)):
    payload = decode_token(body.refresh_token)
    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    db_user = await user_service.get(db, uuid.UUID(user_id))
    if not db_user or db_user.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    token_data = {"sub": str(db_user.id)}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )