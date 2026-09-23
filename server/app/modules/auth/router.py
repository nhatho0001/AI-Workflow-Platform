import uuid
from fastapi import APIRouter, Depends, HTTPException , status
from jose import JWTError
from app.modules.auth.schemes import CreateRefreshToken, LoginRequest
from app.modules.users.schemas import UserRegister
from app.modules.users.service import create_user as create_user_service, get_by_email , user_service
from app.core.database import get_session
from app.modules.auth.utils import create_access_token, create_refresh_token, decode_token, authenticate_user , sha256
from app.modules.auth.schemes import TokenResponse , RefreshRequest
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.auth.services import authentication_service, get_refresh_token_by_hash_token
from app.core.dependencies import CurrentUser

router = APIRouter()

@router.post("/login")
async def login(login_request: LoginRequest ,  db: AsyncSession = Depends(get_session)):
    user = await authenticate_user(db , login_request.email, login_request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    refresh_token_hash = sha256(refresh_token)

    await authentication_service.create(db, obj_in=CreateRefreshToken(user_id=user.id, token_hash=refresh_token_hash))
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

@router.post("/register")
async def register(user_in: UserRegister, db: AsyncSession = Depends(get_session)):
    existing_user = await get_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = await create_user_service(db, name=user_in.name, email=user_in.email, password=user_in.password)
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    await authentication_service.create(db, obj_in=CreateRefreshToken(user_id=user.id, token_hash=sha256(refresh_token)))
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

@router.post("/logout")
async def logout(current_user: CurrentUser, refresh_token: RefreshRequest, db: AsyncSession = Depends(get_session)):
    db_refresh_token = await get_refresh_token_by_hash_token(db, refresh_token.refresh_token, current_user.id)
    if db_refresh_token:
        await authentication_service.remove(db, id=db_refresh_token.id)
    return {"message": "Logged out successfully"}

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_session)):
    try:
        payload = decode_token(body.refresh_token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user_id: str | None = payload.get("sub")
    if not user_id or payload.get("token_type") != "refresh_token":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    db_user = await user_service.get(db, user_uuid)
    if not db_user or db_user.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    db_refresh_token = await get_refresh_token_by_hash_token(db, body.refresh_token, user_uuid)
    if not db_refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token not found or invalid")

    token_data = {"sub": str(db_user.id)}
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    # Rotate: xoá refresh token cũ, lưu hash của refresh token mới
    await authentication_service.remove(db, id=db_refresh_token.id)
    await authentication_service.create(
        db, obj_in=CreateRefreshToken(user_id=db_user.id, token_hash=sha256(new_refresh_token))
    )

    return TokenResponse(access_token=new_access_token, refresh_token=new_refresh_token)