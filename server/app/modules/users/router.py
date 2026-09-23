import uuid

from fastapi import APIRouter ,  Depends , status , HTTPException
from app.modules.users.service import user_service as crud, create_user as create_user_service, get_by_email
from app.modules.users.schemas import UserCreate , ResponseUser , UserUpdate
from app.core.security import get_password_hash
from app.core.dependencies import get_current_user , CurrentUser,  DBSession ,  AdminUser
router = APIRouter(tags=["Users"] ,dependencies=[Depends(get_current_user)] )

@router.get("/" ,  response_model=list[ResponseUser])
async def get_user(db: DBSession , admin_user:  AdminUser, skip: int = 0, limit: int = 100 ):
    return await crud.get_multi(db, skip=skip, limit=limit)

@router.get("/me" ,  response_model=ResponseUser)
async def get_current_user_info(current_user: CurrentUser):
    return current_user

@router.get("/{user_id}" ,  response_model=ResponseUser)
async def get_user_by_id(user_id: uuid.UUID, db: DBSession,  admin_user : AdminUser):
    user = await crud.get(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/create" ,  response_model=ResponseUser , status_code=201)
async def create_user(user_in: UserCreate, db: DBSession, admin_user: AdminUser):
    existing_user = await get_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await create_user_service(
        db,
        name=user_in.name,
        email=user_in.email,
        password=user_in.password,
        role=user_in.role,
        status=user_in.status,
    )

@router.patch("/update/{user_id}"  ,response_model=ResponseUser , status_code=200)
async def update_user(user_id: uuid.UUID, user_in: UserUpdate, db: DBSession ,  current_user:  CurrentUser):
    if user_id != current_user.id and current_user.role != "admin" :
        raise HTTPException(status_code = 403 ,  detail = "Forbiden!")
    user = await crud.get(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user_in.email and user_in.email != user.email:
        email_user = await get_by_email(db, user_in.email)
        if email_user and email_user.id != user.id:
            raise HTTPException(status_code=400, detail="Email already registered")

    update_data = user_in.model_dump(exclude_unset=True, exclude={"password"})
    if user_in.password:
        update_data["hashed_password"] = get_password_hash(user_in.password)
    for field, value in update_data.items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user

@router.delete("/delete/{user_id}" ,  status_code=204)
async def delete_user(user_id: uuid.UUID, db: DBSession ,  current_user: CurrentUser):
    if user_id != current_user.id and current_user.role != "admin" :
        raise HTTPException(status_code = 403 ,  detail = "Forbiden!")
    await crud.remove(db, id=user_id)