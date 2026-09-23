from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.modules.users.models import Role, Status, User
from app.modules.users.schemas import UserCreate , UserUpdate
from app.modules.base import CRUDBase


user_service = CRUDBase[User ,  UserCreate , UserUpdate](User)

async def get_by_email(db: AsyncSession ,  email_address: str) ->  User | None:
    result = await db.execute(select(User).where(User.email == email_address))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    *,
    name: str,
    email: str,
    password: str,
    role: Role = Role.User,
    status: Status = Status.Active,
) -> User:
    user = User(
        name=name,
        email=email,
        hashed_password=get_password_hash(password),
        role=role,
        status=status,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user