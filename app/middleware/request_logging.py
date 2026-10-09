import logging
import time
import uuid

from fastapi import Request

logger = logging.getLogger("app.request")


async def log_requests_middleware(request: Request, call_next):
    """Tag each request with an ID, time it, log it, and add response headers."""
    request_id = uuid.uuid4().hex[:8]
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("[%s] %s %s -> unhandled exception", request_id, request.method, request.url.path)
        raise

    duration_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-ms"] = f"{duration_ms:.2f}"
    logger.info(
        "[%s] %s %s -> %s (%.2f ms)",
        request_id, request.method, request.url.path, response.status_code, duration_ms,
    )
    return response
