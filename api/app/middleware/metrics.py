from prometheus_client import Counter, Histogram, Gauge
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from time import time
import logging

# Initialize metrics collectors
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests count',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint']
)

ACTIVE_REQUESTS = Gauge(
    'http_requests_active',
    'Number of currently active HTTP requests',
    ['method', 'endpoint']
)

ERROR_COUNT = Counter(
    'http_request_errors_total',
    'Total HTTP request errors',
    ['method', 'endpoint', 'error_type']
)

logger = logging.getLogger(__name__)

class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        method = request.method
        path = request.url.path
        
        # Track active requests
        ACTIVE_REQUESTS.labels(method=method, endpoint=path).inc()
        
        # Start timing the request
        start_time = time()
        
        try:
            response = await call_next(request)
            
            # Record request count and latency
            REQUEST_COUNT.labels(
                method=method,
                endpoint=path,
                status=response.status_code
            ).inc()
            
            REQUEST_LATENCY.labels(
                method=method,
                endpoint=path
            ).observe(time() - start_time)
            
            return response
            
        except Exception as e:
            # Record error metrics
            ERROR_COUNT.labels(
                method=method,
                endpoint=path,
                error_type=type(e).__name__
            ).inc()
            logger.exception("Request failed")
            raise
            
        finally:
            # Decrease active requests count
            ACTIVE_REQUESTS.labels(method=method, endpoint=path).dec() 