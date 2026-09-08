from pydantic import BaseModel, EmailStr, Field
from app.modules.users.schemas import UserBase

class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="The email address of the user")
    password: str = Field(..., description="The password of the user")

class TokenResponse(BaseModel):
    access_token: str = Field(..., description="The access token for the user")
    refresh_token: str = Field(..., description="The refresh token for the user")

    model_config = {"from_attributes": True}

class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="The refresh token for the user")

class CreateRefreshToken(BaseModel):
    user_id: str = Field(..., description="The ID of the user")
    token_hash: str = Field(..., description="The hash of the refresh token")