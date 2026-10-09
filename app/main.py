import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.docs import register_docs
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.db.init_db import init_db
from app.middleware.request_logging import log_requests_middleware

setup_logging()
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # create tables + seed admin
    logger.info("Application started")
    yield
    logger.info("Application shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "User management API with **JWT auth**, refresh tokens, **role-based access control**, "
        "UUID identifiers and limit/offset pagination."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,    # replaced by the custom pages in app/core/docs.py
    redoc_url=None,
)

app.middleware("http")(log_requests_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time-ms"],
)

register_exception_handlers(app)
register_docs(app)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Health"])
def health():
    return {"status": "ok", "app": settings.APP_NAME}