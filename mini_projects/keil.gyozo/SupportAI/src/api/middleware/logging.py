"""Logging middleware for request/response tracking."""

import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests and responses."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Process request and log details.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler

        Returns:
            HTTP response
        """
        # Generate request ID
        request_id = request.headers.get("X-Request-ID", f"req-{time.time()}")

        # Log request
        logger.info(
            f"Request started - {request.method} {request.url.path} "
            f"[{request_id}]"
        )

        # Time request
        start_time = time.time()

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Log response
            logger.info(
                f"Request completed - {request.method} {request.url.path} "
                f"[{request_id}] - Status: {response.status_code} - "
                f"Duration: {duration:.3f}s"
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Request failed - {request.method} {request.url.path} "
                f"[{request_id}] - Error: {str(e)} - Duration: {duration:.3f}s",
                exc_info=True
            )
            raise
