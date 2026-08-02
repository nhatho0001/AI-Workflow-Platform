from fastapi import APIRouter
from modules.auth.router import router as auth_router
from modules.users.router import router as user_router

api_router = APIRouter(prefix="/api/v1")

# Public — không cần JWT
api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])

# Protected — JWT được enforce BÊN TRONG từng feature router
api_router.include_router(user_router, prefix="/users", tags=["Users"])