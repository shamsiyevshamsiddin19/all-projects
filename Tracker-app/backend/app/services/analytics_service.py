from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy import distinct, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.assignment import Assignment
from app.models.enums import AssignmentStatus, MembershipStatus, SubmissionStatus, UserRole
from app.models.group import Group, GroupMembership
from app.models.review import Review
from app.models.submission import Submission
from app.models.user import User
from app.schemas.analytics import (
    ActivityPoint,
    GroupPerformanceItem,
    StudentDashboardStats,
    StudentRankingItem,
    TeacherDashboardStats,
)


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class AnalyticsService:
    @staticmethod
    async def get_teacher_stats(db: AsyncSession, teacher: User) -> TeacherDashboardStats:
        now = datetime.now(timezone.utc)

        # 1. Total Groups
        g_res = await db.execute(
            select(func.count(Group.id)).where(
                Group.teacher_id == teacher.id, Group.deleted_at.is_(None)
            )
        )
        total_groups = g_res.scalar() or 0

        # 2. Total distinct active students across teacher's groups
        s_res = await db.execute(
            select(func.count(distinct(GroupMembership.student_id)))
            .join(Group, Group.id == GroupMembership.group_id)
            .where(
                Group.teacher_id == teacher.id,
                Group.deleted_at.is_(None),
                GroupMembership.status == MembershipStatus.ACTIVE,
            )
        )
        total_students = s_res.scalar() or 0

        # 3. Assignments stats
        a_res = await db.execute(
            select(Assignment)
            .where(
                Assignment.teacher_id == teacher.id,
                Assignment.deleted_at.is_(None),
            )
            .options(
                selectinload(Assignment.submissions).selectinload(Submission.reviews),
                selectinload(Assignment.submissions).selectinload(Submission.student),
            )
        )
        assignments = a_res.scalars().all()

        active_assignments = len([
            a for a in assignments
            if a.status == AssignmentStatus.PUBLISHED and (ensure_utc(a.deadline) or now) > now
        ])
        completed_assignments = len([
            a for a in assignments
            if a.status == AssignmentStatus.PUBLISHED and (ensure_utc(a.deadline) or now) <= now
        ])

        all_submissions: List[Submission] = []
        for a in assignments:
            all_submissions.extend(a.submissions)

        pending_reviews = len([s for s in all_submissions if s.status in [SubmissionStatus.SUBMITTED, SubmissionStatus.LATE]])
        late_submissions = len([s for s in all_submissions if s.is_late])

        # Average score
        all_scores = [
            s.reviews[0].score
            for s in all_submissions
            if s.reviews and len(s.reviews) > 0
        ]
        avg_score = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0.0

        # Completion rate
        total_expected_submissions = (total_students * len(assignments)) if total_students and assignments else 0
        completion_rate = (
            round((len(all_submissions) / total_expected_submissions) * 100, 1)
            if total_expected_submissions > 0
            else (100.0 if all_submissions else 0.0)
        )

        # Weekly Activity (Last 7 days)
        day_labels = ["Dush", "Sesh", "Chor", "Pay", "Juma", "Shan", "Yak"]
        today_idx = now.weekday()
        weekly_activity: List[ActivityPoint] = []
        for i in range(6, -1, -1):
            target_date = (now - timedelta(days=i)).date()
            label = day_labels[(today_idx - i) % 7]
            count = len([
                s for s in all_submissions
                if s.submitted_at.date() == target_date
            ])
            weekly_activity.append(ActivityPoint(label=label, value=count))

        # Group Performances
        group_query = (
            select(Group)
            .where(Group.teacher_id == teacher.id, Group.deleted_at.is_(None))
            .options(
                selectinload(Group.memberships),
                selectinload(Group.assignments).selectinload(Assignment.submissions).selectinload(Submission.reviews),
            )
        )
        g_result = await db.execute(group_query)
        teacher_groups = g_result.scalars().all()

        group_performances: List[GroupPerformanceItem] = []
        for tg in teacher_groups:
            active_mems = [m for m in tg.memberships if m.status == MembershipStatus.ACTIVE]
            g_subs = []
            for ga in tg.assignments:
                if ga.deleted_at is None:
                    g_subs.extend(ga.submissions)

            g_scores = [
                s.reviews[0].score for s in g_subs if s.reviews and len(s.reviews) > 0
            ]
            g_avg = round(sum(g_scores) / len(g_scores), 1) if g_scores else 0.0
            g_expected = len(active_mems) * len(tg.assignments) if active_mems and tg.assignments else 0
            g_comp = round((len(g_subs) / g_expected) * 100, 1) if g_expected > 0 else 0.0

            group_performances.append(
                GroupPerformanceItem(
                    group_id=tg.id,
                    group_name=tg.name,
                    total_students=len(active_mems),
                    completion_rate=g_comp,
                    average_score=g_avg,
                )
            )

        # Top Students
        student_scores: Dict[str, Dict[str, Any]] = {}
        for sub in all_submissions:
            if sub.reviews:
                st_id = sub.student_id
                if st_id not in student_scores:
                    student_scores[st_id] = {
                        "student_id": st_id,
                        "student_name": sub.student.full_name if sub.student else "Student",
                        "avatar_url": sub.student.avatar_url if sub.student else None,
                        "completed_tasks": 0,
                        "scores": [],
                    }
                student_scores[st_id]["completed_tasks"] += 1
                student_scores[st_id]["scores"].append(sub.reviews[0].score)

        top_students: List[StudentRankingItem] = []
        for st_id, data in student_scores.items():
            st_avg = round(sum(data["scores"]) / len(data["scores"]), 1) if data["scores"] else 0.0
            top_students.append(
                StudentRankingItem(
                    student_id=st_id,
                    student_name=data["student_name"],
                    avatar_url=data["avatar_url"],
                    completed_tasks=data["completed_tasks"],
                    average_score=st_avg,
                )
            )
        top_students.sort(key=lambda x: (x.average_score, x.completed_tasks), reverse=True)
        top_students = top_students[:5]

        return TeacherDashboardStats(
            total_students=total_students,
            total_groups=total_groups,
            active_assignments=active_assignments,
            completed_assignments=completed_assignments,
            pending_reviews=pending_reviews,
            late_submissions=late_submissions,
            average_score=avg_score,
            completion_rate=completion_rate,
            weekly_activity=weekly_activity,
            group_performances=group_performances,
            top_students=top_students,
        )

    @staticmethod
    async def get_student_stats(db: AsyncSession, student: User) -> StudentDashboardStats:
        now = datetime.now(timezone.utc)

        # 1. Student's groups
        mem_query = select(GroupMembership.group_id).where(
            GroupMembership.student_id == student.id,
            GroupMembership.status == MembershipStatus.ACTIVE,
        )
        mem_res = await db.execute(mem_query)
        group_ids = [row[0] for row in mem_res.all()]

        # 2. Student's assignments
        a_query = select(Assignment).where(
            Assignment.deleted_at.is_(None),
            Assignment.status == AssignmentStatus.PUBLISHED,
            or_(
                Assignment.group_id.in_(group_ids) if group_ids else False,
                Assignment.individual_student_id == student.id,
            ),
        )
        a_res = await db.execute(a_query)
        assignments = a_res.scalars().all()

        # 3. Student's submissions
        sub_query = (
            select(Submission)
            .where(Submission.student_id == student.id)
            .options(selectinload(Submission.reviews))
        )
        sub_res = await db.execute(sub_query)
        submissions = sub_res.scalars().all()
        submitted_assignment_ids = {s.assignment_id for s in submissions}

        active_tasks = len([
            a for a in assignments
            if a.id not in submitted_assignment_ids and (ensure_utc(a.deadline) or now) > now
        ])
        overdue_tasks = len([
            a for a in assignments
            if a.id not in submitted_assignment_ids and (ensure_utc(a.deadline) or now) <= now
        ])
        completed_tasks = len(submissions)

        total_tasks = len(assignments)
        completion_rate = (
            round((completed_tasks / total_tasks) * 100, 1)
            if total_tasks > 0
            else 100.0
        )

        all_scores = [
            s.reviews[0].score for s in submissions if s.reviews and len(s.reviews) > 0
        ]
        avg_score = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0.0
        total_points = sum(all_scores)
        max_possible = sum(
            a.max_score for a in assignments if a.id in submitted_assignment_ids
        )

        day_labels = ["Dush", "Sesh", "Chor", "Pay", "Juma", "Shan", "Yak"]
        today_idx = now.weekday()
        weekly_progress: List[ActivityPoint] = []
        for i in range(6, -1, -1):
            target_date = (now - timedelta(days=i)).date()
            label = day_labels[(today_idx - i) % 7]
            count = len([
                s for s in submissions
                if s.submitted_at.date() == target_date
            ])
            weekly_progress.append(ActivityPoint(label=label, value=count))

        return StudentDashboardStats(
            active_tasks=active_tasks,
            completed_tasks=completed_tasks,
            overdue_tasks=overdue_tasks,
            average_score=avg_score,
            completion_rate=completion_rate,
            total_score_points=total_points,
            max_possible_points=max_possible,
            weekly_progress=weekly_progress,
        )

    @staticmethod
    async def get_report_data(
        db: AsyncSession, teacher: User, group_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetch unified data for PDF and Excel export generators."""
        query = (
            select(Group)
            .where(Group.teacher_id == teacher.id, Group.deleted_at.is_(None))
            .options(
                selectinload(Group.memberships).selectinload(GroupMembership.student),
                selectinload(Group.assignments)
                .selectinload(Assignment.submissions)
                .selectinload(Submission.reviews),
                selectinload(Group.assignments)
                .selectinload(Assignment.submissions)
                .selectinload(Submission.student),
            )
        )
        if group_id:
            query = query.where(Group.id == group_id)

        result = await db.execute(query)
        groups = result.scalars().all()

        if not groups:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hisobot uchun guruh ma'lumotlari topilmadi",
            )

        target_name = groups[0].name if group_id else "Barcha Guruhlar"
        total_students = sum(
            len([m for m in g.memberships if m.status == MembershipStatus.ACTIVE])
            for g in groups
        )

        all_items: List[Dict[str, Any]] = []
        all_scores: List[int] = []

        for g in groups:
            for a in g.assignments:
                if a.deleted_at is None:
                    for s in a.submissions:
                        score_val = (
                            s.reviews[0].score if s.reviews and len(s.reviews) > 0 else "-"
                        )
                        if isinstance(score_val, int):
                            all_scores.append(score_val)
                        all_items.append({
                            "title": f"{s.student.full_name if s.student else 'Talaba'} — {a.title}",
                            "group": g.name,
                            "status": s.status.value,
                            "deadline": a.deadline.strftime("%d.%m.%Y"),
                            "score": f"{score_val}/{a.max_score}" if score_val != "-" else "-",
                        })

        avg_score = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0.0
        comp_rate = 100.0 if all_items else 0.0

        stats = {
            "total_students": total_students,
            "completed_tasks": len(all_items),
            "avg_score": avg_score,
            "completion_rate": comp_rate,
        }

        return {
            "title": f"{target_name} O'zlashtirish Hisoboti",
            "teacher_name": teacher.full_name,
            "target_name": target_name,
            "report_type": "Guruh Hisoboti" if group_id else "Umumiy Hisobot",
            "stats": stats,
            "items": all_items,
        }
