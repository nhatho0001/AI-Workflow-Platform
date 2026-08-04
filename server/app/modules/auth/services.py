from app.modules.base import BaseService
from app.modules.auth.models import RefreshToken
from app.modules.auth.schemes import CreateRefreshToken
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.modules.auth.utils import verify_password

authentication_service = BaseService[RefreshToken,  CreateRefreshToken , CreateRefreshToken](RefreshToken)
async def get_refresh_token_by_hash_token(db: AsyncSession, refresh_token: str , user_id: str) -> RefreshToken | None:  
    stmt = select(RefreshToken).where(RefreshToken.user_id == user_id)
    list_user_token = await db.execute(stmt)
    result = list_user_token.scalars().filter(lambda t: verify_password(refresh_token, t.token_hash)).first()
    return result