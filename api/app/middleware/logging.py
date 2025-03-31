"""Middleware for logging requests and responses."""

import json
import logging
import time
import uuid
import socket
import logging.handlers
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
            
            # Log errors for 5xx status codes
            if status_code >= 500:
                logger.error(
                    json.dumps({
                        "event": "server_error",
                        "request_id": request_id,
                        "path": path,
                        "method": method,
                        "status_code": status_code,
                        "duration": duration,
                        "timestamp": time.time(),
                        "error": f"Server error: HTTP {status_code}"
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


class TCPLogstashHandler(logging.handlers.SocketHandler):
    """Custom handler for sending logs to Logstash via TCP."""
    
    def __init__(self, host, port):
        super().__init__(host, port)
        self.formatter = logging.Formatter()
        # Connect immediately to detect connection issues
        try:
            self.sock = self.makeSocket()
            print(f"Successfully created socket connection to {host}:{port}")
        except Exception as e:
            print(f"Error creating socket connection to {host}:{port}: {e}")
            self.sock = None
    
    def emit(self, record):
        try:
            # Format the record
            msg = self.format(record)
            
            # Ensure it's a valid JSON string
            if not (msg.startswith('{') and msg.endswith('}')):
                # If not a valid JSON object, wrap it in a message field
                msg = json.dumps({"message": msg})
            
            # Add a newline for json_lines codec
            msg = msg + '\n'
            
            # Send as bytes
            if self.sock is None:
                # Try to recreate the socket if it's None
                self.sock = self.makeSocket()
            
            self.send(msg.encode('utf-8'))
        except Exception as e:
            print(f"Error sending log to Logstash: {str(e)}")
            # Try to reconnect
            self.sock = None
            self.handleError(record)


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
    
    # Create formatter
    json_formatter = JsonFormatter()
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(json_formatter)
    root_logger.addHandler(console_handler)
    
    # Add TCP logstash handler with improved connection handling
    logstash_connected = False
    try:
        print(f"Attempting to connect to Logstash on logstash:5000")
        logstash_handler = TCPLogstashHandler('logstash', 5000)
        logstash_handler.setFormatter(json_formatter)
        root_logger.addHandler(logstash_handler)
        print(f"Successfully added Logstash handler to logger")
        logstash_connected = True
    except Exception as e:
        # Log the error but continue if we can't connect to Logstash
        print(f"Failed to set up Logstash handler: {str(e)}")
    
    # Configure API logger
    api_logger = logging.getLogger("api")
    api_logger.setLevel(log_level)
    
    # Log startup message
    startup_msg = {
        "event": "application_startup",
        "environment": settings.ENVIRONMENT,
        "debug_mode": settings.DEBUG,
        "version": settings.VERSION,
        "logstash_connected": logstash_connected
    }
    api_logger.info(json.dumps(startup_msg))


def add_logging_middleware(app: FastAPI) -> None:
    """Add logging middleware to FastAPI application."""
    # Configure logging
    setup_logging()
    
    # Add request context middleware (should be first)
    app.add_middleware(RequestContextMiddleware)
    
    # Add request logging middleware
    app.add_middleware(RequestLoggingMiddleware) 