from app.modules.base import CRUDBase
from app.modules.groups.models import Group, GroupMember
from server.app.modules.groups.schemas import GroupCreate, GroupMemberBase, GroupUpdate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


group_service = CRUDBase[Group, GroupCreate, GroupUpdate](Group)
group_member_service = CRUDBase[GroupMember, GroupMemberBase, GroupMemberBase](GroupMember)

async def get_user_group_ids(db: AsyncSession, user_id: int):
    result = select(GroupMember.group_id).where(GroupMember.user_id == user_id)
    return await db.execute(result).scalars().all()

async def get_is_manager(db: AsyncSession, user_id: int, group_id: int):
    result = await db.execute(select(GroupMember).where(GroupMember.user_id == user_id, GroupMember.group_id == group_id))
    return result.first()
