from app.modules.base import CRUDBase
from app.modules.auth.models import RefreshToken
from app.modules.auth.schemes import CreateRefreshToken
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.modules.auth.utils import sha256

authentication_service = CRUDBase[RefreshToken, CreateRefreshToken, CreateRefreshToken](RefreshToken)
async def get_refresh_token_by_hash_token(db: AsyncSession, refresh_token: str , user_id: str) -> RefreshToken | None:  
    refresh_token_hash = sha256(refresh_token)
    stmt = select(RefreshToken).where(RefreshToken.user_id == user_id , RefreshToken.token_hash == refresh_token_hash)
    list_user_token = await db.execute(stmt)
    return list_user_token.scalar_one_or_none()
