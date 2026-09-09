from fastapi import APIRouter ,  Depends , status , HTTPException
from app.modules.users.service import user_service as crud, get_by_email
from app.modules.users.schemas import UserCreate , ResponseUser , UserUpdate
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.dependencies import get_current_user , CurrentUser,  DBSession ,  AdminUser
router = APIRouter(prefix="/users", tags=["Users"] ,dependencies=[Depends(get_current_user)] )

@router.get("/" ,  response_model=list[ResponseUser])
async def get_user(db: DBSession , admin_user:  AdminUser, skip: int = 0, limit: int = 100 ):
    return await crud.get_users(db, skip=skip, limit=limit)

@router.get("/{user_id}" ,  response_model=ResponseUser)
async def get_user_by_id(user_id: int, db: DBSession,  admin_user : AdminUser):
    user = await crud.get(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/me" ,  response_model=ResponseUser)
async def get_current_user_info(current_user: CurrentUser):
    return current_user

@router.post("/create" ,  response_model=ResponseUser , status_code=201)
async def create_user(user_in: UserCreate, db: AsyncSession = Depends(get_session)):
    existing_user = await get_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await crud.create(db, obj_in=user_in)

@router.patch("/update/{user_id}"  ,response_model=ResponseUser , status_code=200)
async def update_user(user_id: int, user_in: UserUpdate, db: DBSession ,  current_user:  CurrentUser):
    user = await crud.get(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    email_user = await get_by_email(db, user_in.email)
    if email_user and email_user.id != user.id:
        raise HTTPException(status_code=400, detail="Email already registered")
    if user.id != current_user.id and current_user.role != "admin" :
        raise HTTPException(status_code = 403 ,  detail = "Forbiden!")
    return await crud.update(db, db_obj=user, obj_in=user_in)

@router.delete("/delete/{user_id}" ,  status_code=204)
async def delete_user(user_id: int, db: DBSession ,  current_user: CurrentUser):
    if user_id != current_user.id and current_user.role != "admin" :
        raise HTTPException(status_code = 403 ,  detail = "Forbiden!")
    await crud.remove(db, id=user_id)
    return {"detail": "User deleted successfully"}