"""
FastAPI middleware for request/response processing.
"""
import time
import uuid
from typing import Callable
from contextlib import contextmanager

from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import JSONResponse
import structlog

from app.core.logging import get_logger, request_logger
from app.core.monitoring import metrics
from app.core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging all HTTP requests and responses."""
    
    async def dispatch(
        self, 
        request: Request, 
        call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Process request and log details.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware or endpoint
        
        Returns:
            HTTP response
        """
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timer
        start_time = time.time()
        
        # Get client info
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Log request start
        request_logger.log_request_start(
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            client_ip=client_ip,
            user_agent=user_agent,
            headers=dict(request.headers)
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log successful response
            request_logger.log_request_end(
                request_id=request_id,
                status_code=response.status_code,
                duration=duration,
                response_size=len(response.body) if hasattr(response, 'body') else 0
            )
            
            # Update metrics
            metrics.http_requests_total.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code
            ).inc()
            
            metrics.http_request_duration_seconds.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as exc:
            # Calculate duration
            duration = time.time() - start_time
            
            # Log error
            request_logger.log_request_error(
                request_id=request_id,
                error=str(exc),
                duration=duration
            )
            
            # Update error metrics
            metrics.http_requests_total.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=500
            ).inc()
            
            # Re-raise exception
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers."""
    
    async def dispatch(
        self, 
        request: Request, 
        call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Add security headers to response.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware or endpoint
        
        Returns:
            HTTP response with security headers
        """
        response = await call_next(request)
        
        # Add security headers
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware."""
    
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_counts = {}
    
    async def dispatch(
        self, 
        request: Request, 
        call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Check rate limits and process request.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware or endpoint
        
        Returns:
            HTTP response or rate limit error
        """
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Clean old entries
        self._clean_old_entries(current_time)
        
        # Check rate limit
        if self._is_rate_limited(client_ip, current_time):
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"Rate limit exceeded. Max {self.max_requests} requests per {self.window_seconds} seconds."
                }
            )
        
        # Record request
        self._record_request(client_ip, current_time)
        
        return await call_next(request)
    
    def _clean_old_entries(self, current_time: float):
        """Remove old request entries."""
        cutoff_time = current_time - self.window_seconds
        
        for ip in list(self.request_counts.keys()):
            self.request_counts[ip] = [
                timestamp for timestamp in self.request_counts[ip]
                if timestamp > cutoff_time
            ]
            
            # Remove empty entries
            if not self.request_counts[ip]:
                del self.request_counts[ip]
    
    def _is_rate_limited(self, client_ip: str, current_time: float) -> bool:
        """Check if client IP is rate limited."""
        if client_ip not in self.request_counts:
            return False
        
        return len(self.request_counts[client_ip]) >= self.max_requests
    
    def _record_request(self, client_ip: str, current_time: float):
        """Record a request for rate limiting."""
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
        
        self.request_counts[client_ip].append(current_time)


class DatabaseMiddleware(BaseHTTPMiddleware):
    """Middleware for database connection management."""
    
    async def dispatch(
        self, 
        request: Request, 
        call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Manage database connections for request.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware or endpoint
        
        Returns:
            HTTP response
        """
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            # Log database errors
            logger.error(
                "Database error during request processing",
                error=str(exc),
                request_id=getattr(request.state, 'request_id', 'unknown')
            )
            raise


@contextmanager
def request_context(request: Request):
    """
    Context manager for request-specific logging context.
    
    Args:
        request: HTTP request
    
    Yields:
        Request context
    """
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    # Set up structured logging context
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        client_ip=request.client.host if request.client else "unknown"
    )
    
    try:
        yield
    finally:
        # Clear context
        structlog.contextvars.clear_contextvars()


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for centralized error handling."""
    
    async def dispatch(
        self, 
        request: Request, 
        call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Handle errors and return appropriate responses.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware or endpoint
        
        Returns:
            HTTP response or error response
        """
        try:
            return await call_next(request)
        except Exception as exc:
            request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
            
            logger.error(
                "Unhandled exception in request processing",
                error=str(exc),
                request_id=request_id,
                path=request.url.path,
                method=request.method
            )
            
            # Return generic error response
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "request_id": request_id
                }
            )
