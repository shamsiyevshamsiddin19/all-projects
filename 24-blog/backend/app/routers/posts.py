from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_

from ..database import get_db
from .. import models, schemas
from ..auth import get_current_active_user, get_optional_user

router = APIRouter(prefix="/api/posts", tags=["Posts"])


def enrich_post_out(post: models.Post, db: Session) -> schemas.PostOut:
    count = db.query(func.count(models.Comment.id)).filter(models.Comment.post_id == post.id).scalar() or 0
    return schemas.PostOut(
        id=post.id,
        title=post.title,
        content=post.content,
        published=post.published,
        rating=post.rating,
        created_at=post.created_at,
        updated_at=post.updated_at,
        owner_id=post.owner_id,
        category_id=post.category_id,
        owner=post.owner,
        category=post.category,
        comments_count=count
    )


@router.get("", response_model=List[schemas.PostOut])
def get_posts(
    category_id: Optional[int] = Query(None, description="Category ID bo'yicha filter"),
    category_name: Optional[str] = Query(None, description="Category nomi bo'yicha filter"),
    search: Optional[str] = Query(None, description="Maqola sarlavhasi yoki matni bo'yicha qidiruv"),
    owner_id: Optional[int] = Query(None, description="Muallif ID si bo'yicha filter"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_optional_user)
):
    """
    Maqolalar ro'yxatini olish.
    - Qidiruv (Search)
    - Kategoriya bo'yicha filter (Category ID yoki nomi bo'yicha)
    - Muallif bo'yicha filter
    - Sahifalash (Pagination: skip, limit)
    """
    query = db.query(models.Post).options(
        joinedload(models.Post.owner),
        joinedload(models.Post.category)
    )

    # Agar o'zining maqolalarini ko'rayotgan bo'lsa, qoralama (draft) larni ham ko'rsatish
    if owner_id and current_user and current_user.id == owner_id:
        query = query.filter(models.Post.owner_id == owner_id)
    elif owner_id:
        query = query.filter(models.Post.owner_id == owner_id, models.Post.published == True)
    else:
        query = query.filter(models.Post.published == True)

    # Category filter
    if category_id:
        query = query.filter(models.Post.category_id == category_id)
    elif category_name:
        query = query.join(models.Category).filter(
            func.lower(models.Category.name) == category_name.strip().lower()
        )

    # Search filter
    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                models.Post.title.ilike(search_term),
                models.Post.content.ilike(search_term)
            )
        )

    # Eng so'nggi maqolalar birinchi chiqishi uchun
    posts = query.order_by(models.Post.created_at.desc()).offset(skip).limit(limit).all()

    return [enrich_post_out(p, db) for p in posts]


@router.post("", response_model=schemas.PostOut, status_code=status.HTTP_201_CREATED)
def create_post(
    post_in: schemas.PostCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Yangi maqola yaratish (faqat tizimga kirgan foydalanuvchilar)"""
    # Kategoriya tekshiruvi (agar ko'rsatilgan bo'lsa)
    if post_in.category_id:
        category = db.query(models.Category).filter(models.Category.id == post_in.category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ko'rsatilgan kategoriya mavjud emas"
            )

    post = models.Post(
        title=post_in.title.strip(),
        content=post_in.content.strip(),
        category_id=post_in.category_id,
        published=post_in.published,
        rating=post_in.rating or 5,
        owner_id=current_user.id
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return enrich_post_out(post, db)


@router.get("/{post_id}", response_model=schemas.PostDetail)
def get_post_detail(post_id: int, db: Session = Depends(get_db)):
    """Maqola tafsilotlarini va unga yozilgan izohlarni (comments) olish"""
    post = db.query(models.Post).options(
        joinedload(models.Post.owner),
        joinedload(models.Post.category),
        joinedload(models.Post.comments).joinedload(models.Comment.author)
    ).filter(models.Post.id == post_id).first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Maqola topilmadi"
        )

    comments_out = [
        schemas.CommentOut(
            id=c.id,
            content=c.content,
            created_at=c.created_at,
            post_id=c.post_id,
            user_id=c.user_id,
            author=c.author
        )
        for c in post.comments
    ]

    return schemas.PostDetail(
        id=post.id,
        title=post.title,
        content=post.content,
        published=post.published,
        rating=post.rating,
        created_at=post.created_at,
        updated_at=post.updated_at,
        owner_id=post.owner_id,
        category_id=post.category_id,
        owner=post.owner,
        category=post.category,
        comments_count=len(comments_out),
        comments=comments_out
    )


@router.put("/{post_id}", response_model=schemas.PostOut)
def update_post(
    post_id: int,
    post_update: schemas.PostUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Maqolani tahrirlash (faqat maqola muallifi uchun)"""
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tahrirlanadigan maqola topilmadi"
        )

    if post.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Siz faqat o'zingiz yozgan maqolani tahrirlashingiz mumkin"
        )

    if post_update.category_id is not None:
        category = db.query(models.Category).filter(models.Category.id == post_update.category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ko'rsatilgan kategoriya mavjud emas"
            )
        post.category_id = post_update.category_id

    if post_update.title is not None:
        post.title = post_update.title.strip()
    if post_update.content is not None:
        post.content = post_update.content.strip()
    if post_update.published is not None:
        post.published = post_update.published
    if post_update.rating is not None:
        post.rating = post_update.rating

    post.updated_at = func.now()
    db.commit()
    db.refresh(post)
    return enrich_post_out(post, db)


@router.delete("/{post_id}", status_code=status.HTTP_200_OK)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Maqolani o'chirish (faqat maqola muallifi uchun)"""
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="O'chiriladigan maqola topilmadi"
        )

    if post.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Siz faqat o'zingiz yozgan maqolani o'chirishingiz mumkin"
        )

    db.delete(post)
    db.commit()
    return {"message": "Maqola muvaffaqiyatli o'chirildi", "id": post_id}
