from fastapi import APIRouter
from app.modules.groups.services import group_service, group_member_service, get_user_group_ids, get_is_manager
from app.modules.groups.schemas import GroupCreate, GroupUpdate, GroupMemberBase , GroupCreateResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.groups.models import Group, GroupMember
from app.core.dependencies import CurrentUser, AdminUser , DBSession
from fastapi import HTTPException
from sqlalchemy import select


router = APIRouter(
    prefix="/groups",
    tags=["groups"],
    responses={404: {"description": "Not found"}},
)

@router.get("/" , summary="Get all groups" , response_model=list[GroupCreateResponse])
async def get_groups(db: DBSession , admin_user: AdminUser , skip: int = 0, limit: int = 100):
    return await group_service.get_multi(db, skip, limit)

@router.get("/{group_id}" , summary="Get group by ID" , response_model=GroupCreateResponse)
async def get_group(group_id: int, db: DBSession ,  admin_user: AdminUser):
    group = await group_service.get(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group

@router.post("/create" , summary="Create a new group" , response_model=GroupCreateResponse)
async def create_group(group_in: GroupCreate, db: DBSession , admin_user: AdminUser):
    return await group_service.create(db, obj_in=group_in)

@router.patch("/{group_id}" , summary="Update a group" , response_model=GroupCreateResponse)
async def update_group(group_id: int, group_in: GroupUpdate, db: DBSession , admin_user: AdminUser):
    group = await group_service.get(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return await group_service.update(db, db_obj=group, obj_in=group_in)

@router.delete("/{group_id}" , summary="Delete a group" , status_code=204)
async def delete_group(group_id: int, db: DBSession , admin_user: AdminUser):
    group = await group_service.get(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    await group_service.remove(db, id=group_id)