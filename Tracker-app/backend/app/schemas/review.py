from typing import Optional
from pydantic import BaseModel, Field
from app.models.enums import ReviewDecision


class ReviewCreate(BaseModel):
    score: int = Field(..., ge=0, le=1000)
    feedback_text: Optional[str] = None
    decision: ReviewDecision = ReviewDecision.APPROVED
