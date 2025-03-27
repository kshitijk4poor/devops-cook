"""Middleware for logging requests and responses."""

import json
import logging
import time
import uuid
from typing import Callable, Dict, Any

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import settings


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to add request context, including a unique request ID."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Add request ID to response headers
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log request and response information."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timer for request duration
        start_time = time.time()
        
        # Extract request details
        path = request.url.path
        method = request.method
        client_host = request.client.host if request.client else None
        
        # Get request ID from state (set by RequestContextMiddleware)
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        
        # Log request start
        logger = logging.getLogger("api")
        logger.info(
            json.dumps({
                "event": "request_started",
                "request_id": request_id,
                "path": path,
                "method": method,
                "client_host": client_host,
                "timestamp": time.time(),
            })
        )
        
        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
            
            # Calculate request duration
            duration = time.time() - start_time
            
            # Log request completion
            logger.info(
                json.dumps({
                    "event": "request_completed",
                    "request_id": request_id,
                    "path": path,
                    "method": method,
                    "status_code": status_code,
                    "duration": duration,
                    "timestamp": time.time(),
                })
            )
            
            return response
        except Exception as e:
            # Calculate request duration
            duration = time.time() - start_time
            
            # Log exception
            logger.error(
                json.dumps({
                    "event": "request_failed",
                    "request_id": request_id,
                    "path": path,
                    "method": method,
                    "error": str(e),
                    "duration": duration,
                    "timestamp": time.time(),
                })
            )
            raise


def setup_logging() -> None:
    """Configure logging settings based on environment."""
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    
    # Create JSON formatter
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_record = {
                "timestamp": time.time(),
                "level": record.levelname,
                "message": record.getMessage(),
                "module": record.module,
                "service": settings.APP_NAME,
                "environment": settings.ENVIRONMENT,
            }
            
            # Add exception info if present
            if record.exc_info:
                log_record["exception"] = str(record.exc_info[1])
                log_record["traceback"] = self.formatException(record.exc_info)
            
            # Check if record.msg is already a JSON string
            if isinstance(record.msg, str) and record.msg.startswith("{") and record.msg.endswith("}"):
                try:
                    msg_data = json.loads(record.msg)
                    log_record.update(msg_data)
                except json.JSONDecodeError:
                    pass
            
            return json.dumps(log_record)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JsonFormatter())
    root_logger.addHandler(console_handler)
    
    # Configure API logger
    api_logger = logging.getLogger("api")
    api_logger.setLevel(log_level)
    
    # Log startup message
    api_logger.info(
        json.dumps({
            "event": "application_startup",
            "environment": settings.ENVIRONMENT,
            "debug_mode": settings.DEBUG,
            "version": settings.VERSION,
        })
    )


def add_logging_middleware(app: FastAPI) -> None:
    """Add logging middleware to FastAPI application."""
    # Configure logging
    setup_logging()
    
    # Add request context middleware (should be first)
    app.add_middleware(RequestContextMiddleware)
    
    # Add request logging middleware
    app.add_middleware(RequestLoggingMiddleware) 