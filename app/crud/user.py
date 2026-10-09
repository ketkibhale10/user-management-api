import uuid
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import Role, User
from app.schemas import AdminUserCreate, UserCreate, UserUpdate


def get(db: Session, user_id: uuid.UUID) -> Optional[User]:
    return db.get(User, user_id)


def get_by_email(db: Session, email: str) -> Optional[User]:
    return db.scalar(select(User).where(User.email == email.lower()))


def list_users(db: Session, limit: int, offset: int, search: Optional[str] = None) -> tuple[list[User], int]:
    stmt = select(User)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(or_(User.email.ilike(pattern), User.full_name.ilike(pattern)))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    # UUIDs are random, so order by creation time (id is only a tie-breaker) for stable pages
    items = db.scalars(stmt.order_by(User.created_at, User.id).limit(limit).offset(offset)).all()
    return list(items), total


def create(db: Session, data: UserCreate | AdminUserCreate) -> User:
    role = data.role if isinstance(data, AdminUserCreate) else Role.user
    user = User(
        email=data.email.lower(),
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update(db: Session, user: User, data: UserUpdate) -> User:
    values = data.model_dump(exclude_none=True)
    if "password" in values:
        user.hashed_password = hash_password(values.pop("password"))
    for field, value in values.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def delete(db: Session, user: User) -> None:
    db.delete(user)
    db.commit()