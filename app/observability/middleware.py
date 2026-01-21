"""
FastAPI middleware for HTTP request metrics.
"""
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.observability.metrics import http_requests_total, http_request_latency_seconds


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track HTTP request metrics.
    
    Records:
    - Request count by path, method, and status
    - Request latency by path and method
    """
    
    async def dispatch(self, request: Request, call_next):
        """Process request and record metrics."""
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate latency
        latency = time.time() - start_time
        
        # Record metrics
        path = request.url.path
        method = request.method
        status = response.status_code
        
        http_requests_total.labels(
            path=path,
            method=method,
            status=status
        ).inc()
        
        http_request_latency_seconds.labels(
            path=path,
            method=method
        ).observe(latency)
        
        return response
