from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import AssignmentPriority, AssignmentStatus
from app.schemas.user import UserResponse


class AssignmentAttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    file_name: str
    file_path: str
    file_type: str
    file_size: int
    uploaded_at: datetime


class AssignmentBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    description: str = Field(..., min_length=2)
    instructions: Optional[str] = None
    group_id: Optional[str] = None
    individual_student_id: Optional[str] = None
    deadline: datetime
    priority: AssignmentPriority = AssignmentPriority.MEDIUM
    max_score: int = Field(100, ge=1, le=1000)
    status: AssignmentStatus = AssignmentStatus.PUBLISHED


class AssignmentCreate(AssignmentBase):
    pass


class AssignmentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    instructions: Optional[str] = None
    deadline: Optional[datetime] = None
    priority: Optional[AssignmentPriority] = None
    max_score: Optional[int] = Field(None, ge=1, le=1000)
    status: Optional[AssignmentStatus] = None


class AssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str
    instructions: Optional[str] = None
    teacher_id: str
    group_id: Optional[str] = None
    group_name: Optional[str] = None
    individual_student_id: Optional[str] = None
    deadline: datetime
    priority: AssignmentPriority
    max_score: int
    status: AssignmentStatus
    created_at: datetime
    updated_at: datetime
    attachments: List[AssignmentAttachmentResponse] = []
    
    # Extra stats
    total_assigned: Optional[int] = 0
    total_submitted: Optional[int] = 0
    is_submitted_by_me: Optional[bool] = False
    my_submission_status: Optional[str] = None
    my_score: Optional[int] = None
    is_overdue: Optional[bool] = False


class AssignmentDetailResponse(AssignmentResponse):
    teacher: UserResponse
