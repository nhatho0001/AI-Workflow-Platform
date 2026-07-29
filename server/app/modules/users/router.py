from fastapi import APIRouter
from app.modules.users.service import user , get_by_email

router = APIRouter()

@router.get("/users")
def get_users():
    return user.get_users() 