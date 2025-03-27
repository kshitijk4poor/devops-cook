import time
import json
from typing import Callable, List

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from starlette.concurrency import iterate_in_threadpool

from app.core.logging_config import (
    get_logger,
    get_request_id,
    bind_request_context,
    sanitize_log_data,
)

class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_logger(__name__)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = get_request_id()
        logger = bind_request_context(
            self.logger,
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            client_host=request.client.host if request.client else None,
        )

        # Log request
        try:
            body = await request.body()
            if body:
                try:
                    body_text = body.decode()
                    # Try to parse as JSON to sanitize nested fields
                    try:
                        body_json = json.loads(body_text)
                        body_data = {'body': json.dumps(sanitize_log_data(body_json))}
                    except json.JSONDecodeError:
                        # If not JSON, sanitize as plain text
                        body_data = sanitize_log_data({'body': body_text})
                    logger = logger.bind(**body_data)
                except UnicodeDecodeError:
                    logger = logger.bind(body='<binary data>')
        except Exception as e:
            logger = logger.bind(body_error=str(e))

        logger.info(event='request_started')
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Calculate request duration
            duration = time.time() - start_time
            
            # Log response
            logger = logger.bind(
                status_code=response.status_code,
                duration=duration
            )
            
            # Only log response body for error responses
            if response.status_code >= 400:
                try:
                    # Create a copy of the response to read the body
                    response_body = []
                    async for chunk in response.body_iterator:
                        response_body.append(chunk)
                    
                    # Combine chunks and decode
                    body = b''.join(response_body)
                    
                    # Create a new async iterator for the response body
                    async def body_iterator():
                        for chunk in response_body:
                            yield chunk
                    
                    response.body_iterator = body_iterator()
                    
                    # Log sanitized response body
                    try:
                        body_text = body.decode()
                        body_data = sanitize_log_data({'response_body': body_text})
                        logger = logger.bind(**body_data)
                    except UnicodeDecodeError:
                        logger = logger.bind(response_body='<binary data>')
                except Exception as e:
                    logger = logger.bind(response_body_error=str(e))
            
            logger.info(event='request_completed')
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.exception(
                event='request_failed',
                exc_info=e,
                duration=duration
            )
            raise

def setup_logging_middleware(app: FastAPI) -> None:
    """Set up the structured logging middleware."""
    app.add_middleware(StructuredLoggingMiddleware) 