from http.client import HTTPException

from fastapi import APIRouter ,  Depends , status
from app.modules.users.service import user_service as crud, get_by_email
from server.app.modules.users.schemas import UserCreate , ResponseUser , UserUpdate
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/" ,  response_model=list[ResponseUser])
async def get_user(db: AsyncSession = Depends(get_session), skip: int = 0, limit: int = 100):
    return await crud.get_users(db, skip=skip, limit=limit)

@router.get("/{user_id}" ,  response_model=ResponseUser)
async def get_user_by_id(user_id: int, db: AsyncSession = Depends(get_session)):
    user = await crud.get(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/create" ,  response_model=ResponseUser , status_code=201)
async def create_user(user_in: UserCreate, db: AsyncSession = Depends(get_session)):
    existing_user = await get_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await crud.create(db, obj_in=user_in)

@router.patch("/update/{user_id}" ,  response_model=ResponseUser , status_code=200)
async def update_user(user_id: int, user_in: UserUpdate, db: AsyncSession = Depends(get_session)):
    existing_user = await crud.get(db, user_id)
    email_user = await get_by_email(db, user_in.email)
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    if email_user and email_user.id != user_in.id:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await crud.update(db, db_obj=existing_user, obj_in=user_in)