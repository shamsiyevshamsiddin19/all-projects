from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.assignment import Assignment, AssignmentAttachment
from app.models.enums import AssignmentPriority, AssignmentStatus, MembershipStatus, UserRole
from app.models.group import Group, GroupMembership
from app.models.submission import Submission
from app.models.user import User
from app.schemas.assignment import (
    AssignmentAttachmentResponse,
    AssignmentCreate,
    AssignmentDetailResponse,
    AssignmentResponse,
    AssignmentUpdate,
)
from app.schemas.user import UserResponse


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class AssignmentService:
    @staticmethod
    async def create_assignment(
        db: AsyncSession, data: AssignmentCreate, teacher: User
    ) -> AssignmentResponse:
        # Validate group or student ownership
        if data.group_id:
            group_res = await db.execute(
                select(Group).where(
                    Group.id == data.group_id,
                    Group.teacher_id == teacher.id,
                    Group.deleted_at.is_(None),
                )
            )
            if not group_res.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Belgilangan guruh sizga tegishli emas yoki topilmadi",
                )

        assignment = Assignment(
            title=data.title.strip(),
            description=data.description.strip(),
            instructions=data.instructions.strip() if data.instructions else None,
            teacher_id=teacher.id,
            group_id=data.group_id,
            individual_student_id=data.individual_student_id,
            deadline=data.deadline,
            priority=data.priority,
            max_score=data.max_score,
            status=data.status,
        )
        db.add(assignment)
        await db.commit()
        await db.refresh(assignment)

        group_name = None
        if assignment.group_id:
            g = await db.get(Group, assignment.group_id)
            if g:
                group_name = g.name

        return AssignmentResponse(
            id=assignment.id,
            title=assignment.title,
            description=assignment.description,
            instructions=assignment.instructions,
            teacher_id=assignment.teacher_id,
            group_id=assignment.group_id,
            group_name=group_name,
            individual_student_id=assignment.individual_student_id,
            deadline=assignment.deadline,
            priority=assignment.priority,
            max_score=assignment.max_score,
            status=assignment.status,
            created_at=assignment.created_at,
            updated_at=assignment.updated_at,
            attachments=[],
        )

    @staticmethod
    async def list_assignments(
        db: AsyncSession,
        user: User,
        group_id: Optional[str] = None,
        priority: Optional[AssignmentPriority] = None,
        search: Optional[str] = None,
        filter_status: Optional[str] = None,  # active, completed, overdue, all
        sort_by: str = "newest",  # newest, oldest, deadline, priority
        skip: int = 0,
        limit: int = 50,
    ) -> List[AssignmentResponse]:
        now = datetime.now(timezone.utc)

        if user.role == UserRole.TEACHER:
            query = (
                select(Assignment)
                .where(
                    Assignment.teacher_id == user.id,
                    Assignment.deleted_at.is_(None),
                )
                .options(
                    selectinload(Assignment.attachments),
                    selectinload(Assignment.submissions),
                    selectinload(Assignment.group),
                )
            )
            if group_id:
                query = query.where(Assignment.group_id == group_id)
            if priority:
                query = query.where(Assignment.priority == priority)
            if search:
                term = f"%{search.strip().lower()}%"
                query = query.where(
                    or_(
                        Assignment.title.ilike(term),
                        Assignment.description.ilike(term),
                    )
                )

            # Sorting
            if sort_by == "oldest":
                query = query.order_by(Assignment.created_at.asc())
            elif sort_by == "deadline":
                query = query.order_by(Assignment.deadline.asc())
            elif sort_by == "priority":
                query = query.order_by(Assignment.priority.desc())
            else:
                query = query.order_by(Assignment.created_at.desc())

            query = query.offset(skip).limit(limit)
            result = await db.execute(query)
            assignments = result.scalars().all()

            response = []
            for a in assignments:
                deadline_utc = ensure_utc(a.deadline)
                is_overdue = now > deadline_utc if deadline_utc else False
                attachments = [
                    AssignmentAttachmentResponse.model_validate(att)
                    for att in a.attachments
                ]
                response.append(
                    AssignmentResponse(
                        id=a.id,
                        title=a.title,
                        description=a.description,
                        instructions=a.instructions,
                        teacher_id=a.teacher_id,
                        group_id=a.group_id,
                        group_name=a.group.name if a.group else None,
                        individual_student_id=a.individual_student_id,
                        deadline=a.deadline,
                        priority=a.priority,
                        max_score=a.max_score,
                        status=a.status,
                        created_at=a.created_at,
                        updated_at=a.updated_at,
                        attachments=attachments,
                        total_submitted=len(a.submissions),
                        is_overdue=is_overdue,
                    )
                )
            return response

        else:
            # Student view: assignments in student's joined groups or direct individual assignments
            # 1. Get student groups
            mem_query = select(GroupMembership.group_id).where(
                GroupMembership.student_id == user.id,
                GroupMembership.status == MembershipStatus.ACTIVE,
            )
            mem_res = await db.execute(mem_query)
            student_group_ids = [row[0] for row in mem_res.all()]

            query = (
                select(Assignment)
                .where(
                    Assignment.deleted_at.is_(None),
                    Assignment.status == AssignmentStatus.PUBLISHED,
                    or_(
                        Assignment.group_id.in_(student_group_ids)
                        if student_group_ids
                        else False,
                        Assignment.individual_student_id == user.id,
                    ),
                )
                .options(
                    selectinload(Assignment.attachments),
                    selectinload(Assignment.submissions).selectinload(Submission.reviews),
                    selectinload(Assignment.group),
                )
            )

            if group_id:
                query = query.where(Assignment.group_id == group_id)
            if priority:
                query = query.where(Assignment.priority == priority)
            if search:
                term = f"%{search.strip().lower()}%"
                query = query.where(
                    or_(
                        Assignment.title.ilike(term),
                        Assignment.description.ilike(term),
                    )
                )

            if sort_by == "oldest":
                query = query.order_by(Assignment.created_at.asc())
            elif sort_by == "deadline":
                query = query.order_by(Assignment.deadline.asc())
            elif sort_by == "priority":
                query = query.order_by(Assignment.priority.desc())
            else:
                query = query.order_by(Assignment.created_at.desc())

            query = query.offset(skip).limit(limit)
            result = await db.execute(query)
            assignments = result.scalars().all()

            response = []
            for a in assignments:
                # Find student submission
                my_sub = next((s for s in a.submissions if s.student_id == user.id), None)
                is_sub = my_sub is not None
                sub_status = my_sub.status.value if my_sub else None
                my_score = (
                    my_sub.reviews[0].score
                    if (my_sub and my_sub.reviews and len(my_sub.reviews) > 0)
                    else None
                )
                deadline_utc = ensure_utc(a.deadline)
                is_overdue = (not is_sub) and (now > deadline_utc if deadline_utc else False)

                # Status filter
                if filter_status == "active" and (is_sub or is_overdue):
                    continue
                if filter_status == "completed" and not is_sub:
                    continue
                if filter_status == "overdue" and not is_overdue:
                    continue

                attachments = [
                    AssignmentAttachmentResponse.model_validate(att)
                    for att in a.attachments
                ]
                response.append(
                    AssignmentResponse(
                        id=a.id,
                        title=a.title,
                        description=a.description,
                        instructions=a.instructions,
                        teacher_id=a.teacher_id,
                        group_id=a.group_id,
                        group_name=a.group.name if a.group else None,
                        individual_student_id=a.individual_student_id,
                        deadline=a.deadline,
                        priority=a.priority,
                        max_score=a.max_score,
                        status=a.status,
                        created_at=a.created_at,
                        updated_at=a.updated_at,
                        attachments=attachments,
                        is_submitted_by_me=is_sub,
                        my_submission_status=sub_status,
                        my_score=my_score,
                        is_overdue=is_overdue,
                    )
                )
            return response

    @staticmethod
    async def get_assignment_detail(
        db: AsyncSession, assignment_id: str, user: User
    ) -> AssignmentDetailResponse:
        query = (
            select(Assignment)
            .where(Assignment.id == assignment_id, Assignment.deleted_at.is_(None))
            .options(
                selectinload(Assignment.attachments),
                selectinload(Assignment.teacher),
                selectinload(Assignment.group),
                selectinload(Assignment.submissions).selectinload(Submission.reviews),
            )
        )
        result = await db.execute(query)
        a = result.scalar_one_or_none()
        if not a:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vazifa topilmadi",
            )

        # RBAC/IDOR tekshiruvi: bu yerga qadar har qanday login qilgan
        # foydalanuvchi ID'ni bilsa (yoki topsa) istalgan vazifaning
        # tafsilotini ko'ra olar edi — guruhga a'zo bo'lishi shart emas edi.
        if user.role == UserRole.TEACHER:
            if a.teacher_id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Ushbu vazifa sizga tegishli emas",
                )
        else:
            is_individual_target = a.individual_student_id == user.id
            is_group_member = False
            if a.group_id:
                mem_res = await db.execute(
                    select(GroupMembership).where(
                        GroupMembership.group_id == a.group_id,
                        GroupMembership.student_id == user.id,
                        GroupMembership.status == MembershipStatus.ACTIVE,
                    )
                )
                is_group_member = mem_res.scalar_one_or_none() is not None
            if not (is_individual_target or is_group_member):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bu vazifa sizga tegishli emas",
                )

        now = datetime.now(timezone.utc)
        my_sub = next((s for s in a.submissions if s.student_id == user.id), None)
        is_sub = my_sub is not None
        sub_status = my_sub.status.value if my_sub else None
        my_score = (
            my_sub.reviews[0].score
            if (my_sub and my_sub.reviews and len(my_sub.reviews) > 0)
            else None
        )
        deadline_utc = ensure_utc(a.deadline)
        is_overdue = (not is_sub) and (now > deadline_utc if deadline_utc else False)

        attachments = [
            AssignmentAttachmentResponse.model_validate(att)
            for att in a.attachments
        ]

        return AssignmentDetailResponse(
            id=a.id,
            title=a.title,
            description=a.description,
            instructions=a.instructions,
            teacher_id=a.teacher_id,
            group_id=a.group_id,
            group_name=a.group.name if a.group else None,
            individual_student_id=a.individual_student_id,
            deadline=a.deadline,
            priority=a.priority,
            max_score=a.max_score,
            status=a.status,
            created_at=a.created_at,
            updated_at=a.updated_at,
            attachments=attachments,
            total_submitted=len(a.submissions),
            is_submitted_by_me=is_sub,
            my_submission_status=sub_status,
            my_score=my_score,
            is_overdue=is_overdue,
            teacher=UserResponse.model_validate(a.teacher),
        )

    @staticmethod
    async def update_assignment(
        db: AsyncSession, assignment_id: str, data: AssignmentUpdate, teacher: User
    ) -> AssignmentResponse:
        result = await db.execute(
            select(Assignment)
            .where(
                Assignment.id == assignment_id,
                Assignment.teacher_id == teacher.id,
                Assignment.deleted_at.is_(None),
            )
            .options(selectinload(Assignment.attachments), selectinload(Assignment.group))
        )
        a = result.scalar_one_or_none()
        if not a:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vazifa topilmadi yoki sizga tegishli emas",
            )

        if data.title is not None:
            a.title = data.title.strip()
        if data.description is not None:
            a.description = data.description.strip()
        if data.instructions is not None:
            a.instructions = data.instructions.strip()
        if data.deadline is not None:
            a.deadline = data.deadline
        if data.priority is not None:
            a.priority = data.priority
        if data.max_score is not None:
            a.max_score = data.max_score
        if data.status is not None:
            a.status = data.status

        await db.commit()
        await db.refresh(a)

        return AssignmentResponse(
            id=a.id,
            title=a.title,
            description=a.description,
            instructions=a.instructions,
            teacher_id=a.teacher_id,
            group_id=a.group_id,
            group_name=a.group.name if a.group else None,
            individual_student_id=a.individual_student_id,
            deadline=a.deadline,
            priority=a.priority,
            max_score=a.max_score,
            status=a.status,
            created_at=a.created_at,
            updated_at=a.updated_at,
            attachments=[
                AssignmentAttachmentResponse.model_validate(att)
                for att in a.attachments
            ],
        )

    @staticmethod
    async def delete_assignment(
        db: AsyncSession, assignment_id: str, teacher: User
    ) -> None:
        result = await db.execute(
            select(Assignment).where(
                Assignment.id == assignment_id,
                Assignment.teacher_id == teacher.id,
                Assignment.deleted_at.is_(None),
            )
        )
        a = result.scalar_one_or_none()
        if not a:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vazifa topilmadi yoki sizga tegishli emas",
            )

        a.deleted_at = datetime.now(timezone.utc)
        await db.commit()
