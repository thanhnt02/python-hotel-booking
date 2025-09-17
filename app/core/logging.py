"""
Logging configuration and utilities.
"""
import logging
import logging.config
import sys
from datetime import datetime
from typing import Any, Dict
import structlog
from pythonjsonlogger import jsonlogger
from app.config import settings


def configure_logging():
    """Configure structured logging with JSON format."""
    
    # Configure structlog
    structlog.configure(
        processors=[
            # Add timestamp
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            # Add request ID if available
            add_request_id,
            # JSON serializer
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": jsonlogger.JsonFormatter,
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
            },
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            }
        },
        "handlers": {
            "default": {
                "level": "INFO",
                "formatter": "json" if settings.ENVIRONMENT == "production" else "standard",
                "class": "logging.StreamHandler",
                "stream": sys.stdout
            },
            "error_file": {
                "level": "ERROR",
                "formatter": "json",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            }
        },
        "loggers": {
            "": {
                "handlers": ["default"],
                "level": "DEBUG" if settings.DEBUG else "INFO",
                "propagate": False
            },
            "app": {
                "handlers": ["default", "error_file"],
                "level": "DEBUG" if settings.DEBUG else "INFO",
                "propagate": False
            },
            "uvicorn": {
                "handlers": ["default"],
                "level": "INFO",
                "propagate": False
            },
            "sqlalchemy.engine": {
                "handlers": ["default"],
                "level": "INFO" if settings.DEBUG else "WARNING",
                "propagate": False
            }
        }
    }
    
    logging.config.dictConfig(logging_config)


def add_request_id(logger, method_name, event_dict):
    """Add request ID to log entries if available."""
    import contextvars
    
    try:
        request_id = request_id_context.get()
        if request_id:
            event_dict["request_id"] = request_id
    except LookupError:
        pass
    
    return event_dict


# Context variable for request ID
request_id_context = contextvars.ContextVar('request_id', default=None)


class LoggerMixin:
    """Mixin class to add structured logging to other classes."""
    
    @property
    def logger(self):
        """Get logger instance for the class."""
        return structlog.get_logger(self.__class__.__module__ + "." + self.__class__.__name__)


def get_logger(name: str = None) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (defaults to caller's module)
    
    Returns:
        Structured logger instance
    """
    if name is None:
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'unknown')
    
    return structlog.get_logger(name)


class RequestLogger:
    """Logger for HTTP requests and responses."""
    
    def __init__(self):
        self.logger = get_logger("app.requests")
    
    def log_request(self, method: str, url: str, headers: Dict[str, Any] = None, 
                   body: Any = None, user_id: int = None):
        """Log incoming HTTP request."""
        self.logger.info(
            "HTTP request received",
            method=method,
            url=str(url),
            headers=dict(headers) if headers else None,
            user_id=user_id,
            request_size=len(str(body)) if body else 0
        )
    
    def log_response(self, status_code: int, processing_time: float, 
                    response_size: int = 0, error: str = None):
        """Log HTTP response."""
        log_level = "error" if status_code >= 500 else "warning" if status_code >= 400 else "info"
        
        getattr(self.logger, log_level)(
            "HTTP response sent",
            status_code=status_code,
            processing_time_ms=round(processing_time * 1000, 2),
            response_size=response_size,
            error=error
        )


class DatabaseLogger:
    """Logger for database operations."""
    
    def __init__(self):
        self.logger = get_logger("app.database")
    
    def log_query(self, query: str, params: Dict[str, Any] = None, 
                 execution_time: float = None):
        """Log database query."""
        self.logger.debug(
            "Database query executed",
            query=query,
            params=params,
            execution_time_ms=round(execution_time * 1000, 2) if execution_time else None
        )
    
    def log_transaction(self, operation: str, table: str, record_id: Any = None,
                       user_id: int = None):
        """Log database transaction."""
        self.logger.info(
            "Database transaction",
            operation=operation,
            table=table,
            record_id=record_id,
            user_id=user_id
        )


class SecurityLogger:
    """Logger for security events."""
    
    def __init__(self):
        self.logger = get_logger("app.security")
    
    def log_authentication(self, user_id: int, email: str, success: bool, 
                          ip_address: str = None, user_agent: str = None):
        """Log authentication attempt."""
        self.logger.info(
            "Authentication attempt",
            user_id=user_id,
            email=email,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def log_authorization(self, user_id: int, resource: str, action: str, 
                         granted: bool, reason: str = None):
        """Log authorization check."""
        self.logger.info(
            "Authorization check",
            user_id=user_id,
            resource=resource,
            action=action,
            granted=granted,
            reason=reason
        )
    
    def log_security_event(self, event_type: str, severity: str, details: Dict[str, Any]):
        """Log security event."""
        log_level = severity.lower() if severity.lower() in ['debug', 'info', 'warning', 'error', 'critical'] else 'info'
        
        getattr(self.logger, log_level)(
            f"Security event: {event_type}",
            event_type=event_type,
            severity=severity,
            **details
        )


class BusinessLogger:
    """Logger for business operations."""
    
    def __init__(self):
        self.logger = get_logger("app.business")
    
    def log_booking_created(self, booking_id: int, user_id: int, hotel_id: int, 
                           room_id: int, amount: float):
        """Log booking creation."""
        self.logger.info(
            "Booking created",
            booking_id=booking_id,
            user_id=user_id,
            hotel_id=hotel_id,
            room_id=room_id,
            amount=amount
        )
    
    def log_payment_processed(self, payment_id: int, booking_id: int, amount: float,
                             status: str, gateway: str = None):
        """Log payment processing."""
        self.logger.info(
            "Payment processed",
            payment_id=payment_id,
            booking_id=booking_id,
            amount=amount,
            status=status,
            gateway=gateway
        )
    
    def log_booking_cancelled(self, booking_id: int, user_id: int, reason: str,
                             refund_amount: float = 0):
        """Log booking cancellation."""
        self.logger.info(
            "Booking cancelled",
            booking_id=booking_id,
            user_id=user_id,
            reason=reason,
            refund_amount=refund_amount
        )


# Global logger instances
request_logger = RequestLogger()
database_logger = DatabaseLogger()
security_logger = SecurityLogger()
business_logger = BusinessLogger()


# Initialize logging on module import
configure_logging()
