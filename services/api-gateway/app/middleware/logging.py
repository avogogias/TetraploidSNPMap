"""
Request / response logging middleware.

Logs method, path, status code and elapsed time for every request.
"""

import logging
import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("tetraploid_snpmap.api")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs basic information about each HTTP request."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log the request method, path, response status and elapsed time."""
        start_time = time.perf_counter()

        # Log incoming request
        logger.info(
            "Incoming request: %s %s",
            request.method,
            request.url.path,
        )

        try:
            response: Response = await call_next(request)
        except Exception:
            logger.exception(
                "Unhandled exception during %s %s",
                request.method,
                request.url.path,
            )
            raise

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        logger.info(
            "Completed %s %s -> %d (%.1f ms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )

        # Attach timing header for observability
        response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.1f}"
        return response
