from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import MembershipStatus
from app.schemas.user import UserResponse


class GroupBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None


class GroupCreate(GroupBase):
    pass


class GroupUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None


class JoinGroupRequest(BaseModel):
    invite_code: str = Field(..., min_length=4, max_length=10)


class AddStudentRequest(BaseModel):
    student_id: str


class GroupMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    student: UserResponse
    status: MembershipStatus
    joined_at: datetime


class GroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    invite_code: str
    teacher_id: str
    created_at: datetime
    updated_at: datetime
    total_students: Optional[int] = 0
    total_assignments: Optional[int] = 0


class GroupDetailResponse(GroupResponse):
    teacher: UserResponse
    members: List[GroupMemberResponse] = []
