from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from .. import models, schemas
from ..auth import get_current_active_user

router = APIRouter(prefix="/api/categories", tags=["Categories"])


@router.get("", response_model=List[schemas.CategoryOut])
def get_categories(db: Session = Depends(get_db)):
    """Barcha mavjud kategoriyalar va ularning maqolalar sonini qaytaradi"""
    categories = db.query(models.Category).order_by(models.Category.name.asc()).all()
    result = []
    for cat in categories:
        post_count = db.query(func.count(models.Post.id)).filter(
            models.Post.category_id == cat.id,
            models.Post.published == True
        ).scalar()
        cat_out = schemas.CategoryOut(
            id=cat.id,
            name=cat.name,
            description=cat.description,
            created_at=cat.created_at,
            post_count=post_count or 0
        )
        result.append(cat_out)
    return result


@router.post("", response_model=schemas.CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(
    category_in: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Yangi kategoriya qo'shish (faqat tizimga kirgan foydalanuvchilar uchun)"""
    existing = db.query(models.Category).filter(
        func.lower(models.Category.name) == category_in.name.strip().lower()
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ushbu nomdagi kategoriya allaqachon mavjud"
        )

    category = models.Category(
        name=category_in.name.strip(),
        description=category_in.description
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return schemas.CategoryOut(
        id=category.id,
        name=category.name,
        description=category.description,
        created_at=category.created_at,
        post_count=0
    )


@router.get("/{category_id}", response_model=schemas.CategoryOut)
def get_category_by_id(category_id: int, db: Session = Depends(get_db)):
    """Kategoriya tafsilotlarini olish"""
    category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kategoriya topilmadi"
        )
    post_count = db.query(func.count(models.Post.id)).filter(
        models.Post.category_id == category.id,
        models.Post.published == True
    ).scalar()
    return schemas.CategoryOut(
        id=category.id,
        name=category.name,
        description=category.description,
        created_at=category.created_at,
        post_count=post_count or 0
    )
