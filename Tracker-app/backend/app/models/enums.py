import enum


class UserRole(str, enum.Enum):
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"


class AssignmentPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class AssignmentStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class SubmissionStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    GRADED = "GRADED"
    RESUBMIT_REQUESTED = "RESUBMIT_REQUESTED"
    LATE = "LATE"


class ReviewDecision(str, enum.Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RESUBMIT = "RESUBMIT"


class MembershipStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    REMOVED = "REMOVED"


class NotificationType(str, enum.Enum):
    NEW_ASSIGNMENT = "NEW_ASSIGNMENT"
    DEADLINE_APPROACHING = "DEADLINE_APPROACHING"
    ASSIGNMENT_SUBMITTED = "ASSIGNMENT_SUBMITTED"
    ASSIGNMENT_REVIEWED = "ASSIGNMENT_REVIEWED"
    RESUBMISSION_REQUESTED = "RESUBMISSION_REQUESTED"
    GROUP_INVITATION = "GROUP_INVITATION"
    SYSTEM = "SYSTEM"
