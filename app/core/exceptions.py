import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

logger = logging.getLogger("app.errors")


def register_exception_handlers(app: FastAPI) -> None:
    """HTTPException (4xx) and validation errors (422) are handled by FastAPI itself."""

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        logger.warning("Integrity error on %s: %s", request.url.path, exc.orig)
        return JSONResponse(status.HTTP_409_CONFLICT, {"detail": "Conflict: duplicate or invalid data"})

    @app.exception_handler(SQLAlchemyError)
    async def db_error_handler(request: Request, exc: SQLAlchemyError):
        logger.exception("Database error on %s", request.url.path)
        return JSONResponse(status.HTTP_500_INTERNAL_SERVER_ERROR, {"detail": "Database error"})

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error on %s", request.url.path)
        return JSONResponse(status.HTTP_500_INTERNAL_SERVER_ERROR, {"detail": "Internal server error"})