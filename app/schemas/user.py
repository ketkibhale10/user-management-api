import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import Role


class UserCreate(BaseModel):
    """Public registration payload (no role: always 'user')."""
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=64)


class AdminUserCreate(UserCreate):
    """Admin-only creation payload (can set role)."""
    role: Role = Role.user


class UserUpdate(BaseModel):
    """Partial update: every field optional."""
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    password: Optional[str] = Field(default=None, min_length=8, max_length=64)
    role: Optional[Role] = None         # admin only
    is_active: Optional[bool] = None    # admin only


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: Role
    is_active: bool
    created_at: datetime


class UserPage(BaseModel):
    items: list[UserOut]
    total: int
    limit: int
    offset: int