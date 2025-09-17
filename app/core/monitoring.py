"""
OpenTelemetry monitoring and tracing configuration.
"""
import os
from typing import Dict, Any
from opentelemetry import trace, metrics
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time
from app.config import settings


def setup_tracing():
    """Setup distributed tracing with Jaeger."""
    
    # Create resource
    resource = Resource.create({
        "service.name": settings.APP_NAME,
        "service.version": settings.VERSION,
        "service.environment": settings.ENVIRONMENT,
    })
    
    # Setup tracer provider
    trace.set_tracer_provider(TracerProvider(resource=resource))
    tracer = trace.get_tracer(__name__)
    
    # Setup Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name=settings.JAEGER_AGENT_HOST,
        agent_port=settings.JAEGER_AGENT_PORT,
    )
    
    # Add span processor
    span_processor = BatchSpanProcessor(jaeger_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)
    
    return tracer


def setup_metrics():
    """Setup metrics collection with Prometheus."""
    
    # Create resource
    resource = Resource.create({
        "service.name": settings.APP_NAME,
        "service.version": settings.VERSION,
        "service.environment": settings.ENVIRONMENT,
    })
    
    # Setup metrics
    prometheus_reader = PrometheusMetricReader()
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[prometheus_reader]))
    
    # Start Prometheus metrics server
    start_http_server(settings.PROMETHEUS_METRICS_PORT)
    
    return metrics.get_meter(__name__)


def instrument_app(app):
    """Instrument FastAPI application with OpenTelemetry."""
    
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
    
    # Instrument SQLAlchemy
    SQLAlchemyInstrumentor().instrument()
    
    # Instrument Redis
    RedisInstrumentor().instrument()


# Global tracer and meter
tracer = setup_tracing()
meter = setup_metrics()


class Metrics:
    """Application metrics."""
    
    def __init__(self):
        # HTTP metrics
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code']
        )
        
        self.http_request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint']
        )
        
        # Database metrics
        self.db_queries_total = Counter(
            'db_queries_total',
            'Total database queries',
            ['operation', 'table']
        )
        
        self.db_query_duration = Histogram(
            'db_query_duration_seconds',
            'Database query duration',
            ['operation', 'table']
        )
        
        self.db_connections_active = Gauge(
            'db_connections_active',
            'Active database connections'
        )
        
        # Business metrics
        self.bookings_total = Counter(
            'bookings_total',
            'Total bookings created',
            ['status']
        )
        
        self.payments_total = Counter(
            'payments_total',
            'Total payments processed',
            ['status', 'method']
        )
        
        self.revenue_total = Counter(
            'revenue_total',
            'Total revenue in USD'
        )
        
        # Cache metrics
        self.cache_operations_total = Counter(
            'cache_operations_total',
            'Total cache operations',
            ['operation', 'result']
        )
        
        self.cache_hit_ratio = Gauge(
            'cache_hit_ratio',
            'Cache hit ratio'
        )
        
        # Authentication metrics
        self.auth_attempts_total = Counter(
            'auth_attempts_total',
            'Total authentication attempts',
            ['result']
        )
        
        # Error metrics
        self.errors_total = Counter(
            'errors_total',
            'Total errors',
            ['type', 'severity']
        )
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics."""
        self.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code
        ).inc()
        
        self.http_request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_db_query(self, operation: str, table: str, duration: float):
        """Record database query metrics."""
        self.db_queries_total.labels(
            operation=operation,
            table=table
        ).inc()
        
        self.db_query_duration.labels(
            operation=operation,
            table=table
        ).observe(duration)
    
    def record_booking(self, status: str):
        """Record booking metrics."""
        self.bookings_total.labels(status=status).inc()
    
    def record_payment(self, status: str, method: str, amount: float = 0):
        """Record payment metrics."""
        self.payments_total.labels(status=status, method=method).inc()
        if status == 'completed' and amount > 0:
            self.revenue_total.inc(amount)
    
    def record_cache_operation(self, operation: str, hit: bool):
        """Record cache operation metrics."""
        result = 'hit' if hit else 'miss'
        self.cache_operations_total.labels(
            operation=operation,
            result=result
        ).inc()
    
    def record_auth_attempt(self, success: bool):
        """Record authentication attempt."""
        result = 'success' if success else 'failure'
        self.auth_attempts_total.labels(result=result).inc()
    
    def record_error(self, error_type: str, severity: str = 'error'):
        """Record error metrics."""
        self.errors_total.labels(type=error_type, severity=severity).inc()


# Global metrics instance
app_metrics = Metrics()


class TracingMixin:
    """Mixin class to add tracing to other classes."""
    
    def create_span(self, name: str, attributes: Dict[str, Any] = None):
        """Create a new span."""
        span = tracer.start_span(name)
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        return span


def trace_function(operation_name: str = None):
    """Decorator to trace function execution."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            span_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with tracer.start_as_current_span(span_name) as span:
                # Add function attributes
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                # Add arguments (be careful with sensitive data)
                if args:
                    span.set_attribute("function.args_count", len(args))
                if kwargs:
                    span.set_attribute("function.kwargs_count", len(kwargs))
                
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("function.result", "success")
                    return result
                except Exception as e:
                    span.set_attribute("function.result", "error")
                    span.set_attribute("function.error", str(e))
                    span.record_exception(e)
                    raise
        
        return wrapper
    return decorator


class PerformanceMonitor:
    """Monitor application performance."""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_times = []
    
    def start_request(self):
        """Start timing a request."""
        return time.time()
    
    def end_request(self, start_time: float, method: str, endpoint: str, status_code: int):
        """End timing a request and record metrics."""
        duration = time.time() - start_time
        self.request_times.append(duration)
        
        # Record metrics
        app_metrics.record_request(method, endpoint, status_code, duration)
        
        # Keep only recent requests for memory efficiency
        if len(self.request_times) > 1000:
            self.request_times = self.request_times[-500:]
    
    def get_average_response_time(self) -> float:
        """Get average response time."""
        if not self.request_times:
            return 0.0
        return sum(self.request_times) / len(self.request_times)
    
    def get_uptime(self) -> float:
        """Get application uptime in seconds."""
        return time.time() - self.start_time


# Global performance monitor
perf_monitor = PerformanceMonitor()


def setup_monitoring(app):
    """Setup complete monitoring for the application."""
    
    # Setup tracing and metrics
    instrument_app(app)
    
    # Add middleware for request monitoring
    @app.middleware("http")
    async def monitoring_middleware(request, call_next):
        start_time = perf_monitor.start_request()
        
        response = await call_next(request)
        
        # Record metrics
        perf_monitor.end_request(
            start_time,
            request.method,
            request.url.path,
            response.status_code
        )
        
        return response
    
    return app
