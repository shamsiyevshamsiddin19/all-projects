from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas
from ..auth import hash_password, verify_password, create_access_token, get_current_active_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=schemas.Token, status_code=status.HTTP_201_CREATED)
def register(user_in: schemas.UserRegister, db: Session = Depends(get_db)):
    """Yangi foydalanuvchini ro'yxatdan o'tkazish"""
    # Email borligini tekshirish
    existing_user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ushbu email bilan foydalanuvchi allaqachon mavjud"
        )

    # Yangi user yaratish
    hashed_pwd = hash_password(user_in.password)
    user = models.User(
        username=user_in.username,
        email=user_in.email,
        password=hashed_pwd,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Token yaratish
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/login", response_model=schemas.Token)
async def login(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Tizimga kirish (Login).
    JSON body ({email, password}) yoki Form data (username/email, password) ni qabul qiladi.
    """
    content_type = request.headers.get("content-type", "")
    email = None
    password = None

    if "application/json" in content_type:
        data = await request.json()
        email = data.get("email") or data.get("username")
        password = data.get("password")
    else:
        # Form data fallback (Swagger UI uchun)
        form = await request.form()
        email = form.get("username") or form.get("email")
        password = form.get("password")

    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email va parol kiritilishi shart"
        )

    user = db.query(models.User).filter(
        (models.User.email == email) | (models.User.username == email)
    ).first()

    if not user or not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email yoki parol noto'g'ri",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ushbu foydalanuvchi akkaunti faolsizlantirilgan"
        )

    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.get("/me", response_model=schemas.UserOut)
def get_current_user_profile(
    current_user: models.User = Depends(get_current_active_user)
):
    """Hozirgi tizimga kirgan foydalanuvchi ma'lumotlari"""
    return current_user
