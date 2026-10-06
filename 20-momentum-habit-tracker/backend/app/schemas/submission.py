from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import ReviewDecision, SubmissionStatus
from app.schemas.user import UserResponse


class SubmissionAttachmentCreate(BaseModel):
    file_name: str
    file_path: str
    file_type: str
    file_size: int


class SubmissionAttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    file_name: str
    file_path: str
    file_type: str
    file_size: int
    uploaded_at: datetime


class SubmissionCreate(BaseModel):
    answer_text: Optional[str] = None
    attachments: List[SubmissionAttachmentCreate] = []


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    submission_id: str
    reviewer_id: str
    score: int
    feedback_text: Optional[str] = None
    decision: ReviewDecision
    reviewed_at: datetime
    reviewer: Optional[UserResponse] = None


class SubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    assignment_id: str
    student_id: str
    answer_text: Optional[str] = None
    status: SubmissionStatus
    is_late: bool
    submitted_at: datetime
    created_at: datetime
    student: Optional[UserResponse] = None
    attachments: List[SubmissionAttachmentResponse] = []
    reviews: List[ReviewResponse] = []
    latest_score: Optional[int] = None
    latest_feedback: Optional[str] = None
