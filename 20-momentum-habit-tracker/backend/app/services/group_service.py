from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.assignment import Assignment
from app.models.enums import MembershipStatus, UserRole
from app.models.group import Group, GroupMembership
from app.models.user import User
from app.schemas.group import (
    GroupCreate,
    GroupDetailResponse,
    GroupMemberResponse,
    GroupResponse,
    GroupUpdate,
)
from app.schemas.user import UserResponse


class GroupService:
    @staticmethod
    async def create_group(
        db: AsyncSession, data: GroupCreate, teacher: User
    ) -> GroupResponse:
        group = Group(
            name=data.name.strip(),
            description=data.description.strip() if data.description else None,
            teacher_id=teacher.id,
        )
        db.add(group)
        await db.commit()
        await db.refresh(group)
        return GroupResponse(
            id=group.id,
            name=group.name,
            description=group.description,
            invite_code=group.invite_code,
            teacher_id=group.teacher_id,
            created_at=group.created_at,
            updated_at=group.updated_at,
            total_students=0,
            total_assignments=0,
        )

    @staticmethod
    async def get_user_groups(
        db: AsyncSession, user: User, skip: int = 0, limit: int = 50
    ) -> List[GroupResponse]:
        if user.role == UserRole.TEACHER:
            query = (
                select(Group)
                .where(Group.teacher_id == user.id, Group.deleted_at.is_(None))
                .options(selectinload(Group.memberships), selectinload(Group.assignments))
                .order_by(Group.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            result = await db.execute(query)
            groups = result.scalars().all()

            response = []
            for g in groups:
                active_members = len(
                    [m for m in g.memberships if m.status == MembershipStatus.ACTIVE]
                )
                active_assignments = len([a for a in g.assignments if a.deleted_at is None])
                response.append(
                    GroupResponse(
                        id=g.id,
                        name=g.name,
                        description=g.description,
                        invite_code=g.invite_code,
                        teacher_id=g.teacher_id,
                        created_at=g.created_at,
                        updated_at=g.updated_at,
                        total_students=active_members,
                        total_assignments=active_assignments,
                    )
                )
            return response
        else:
            # For student, find groups where student is active member
            query = (
                select(Group)
                .join(GroupMembership, GroupMembership.group_id == Group.id)
                .where(
                    GroupMembership.student_id == user.id,
                    GroupMembership.status == MembershipStatus.ACTIVE,
                    Group.deleted_at.is_(None),
                )
                .options(selectinload(Group.memberships), selectinload(Group.assignments))
                .order_by(Group.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            result = await db.execute(query)
            groups = result.scalars().all()

            response = []
            for g in groups:
                active_members = len(
                    [m for m in g.memberships if m.status == MembershipStatus.ACTIVE]
                )
                active_assignments = len([a for a in g.assignments if a.deleted_at is None])
                response.append(
                    GroupResponse(
                        id=g.id,
                        name=g.name,
                        description=g.description,
                        invite_code=g.invite_code,
                        teacher_id=g.teacher_id,
                        created_at=g.created_at,
                        updated_at=g.updated_at,
                        total_students=active_members,
                        total_assignments=active_assignments,
                    )
                )
            return response

    @staticmethod
    async def get_group_detail(
        db: AsyncSession, group_id: str, user: User
    ) -> GroupDetailResponse:
        query = (
            select(Group)
            .where(Group.id == group_id, Group.deleted_at.is_(None))
            .options(
                selectinload(Group.teacher),
                selectinload(Group.memberships).selectinload(GroupMembership.student),
                selectinload(Group.assignments),
            )
        )
        result = await db.execute(query)
        group = result.scalar_one_or_none()

        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guruh topilmadi",
            )

        # RBAC Check: Teacher must own group OR student must be a member
        if user.role == UserRole.TEACHER and group.teacher_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Siz bu guruh egasi emassiz",
            )
        elif user.role == UserRole.STUDENT:
            is_member = any(
                m.student_id == user.id and m.status == MembershipStatus.ACTIVE
                for m in group.memberships
            )
            if not is_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Siz bu guruh a'zosi emassiz",
                )

        members_response = [
            GroupMemberResponse(
                id=m.id,
                student=UserResponse.model_validate(m.student),
                status=m.status,
                joined_at=m.joined_at,
            )
            for m in group.memberships
            if m.status == MembershipStatus.ACTIVE
        ]

        active_assignments = len([a for a in group.assignments if a.deleted_at is None])

        return GroupDetailResponse(
            id=group.id,
            name=group.name,
            description=group.description,
            invite_code=group.invite_code,
            teacher_id=group.teacher_id,
            created_at=group.created_at,
            updated_at=group.updated_at,
            total_students=len(members_response),
            total_assignments=active_assignments,
            teacher=UserResponse.model_validate(group.teacher),
            members=members_response,
        )

    @staticmethod
    async def update_group(
        db: AsyncSession, group_id: str, data: GroupUpdate, teacher: User
    ) -> GroupResponse:
        result = await db.execute(
            select(Group).where(
                Group.id == group_id,
                Group.teacher_id == teacher.id,
                Group.deleted_at.is_(None),
            )
        )
        group = result.scalar_one_or_none()
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guruh topilmadi yoki sizga tegishli emas",
            )

        if data.name is not None:
            group.name = data.name.strip()
        if data.description is not None:
            group.description = data.description.strip()

        await db.commit()
        await db.refresh(group)
        return GroupResponse.model_validate(group)

    @staticmethod
    async def delete_group(db: AsyncSession, group_id: str, teacher: User) -> None:
        result = await db.execute(
            select(Group).where(
                Group.id == group_id,
                Group.teacher_id == teacher.id,
                Group.deleted_at.is_(None),
            )
        )
        group = result.scalar_one_or_none()
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guruh topilmadi yoki sizga tegishli emas",
            )

        group.deleted_at = datetime.now(timezone.utc)
        await db.commit()

    @staticmethod
    async def join_group_by_code(
        db: AsyncSession, invite_code: str, student: User
    ) -> GroupDetailResponse:
        result = await db.execute(
            select(Group).where(
                Group.invite_code == invite_code.strip().upper(),
                Group.deleted_at.is_(None),
            )
        )
        group = result.scalar_one_or_none()
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guruh kodi noto'g'ri (Invalid invite code)",
            )

        # Check if already a member
        mem_result = await db.execute(
            select(GroupMembership).where(
                GroupMembership.group_id == group.id,
                GroupMembership.student_id == student.id,
            )
        )
        membership = mem_result.scalar_one_or_none()
        if membership:
            if membership.status == MembershipStatus.ACTIVE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Siz allaqachon ushbu guruh a'zosisiz",
                )
            else:
                membership.status = MembershipStatus.ACTIVE
                membership.joined_at = datetime.now(timezone.utc)
        else:
            membership = GroupMembership(
                group_id=group.id,
                student_id=student.id,
                status=MembershipStatus.ACTIVE,
            )
            db.add(membership)

        await db.commit()
        return await GroupService.get_group_detail(db, group.id, student)

    @staticmethod
    async def add_student_to_group(
        db: AsyncSession, group_id: str, student_id: str, teacher: User
    ) -> None:
        # Check group ownership
        group_res = await db.execute(
            select(Group).where(
                Group.id == group_id,
                Group.teacher_id == teacher.id,
                Group.deleted_at.is_(None),
            )
        )
        group = group_res.scalar_one_or_none()
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guruh topilmadi yoki sizga tegishli emas",
            )

        # Check student existence
        student_res = await db.execute(
            select(User).where(
                User.id == student_id,
                User.role == UserRole.STUDENT,
                User.deleted_at.is_(None),
            )
        )
        student = student_res.scalar_one_or_none()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Talaba topilmadi",
            )

        mem_res = await db.execute(
            select(GroupMembership).where(
                GroupMembership.group_id == group.id,
                GroupMembership.student_id == student.id,
            )
        )
        membership = mem_res.scalar_one_or_none()
        if membership:
            membership.status = MembershipStatus.ACTIVE
        else:
            membership = GroupMembership(
                group_id=group.id,
                student_id=student.id,
                status=MembershipStatus.ACTIVE,
            )
            db.add(membership)

        await db.commit()

    @staticmethod
    async def remove_student_from_group(
        db: AsyncSession, group_id: str, student_id: str, teacher: User
    ) -> None:
        group_res = await db.execute(
            select(Group).where(
                Group.id == group_id,
                Group.teacher_id == teacher.id,
                Group.deleted_at.is_(None),
            )
        )
        group = group_res.scalar_one_or_none()
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guruh topilmadi yoki sizga tegishli emas",
            )

        mem_res = await db.execute(
            select(GroupMembership).where(
                GroupMembership.group_id == group.id,
                GroupMembership.student_id == student_id,
            )
        )
        membership = mem_res.scalar_one_or_none()
        if membership:
            membership.status = MembershipStatus.REMOVED
            await db.commit()
