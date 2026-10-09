import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import crud
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_user_id_from_payload,
    verify_password,
)
from app.db.session import get_db
from app.models import User
from app.schemas import RefreshRequest, TokenResponse, UserCreate, UserOut

logger = logging.getLogger("app.auth")
router = APIRouter(prefix="/auth", tags=["Authentication"])


def _build_tokens(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    """Public sign-up. The new account always gets the `user` role."""
    if crud.user.get_by_email(db, payload.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    user = crud.user.create(db, payload)
    logger.info("New user registered: %s (id=%s)", user.email, user.id)
    return user


@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Log in with email (in the `username` field) and password to get an access and a refresh token."""
    user = crud.user.get_by_email(db, form.username)
    if not user or not verify_password(form.password, user.hashed_password):
        logger.warning("Failed login attempt for %s", form.username)
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is deactivated")
    logger.info("User logged in: %s", user.email)
    return _build_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    """Exchange a valid refresh token for a new access + refresh token pair."""
    payload = decode_token(body.refresh_token, expected_type="refresh")
    user = crud.user.get(db, get_user_id_from_payload(payload))
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")
    logger.info("Tokens refreshed for %s", user.email)
    return _build_tokens(user)