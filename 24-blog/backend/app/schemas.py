from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict

# ============================
# User Schemas
# ============================

class UserBase(BaseModel):
    username: str = Field(..., min_length=2, max_length=100)
    email: EmailStr

class UserRegister(UserBase):
    password: str = Field(..., min_length=6, max_length=128)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None

# ============================
# Category Schemas
# ============================

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryOut(CategoryBase):
    id: int
    created_at: datetime
    post_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)

# ============================
# Comment Schemas
# ============================

class CommentBase(BaseModel):
    content: str = Field(..., min_length=1)

class CommentCreate(CommentBase):
    pass

class CommentOut(CommentBase):
    id: int
    created_at: datetime
    post_id: int
    user_id: int
    author: Optional[UserOut] = None

    model_config = ConfigDict(from_attributes=True)

# ============================
# Post Schemas
# ============================

class PostBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    content: str = Field(..., min_length=5)
    category_id: Optional[int] = None
    published: bool = True
    rating: Optional[int] = Field(default=5, ge=1, le=5)

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    content: Optional[str] = Field(None, min_length=5)
    category_id: Optional[int] = None
    published: Optional[bool] = None
    rating: Optional[int] = Field(None, ge=1, le=5)

class PostOut(BaseModel):
    id: int
    title: str
    content: str
    published: bool
    rating: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    owner_id: Optional[int] = None
    category_id: Optional[int] = None
    owner: Optional[UserOut] = None
    category: Optional[CategoryOut] = None
    comments_count: int = 0

    model_config = ConfigDict(from_attributes=True)

class PostDetail(PostOut):
    comments: List[CommentOut] = []

    model_config = ConfigDict(from_attributes=True)
