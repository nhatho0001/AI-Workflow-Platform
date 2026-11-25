from pydantic import BaseModel, Field


class GroupBase(BaseModel):
    name: str = Field(..., description="The name of the group")
    code: str = Field(..., description="The unique code of the group")
    description: str | None = Field(None, description="The description of the group")

class GroupMemberBase(BaseModel):
    group_id: str = Field(..., description="The ID of the group")
    user_id: str = Field(..., description="The ID of the user")
    role: str = Field(..., description="The role of the user in the group")

class GroupCreate(GroupBase):
    pass

class GroupUpdate(GroupBase):
    pass