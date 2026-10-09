from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.core.security import decode_token, get_user_id_from_payload
from app.db.session import get_db
from app.models import Role, User

# tokenUrl makes Swagger's "Authorize" button call the login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_token(token, expected_type="access")
    user = crud.user.get(db, get_user_id_from_payload(payload))
    if user is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "User no longer exists", headers={"WWW-Authenticate": "Bearer"}
        )
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is deactivated")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != Role.admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin privileges required")
    return current_user