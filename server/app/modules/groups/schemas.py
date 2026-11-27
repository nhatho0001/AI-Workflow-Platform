from pydantic import BaseModel, Field
from app.modules.users.schemas import ResponseUser


class GroupBase(BaseModel):
    name: str = Field(..., description="The name of the group")
    description: str | None = Field(None, description="The description of the group")

class GroupMemberBase(BaseModel):
    group_id: str = Field(..., description="The ID of the group")
    user_id: str = Field(..., description="The ID of the user")
    role: str = Field(..., description="The role of the user in the group")

class GroupMemberOut(GroupMemberBase):
    user: ResponseUser
class GroupCreateResponse(GroupBase):
    id: str = Field(..., description="The ID of the group")
    create_at: str = Field(..., description="The creation timestamp of the group")
    update_at: str = Field(..., description="The last update timestamp of the group")


class GroupCreate(GroupBase):
    code: str = Field(..., description="The unique code of the group")

class GroupUpdate(GroupBase):
    pass