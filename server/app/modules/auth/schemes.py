from pydantic import BaseModel, EmailStr, Field
from app.modules.users.schemas import UserBase

class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="The email address of the user")
    password: str = Field(..., description="The password of the user")

class TokenResponse(BaseModel):
    access_token: str = Field(..., description="The access token for the user")
    token_type: str = Field(..., description="The type of the token, typically 'bearer'")
