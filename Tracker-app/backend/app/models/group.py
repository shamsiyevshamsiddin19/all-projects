import random
import string
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.enums import MembershipStatus


def utcnow():
    return datetime.now(timezone.utc)


def generate_invite_code(length: int = 6) -> str:
    """Generate unique 6-character alphanumeric code for group joining."""
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    invite_code: Mapped[str] = mapped_column(
        String(10), unique=True, index=True, default=generate_invite_code, nullable=False
    )
    teacher_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    teacher: Mapped["User"] = relationship("User", back_populates="created_groups", foreign_keys=[teacher_id])
    memberships: Mapped[List["GroupMembership"]] = relationship(
        "GroupMembership", back_populates="group", cascade="all, delete-orphan"
    )
    assignments: Mapped[List["Assignment"]] = relationship(
        "Assignment", back_populates="group", cascade="all, delete-orphan"
    )


class GroupMembership(Base):
    __tablename__ = "group_memberships"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    group_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[MembershipStatus] = mapped_column(
        Enum(MembershipStatus, name="membership_status_enum", native_enum=False),
        default=MembershipStatus.ACTIVE,
        nullable=False,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    # Relationships
    group: Mapped["Group"] = relationship("Group", back_populates="memberships")
    student: Mapped["User"] = relationship("User", back_populates="memberships")
