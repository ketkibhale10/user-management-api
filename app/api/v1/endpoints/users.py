import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models import Role, User
from app.schemas import AdminUserCreate, UserOut, UserPage, UserUpdate

logger = logging.getLogger("app.users")
router = APIRouter(prefix="/users", tags=["Users"])


def _get_or_404(db: Session, user_id: uuid.UUID) -> User:
    user = crud.user.get(db, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"User {user_id} not found")
    return user


# NOTE: /me must be declared BEFORE /{user_id}
@router.get("/me", response_model=UserOut)
def read_me(current_user: User = Depends(get_current_user)):
    """Return the profile of the logged-in user."""
    return current_user


@router.get("", response_model=UserPage)
def list_users(
    limit: int = Query(10, ge=1, le=100, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    search: Optional[str] = Query(None, description="Filter by email or name"),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """List users with limit/offset pagination (admin only)."""
    items, total = crud.user.list_users(db, limit, offset, search)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: AdminUserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Create a user with a chosen role (admin only)."""
    if crud.user.get_by_email(db, payload.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    user = crud.user.create(db, payload)
    logger.info("Admin %s created user %s with role %s", admin.email, user.email, user.role.value)
    return user


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admins can view anyone; regular users can only view themselves."""
    if current_user.role != Role.admin and current_user.id != user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not allowed to view other users")
    return _get_or_404(db, user_id)


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Partial update. Only admins may change `role` or `is_active`."""
    is_admin = current_user.role == Role.admin
    if not is_admin and current_user.id != user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not allowed to modify other users")

    # Privilege-escalation guard
    if not is_admin and ({"role", "is_active"} & payload.model_dump(exclude_none=True).keys()):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only admins can change role or active status")

    user = crud.user.update(db, _get_or_404(db, user_id), payload)
    logger.info("User %s updated by %s", user.email, current_user.email)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Delete a user (admin only, cannot delete yourself)."""
    if admin.id == user_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Admins cannot delete themselves")
    user = _get_or_404(db, user_id)
    crud.user.delete(db, user)
    logger.info("User %s deleted by admin %s", user.email, admin.email)
    return Response(status_code=status.HTTP_204_NO_CONTENT)