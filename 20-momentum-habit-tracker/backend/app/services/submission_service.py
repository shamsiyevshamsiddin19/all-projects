from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.assignment import Assignment
from app.models.enums import (
    MembershipStatus,
    NotificationType,
    ReviewDecision,
    SubmissionStatus,
    UserRole,
)
from app.models.group import GroupMembership
from app.models.notification import Notification
from app.models.review import Review
from app.models.submission import Submission, SubmissionAttachment
from app.models.user import User
from app.schemas.review import ReviewCreate
from app.schemas.submission import (
    ReviewResponse,
    SubmissionAttachmentResponse,
    SubmissionCreate,
    SubmissionResponse,
)
from app.schemas.user import UserResponse


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class SubmissionService:
    @staticmethod
    async def submit_assignment(
        db: AsyncSession, assignment_id: str, data: SubmissionCreate, student: User
    ) -> SubmissionResponse:
        # 1. Fetch assignment
        res = await db.execute(
            select(Assignment).where(
                Assignment.id == assignment_id, Assignment.deleted_at.is_(None)
            )
        )
        assignment = res.scalar_one_or_none()
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vazifa topilmadi",
            )

        # IDOR tekshiruvi: bu bo'lmasa, har qanday talaba assignment_id'ni
        # bilib (yoki topib) o'ziga tegishli bo'lmagan — hatto boshqa
        # o'qituvchining guruhidagi — vazifaga ham javob topshira olar edi.
        is_individual_target = assignment.individual_student_id == student.id
        is_group_member = False
        if assignment.group_id:
            mem_res = await db.execute(
                select(GroupMembership).where(
                    GroupMembership.group_id == assignment.group_id,
                    GroupMembership.student_id == student.id,
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
        deadline_utc = ensure_utc(assignment.deadline)
        # Check if deadline passed
        is_late = (now > deadline_utc) if deadline_utc else False

        # 2. Check if existing submission exists
        sub_res = await db.execute(
            select(Submission)
            .where(
                Submission.assignment_id == assignment_id,
                Submission.student_id == student.id,
            )
            .options(
                selectinload(Submission.attachments),
                selectinload(Submission.reviews),
            )
        )
        submission = sub_res.scalar_one_or_none()

        if submission:
            # Update existing submission (resubmission)
            submission.answer_text = data.answer_text.strip() if data.answer_text else None
            submission.submitted_at = now
            submission.is_late = is_late
            submission.status = SubmissionStatus.SUBMITTED

            # Replace attachments if new ones provided
            if data.attachments:
                # Remove previous attachments
                for old_att in submission.attachments:
                    await db.delete(old_att)
                submission.attachments = [
                    SubmissionAttachment(
                        submission_id=submission.id,
                        file_name=att.file_name,
                        file_path=att.file_path,
                        file_type=att.file_type,
                        file_size=att.file_size,
                    )
                    for att in data.attachments
                ]
        else:
            # Create new submission
            submission = Submission(
                assignment_id=assignment_id,
                student_id=student.id,
                answer_text=data.answer_text.strip() if data.answer_text else None,
                status=SubmissionStatus.LATE if is_late else SubmissionStatus.SUBMITTED,
                is_late=is_late,
                submitted_at=now,
            )
            db.add(submission)
            await db.flush()

            if data.attachments:
                for att in data.attachments:
                    new_att = SubmissionAttachment(
                        submission_id=submission.id,
                        file_name=att.file_name,
                        file_path=att.file_path,
                        file_type=att.file_type,
                        file_size=att.file_size,
                    )
                    db.add(new_att)

        # Notify teacher
        teacher_notification = Notification(
            user_id=assignment.teacher_id,
            title="Yangi vazifa topshirildi",
            body=f"{student.full_name} '{assignment.title}' vazifasini topshirdi.",
            type=NotificationType.ASSIGNMENT_SUBMITTED,
            payload={"assignment_id": assignment.id, "submission_id": submission.id},
        )
        db.add(teacher_notification)

        await db.commit()
        await db.refresh(submission)

        return await SubmissionService.get_submission_detail(db, submission.id, student)

    @staticmethod
    async def get_submission_detail(
        db: AsyncSession, submission_id: str, user: User
    ) -> SubmissionResponse:
        # Expire session state to ensure fresh relations
        db.expire_all()
        query = (
            select(Submission)
            .where(Submission.id == submission_id)
            .options(
                selectinload(Submission.attachments),
                selectinload(Submission.reviews).selectinload(Review.reviewer),
                selectinload(Submission.student),
                selectinload(Submission.assignment),
            )
        )
        result = await db.execute(query)
        sub = result.scalar_one_or_none()

        if not sub:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topshiriq ishi topilmadi",
            )

        # RBAC Check: Must be student who submitted or teacher who owns assignment
        if user.role == UserRole.STUDENT and sub.student_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Siz boshqa talabaning ishini ko'ra olmaysiz",
            )
        elif user.role == UserRole.TEACHER and sub.assignment.teacher_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Ushbu vazifa sizga tegishli emas",
            )

        # Sort reviews by reviewed_at
        sorted_reviews = sorted(sub.reviews, key=lambda r: r.reviewed_at)

        reviews_resp = [
            ReviewResponse(
                id=r.id,
                submission_id=r.submission_id,
                reviewer_id=r.reviewer_id,
                score=r.score,
                feedback_text=r.feedback_text,
                decision=r.decision,
                reviewed_at=r.reviewed_at,
                reviewer=UserResponse.model_validate(r.reviewer) if r.reviewer else None,
            )
            for r in sorted_reviews
        ]

        latest_score = reviews_resp[-1].score if reviews_resp else None
        latest_feedback = reviews_resp[-1].feedback_text if reviews_resp else None

        return SubmissionResponse(
            id=sub.id,
            assignment_id=sub.assignment_id,
            student_id=sub.student_id,
            answer_text=sub.answer_text,
            status=sub.status,
            is_late=sub.is_late,
            submitted_at=sub.submitted_at,
            created_at=sub.created_at,
            student=UserResponse.model_validate(sub.student) if sub.student else None,
            attachments=[
                SubmissionAttachmentResponse.model_validate(att)
                for att in sub.attachments
            ],
            reviews=reviews_resp,
            latest_score=latest_score,
            latest_feedback=latest_feedback,
        )

    @staticmethod
    async def list_assignment_submissions(
        db: AsyncSession, assignment_id: str, teacher: User
    ) -> List[SubmissionResponse]:
        # Validate teacher ownership of assignment
        a_res = await db.execute(
            select(Assignment).where(
                Assignment.id == assignment_id,
                Assignment.teacher_id == teacher.id,
                Assignment.deleted_at.is_(None),
            )
        )
        if not a_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vazifa topilmadi yoki sizga tegishli emas",
            )

        query = (
            select(Submission)
            .where(Submission.assignment_id == assignment_id)
            .options(
                selectinload(Submission.attachments),
                selectinload(Submission.reviews).selectinload(Review.reviewer),
                selectinload(Submission.student),
            )
            .order_by(Submission.submitted_at.desc())
        )
        result = await db.execute(query)
        submissions = result.scalars().all()

        response = []
        for sub in submissions:
            reviews_resp = [
                ReviewResponse(
                    id=r.id,
                    submission_id=r.submission_id,
                    reviewer_id=r.reviewer_id,
                    score=r.score,
                    feedback_text=r.feedback_text,
                    decision=r.decision,
                    reviewed_at=r.reviewed_at,
                    reviewer=UserResponse.model_validate(r.reviewer) if r.reviewer else None,
                )
                for r in sub.reviews
            ]
            response.append(
                SubmissionResponse(
                    id=sub.id,
                    assignment_id=sub.assignment_id,
                    student_id=sub.student_id,
                    answer_text=sub.answer_text,
                    status=sub.status,
                    is_late=sub.is_late,
                    submitted_at=sub.submitted_at,
                    created_at=sub.created_at,
                    student=UserResponse.model_validate(sub.student) if sub.student else None,
                    attachments=[
                        SubmissionAttachmentResponse.model_validate(att)
                        for att in sub.attachments
                    ],
                    reviews=reviews_resp,
                    latest_score=reviews_resp[-1].score if reviews_resp else None,
                    latest_feedback=reviews_resp[-1].feedback_text if reviews_resp else None,
                )
            )
        return response

    @staticmethod
    async def review_submission(
        db: AsyncSession, submission_id: str, data: ReviewCreate, teacher: User
    ) -> SubmissionResponse:
        query = (
            select(Submission)
            .where(Submission.id == submission_id)
            .options(
                selectinload(Submission.assignment),
                selectinload(Submission.student),
                selectinload(Submission.reviews),
            )
        )
        result = await db.execute(query)
        sub = result.scalar_one_or_none()

        if not sub:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topshiriq topilmadi",
            )

        if sub.assignment.teacher_id != teacher.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Ushbu vazifani baholash huquqiga ega emassiz",
            )

        if data.score > sub.assignment.max_score:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Baho maksimal balldan ({sub.assignment.max_score}) oshmasligi kerak",
            )

        # Create review record
        review = Review(
            submission_id=sub.id,
            reviewer_id=teacher.id,
            score=data.score,
            feedback_text=data.feedback_text.strip() if data.feedback_text else None,
            decision=data.decision,
            reviewed_at=datetime.now(timezone.utc),
        )
        db.add(review)

        # Update submission status
        if data.decision == ReviewDecision.RESUBMIT:
            sub.status = SubmissionStatus.RESUBMIT_REQUESTED
            notif_type = NotificationType.RESUBMISSION_REQUESTED
            notif_msg = f"'{sub.assignment.title}' vazifasi bo'yicha qayta topshirish so'raldi: {data.feedback_text or ''}"
        else:
            sub.status = SubmissionStatus.GRADED
            notif_type = NotificationType.ASSIGNMENT_REVIEWED
            notif_msg = f"'{sub.assignment.title}' vazifangiz baholandi: {data.score}/{sub.assignment.max_score} ball."

        # Send notification to student
        student_notif = Notification(
            user_id=sub.student_id,
            title="Vazifa tekshirildi",
            body=notif_msg,
            type=notif_type,
            payload={"assignment_id": sub.assignment_id, "submission_id": sub.id},
        )
        db.add(student_notif)

        await db.commit()
        return await SubmissionService.get_submission_detail(db, sub.id, teacher)
