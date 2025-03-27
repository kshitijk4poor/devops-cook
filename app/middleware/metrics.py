from prometheus_client import Counter, Histogram, Gauge
from fastapi import Request
from typing import Callable, Dict, Any
import time
import traceback

# Request metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests count",
    ["method", "endpoint", "status_code"]
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.1, 0.5, 1.0, 2.0, 4.0, float("inf")]
)

# Database metrics (simulated)
DB_OPERATION_DURATION = Histogram(
    "db_operation_duration_seconds",
    "Database operation duration in seconds",
    ["operation_type"],
    buckets=[0.01, 0.1, 0.5, 1.0, 2.0, 4.0, float("inf")]
)

# External API metrics
EXTERNAL_API_DURATION = Histogram(
    "external_api_duration_seconds",
    "External API call duration in seconds",
    ["service"],
    buckets=[0.1, 0.5, 1.0, 2.0, 4.0, float("inf")]
)

EXTERNAL_API_FAILURES = Counter(
    "external_api_failures_total",
    "External API call failures",
    ["service", "error_type"]
)

# Business metrics
SLOW_OPERATIONS = Counter(
    "slow_operations_total",
    "Operations taking longer than 4 seconds",
    ["endpoint"]
)

ERROR_COUNT = Counter(
    "error_count_total",
    "Total error count by type",
    ["endpoint", "error_type"]
)

# Active requests gauge
ACTIVE_REQUESTS = Gauge(
    "active_requests",
    "Number of currently active requests",
    ["endpoint"]
)

class MetricsMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope: Dict[str, Any], receive: Callable, send: Callable):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        endpoint = scope["path"]
        method = scope.get("method", "UNKNOWN")
        start_time = time.time()
        
        # Track active requests
        ACTIVE_REQUESTS.labels(endpoint=endpoint).inc()
        
        # Wrap send to capture response status
        response_status = None
        
        async def wrapped_send(message: Dict[str, Any]):
            nonlocal response_status
            if message["type"] == "http.response.start":
                response_status = message["status"]
            await send(message)
            
        try:
            await self.app(scope, receive, wrapped_send)
            
        except Exception as e:
            # Record error metrics
            error_type = type(e).__name__
            ERROR_COUNT.labels(
                endpoint=endpoint,
                error_type=error_type
            ).inc()
            
            # Set error status for 500 if not already set
            if response_status is None:
                response_status = 500
            
            raise
            
        finally:
            try:
                # Record request metrics if we got a response
                if response_status is not None:
                    REQUEST_COUNT.labels(
                        method=method,
                        endpoint=endpoint,
                        status_code=str(response_status)
                    ).inc()
                    
                    # Record duration
                    duration = time.time() - start_time
                    REQUEST_DURATION.labels(
                        method=method,
                        endpoint=endpoint
                    ).observe(duration)
                    
                    # Track slow operations
                    if duration > 4.0:
                        SLOW_OPERATIONS.labels(endpoint=endpoint).inc()
            except Exception:
                # Don't let metrics recording failures affect the response
                traceback.print_exc()
            finally:
                # Always decrease active requests count
                ACTIVE_REQUESTS.labels(endpoint=endpoint).dec()

# Utility functions for other parts of the application
def record_db_operation_duration(operation_type: str, duration: float):
    """Record the duration of a database operation"""
    DB_OPERATION_DURATION.labels(operation_type=operation_type).observe(duration)

def record_external_api_metrics(service: str, duration: float, error: Exception = None):
    """Record metrics for external API calls"""
    EXTERNAL_API_DURATION.labels(service=service).observe(duration)
    if error:
        EXTERNAL_API_FAILURES.labels(
            service=service,
            error_type=type(error).__name__
        ).inc() 