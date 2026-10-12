from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from .. import models, schemas
from ..auth import get_current_active_user, get_optional_user
from .posts import enrich_post_out

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/me/posts", response_model=List[schemas.PostOut])
def get_my_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Hozirgi tizimga kirgan foydalanuvchining barcha maqolalari (nashr qilingan va qoralama)"""
    posts = db.query(models.Post).options(
        joinedload(models.Post.owner),
        joinedload(models.Post.category)
    ).filter(
        models.Post.owner_id == current_user.id
    ).order_by(models.Post.created_at.desc()).offset(skip).limit(limit).all()

    return [enrich_post_out(p, db) for p in posts]


@router.get("/{user_id}/posts", response_model=List[schemas.PostOut])
def get_user_posts(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_optional_user)
):
    """Muayyan foydalanuvchining maqolalarini ko'rish"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Foydalanuvchi topilmadi"
        )

    query = db.query(models.Post).options(
        joinedload(models.Post.owner),
        joinedload(models.Post.category)
    ).filter(models.Post.owner_id == user_id)

    # Agar o'zining profili bo'lmasa, faqat published postlar ko'rinadi
    if not (current_user and current_user.id == user_id):
        query = query.filter(models.Post.published == True)

    posts = query.order_by(models.Post.created_at.desc()).offset(skip).limit(limit).all()
    return [enrich_post_out(p, db) for p in posts]


@router.get("/{user_id}", response_model=schemas.UserOut)
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    """Foydalanuvchi ommaviy profili"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Foydalanuvchi topilmadi"
        )
    return user
