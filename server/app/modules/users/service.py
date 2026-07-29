from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import User
from app.modules.users.schemas import UserCreate , UserUpdate
from app.modules.base import CRUDBase


user = CRUDBase[User ,  UserCreate , UserUpdate](User)

async def get_by_email(db: AsyncSession ,  email_address: str) ->  User | None:
    result = await db.execute(select(User).where(User.email == email_address))
    return result.scalar_one_or_none()