from fastapi import APIRouter, HTTPException
from schemes import LoginRequest
from app.modules.users.schemas import UserBase
from app.modules.users.service import get_by_email
router = APIRouter()

@router.post("/login")
async def login(login_request: LoginRequest):
    db_user = await get_by_email(login_request.email)
    if not db_user:
        return HTTPException(status_code=404, detail="Invalid email not found")
    