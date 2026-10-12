from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from .. import models, schemas
from ..auth import get_current_active_user

router = APIRouter(tags=["Comments"])


@router.get("/api/posts/{post_id}/comments", response_model=List[schemas.CommentOut])
def get_comments(post_id: int, db: Session = Depends(get_db)):
    """Maqolaga yozilgan barcha izohlarni ko'rish"""
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Maqola topilmadi"
        )

    comments = db.query(models.Comment).options(
        joinedload(models.Comment.author)
    ).filter(models.Comment.post_id == post_id).order_by(models.Comment.created_at.asc()).all()

    return comments


@router.post("/api/posts/{post_id}/comments", response_model=schemas.CommentOut, status_code=status.HTTP_201_CREATED)
def create_comment(
    post_id: int,
    comment_in: schemas.CommentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Maqolaga yangi izoh (comment) qoldirish (faqat tizimga kirgan foydalanuvchilar)"""
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Maqola topilmadi"
        )

    content_clean = comment_in.content.strip()
    if not content_clean:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Izoh matni bo'sh bo'lishi mumkin emas"
        )

    comment = models.Comment(
        content=content_clean,
        post_id=post_id,
        user_id=current_user.id
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    # Muallif ma'lumotlarini yuklash
    comment.author = current_user
    return comment


@router.delete("/api/comments/{comment_id}", status_code=status.HTTP_200_OK)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Izohni o'chirish (faqat izoh muallifi yoki maqola egasi uchun)"""
    comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Izoh topilmadi"
        )

    post = db.query(models.Post).filter(models.Post.id == comment.post_id).first()

    # Faqat izoh yozgan odam yoki post egasi o'chira oladi
    is_comment_author = (comment.user_id == current_user.id)
    is_post_owner = (post and post.owner_id == current_user.id)

    if not (is_comment_author or is_post_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Siz bu izohni o'chirish huquqiga ega emassiz"
        )

    db.delete(comment)
    db.commit()
    return {"message": "Izoh muvaffaqiyatli o'chirildi", "id": comment_id}
