import logging
import sys
import time
import socket
from typing import Any, Dict

import structlog
from pythonjsonlogger import jsonlogger
import logstash

# Configure standard logging
def configure_standard_logging() -> None:
    json_handler = logging.StreamHandler(sys.stdout)
    json_handler.setFormatter(jsonlogger.JsonFormatter(
        fmt='%(timestamp)s %(level)s %(name)s %(message)s'
    ))
    
    # Create Logstash handler
    logstash_handler = logstash.TCPLogstashHandler(
        host='logstash',
        port=5000,  # This is the internal Docker port, no need to change
        version=1,
        message_type='fastapi',
        fqdn=False,
        tags=['fastapi', 'application']
    )
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        handlers=[json_handler, logstash_handler]
    )

# Configure structlog
def configure_structlog() -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)

def get_request_id() -> str:
    """Generate a unique request ID."""
    return str(int(time.time() * 1000000))

def bind_request_context(logger: structlog.BoundLogger, request_id: str, **kwargs: Any) -> structlog.BoundLogger:
    """Bind request context to logger."""
    return logger.bind(request_id=request_id, **kwargs)

def sanitize_log_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove sensitive information from log data."""
    sensitive_fields = {'password', 'token', 'secret', 'authorization', 'api_key'}
    sanitized = {}
    
    for key, value in data.items():
        if any(sensitive in key.lower() for sensitive in sensitive_fields):
            sanitized[key] = '***REDACTED***'
        elif isinstance(value, dict):
            sanitized[key] = sanitize_log_data(value)
        else:
            sanitized[key] = value
            
    return sanitized 