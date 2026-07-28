from fastapi import APIRouter
from app.modules.users.controller import UserController


router = APIRouter()

@router.get("/users")
def get_users():
    return UserController.get_users()