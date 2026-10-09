import logging

from app import crud
from app.core.config import settings
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import Role  # noqa: F401  (also imports models so tables are registered)
from app.schemas import AdminUserCreate

logger = logging.getLogger("app.db")


def init_db() -> None:
    """Create tables and seed the default admin account."""
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if not crud.user.get_by_email(db, settings.ADMIN_EMAIL):
            crud.user.create(
                db,
                AdminUserCreate(
                    email=settings.ADMIN_EMAIL,
                    full_name=settings.ADMIN_NAME,
                    password=settings.ADMIN_PASSWORD,
                    role=Role.admin,
                ),
            )
            logger.info("Seeded admin user: %s", settings.ADMIN_EMAIL)
