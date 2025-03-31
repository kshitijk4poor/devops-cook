"""Health check endpoints for the API."""

from fastapi import APIRouter, status
from pydantic import BaseModel
from datetime import datetime, UTC
import platform
import os
from opentelemetry import trace
import logging
import uuid
import time
import json
import requests

# Create router
router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    
    status: str
    version: str
    timestamp: datetime
    hostname: str
    environment: str


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Endpoint to check if the API is running correctly.",
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint that returns basic system information.
    
    Returns:
        HealthResponse: Health status and system information
    """
    start_time = time.time_ns()
    
    # Get tracer and create a span for health check
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("health_check_processing") as span:
        span.set_attribute("endpoint_type", "health")
        span.set_attribute("health.status", "healthy")
        span.add_event("health_check_processed", {"timestamp": datetime.now(UTC).isoformat()})
        
        # Create the response
        response = HealthResponse(
            status="healthy",
            version=os.getenv("VERSION", "1.0.0"),
            timestamp=datetime.now(UTC),
            hostname=platform.node(),
            environment=os.getenv("ENVIRONMENT", "development")
        )
        
        # Add attributes for important response fields
        span.set_attribute("health.version", response.version)
        span.set_attribute("health.environment", response.environment)
        
        # Manually post trace to Jaeger
        try:
            end_time = time.time_ns()
            duration = end_time - start_time
            
            trace_id = str(uuid.uuid4()).replace('-', '')
            span_id = str(uuid.uuid4()).replace('-', '')[:16]
            
            # Create a JSON payload for the trace
            trace_data = {
                "data": [{
                    "traceID": trace_id,
                    "spans": [{
                        "traceID": trace_id,
                        "spanID": span_id,
                        "operationName": "GET /api/health",
                        "references": [],
                        "startTime": start_time // 1000,  # Convert to microseconds
                        "duration": duration // 1000,  # Convert to microseconds
                        "tags": [
                            {"key": "http.method", "type": "string", "value": "GET"},
                            {"key": "http.url", "type": "string", "value": "/api/health"},
                            {"key": "span.kind", "type": "string", "value": "server"},
                            {"key": "service.name", "type": "string", "value": "API Observability Platform"},
                            {"key": "health.status", "type": "string", "value": "healthy"},
                            {"key": "health.version", "type": "string", "value": response.version},
                            {"key": "health.environment", "type": "string", "value": response.environment}
                        ],
                        "logs": [{
                            "timestamp": start_time // 1000,
                            "fields": [{"key": "event", "value": "health_check_processed"}]
                        }],
                        "processID": "p1"
                    }],
                    "processes": {
                        "p1": {"serviceName": "API Observability Platform", "tags": []}
                    }
                }]
            }
            
            # Log the trace data for debugging
            logging.info(f"Sending manual trace for health endpoint: {json.dumps(trace_data)}")
            
            # Send to Jaeger
            try:
                r = requests.post(
                    "http://jaeger:16686/api/traces",
                    json=trace_data,
                    headers={"Content-Type": "application/json"},
                    timeout=1
                )
                logging.info(f"Jaeger trace submission result: {r.status_code}")
            except Exception as e:
                logging.error(f"Error sending trace to Jaeger: {str(e)}")
                
        except Exception as e:
            logging.error(f"Error creating manual trace: {str(e)}")
        
        return response
