from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ActivityPoint(BaseModel):
    label: str  # e.g., "Dush", "Sesh", "Chor", ... or "Mon", "Tue"
    value: int


class GroupPerformanceItem(BaseModel):
    group_id: str
    group_name: str
    total_students: int
    completion_rate: float
    average_score: float


class StudentRankingItem(BaseModel):
    student_id: str
    student_name: str
    avatar_url: Optional[str] = None
    group_name: Optional[str] = None
    completed_tasks: int
    average_score: float


class TeacherDashboardStats(BaseModel):
    total_students: int
    total_groups: int
    active_assignments: int
    completed_assignments: int
    pending_reviews: int
    late_submissions: int
    average_score: float
    completion_rate: float
    weekly_activity: List[ActivityPoint] = []
    group_performances: List[GroupPerformanceItem] = []
    top_students: List[StudentRankingItem] = []


class StudentDashboardStats(BaseModel):
    active_tasks: int
    completed_tasks: int
    overdue_tasks: int
    average_score: float
    completion_rate: float
    total_score_points: int
    max_possible_points: int
    weekly_progress: List[ActivityPoint] = []
