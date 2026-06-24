"""
middleware/logging.py
─────────────────────
Starlette ASGI middleware that logs every inbound HTTP request and its outcome.

Log format:
    [2024-01-15 10:32:01 UTC]  POST /customers  201  15ms

The middleware logs BEFORE forwarding to the route handler (to capture the
request timestamp) and AFTER receiving the response (to capture status + duration).
"""

import logging
import time
from datetime import datetime, timezone

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings

# ── Configure module-level logger ─────────────────────────────────────────────
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(message)s",        # We build the full line ourselves
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("api.access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    ASGI middleware that emits a one-line access log entry per request,
    including the HTTP method, path, response status code, and elapsed time.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time: float = time.perf_counter()
        timestamp: str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        # Forward request to the actual route handler
        response: Response = await call_next(request)

        elapsed_ms: int = int((time.perf_counter() - start_time) * 1000)

        logger.info(
            "[%s UTC]  %-6s %-40s  %d  %dms",
            timestamp,
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )

        return response
