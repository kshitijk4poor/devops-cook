import os
import json
import httpx
from typing import Any, Dict, Optional

from opentelemetry import trace
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.context import Context
from opentelemetry.propagate import inject
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

tracer = trace.get_tracer(__name__)

async def traced_http_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    timeout: float = 10.0,
    span_name: Optional[str] = None,
    span_attributes: Optional[Dict[str, Any]] = None
) -> httpx.Response:
    """
    Send an HTTP request with OpenTelemetry tracing.
    
    Args:
        url: URL to send the request to
        method: HTTP method (GET, POST, etc.)
        headers: HTTP headers
        params: Query parameters
        json_data: JSON data to include in the request
        timeout: Request timeout in seconds
        span_name: Custom name for the span
        span_attributes: Additional span attributes
        
    Returns:
        Response from the HTTP request
    """
    if headers is None:
        headers = {}
    
    if span_attributes is None:
        span_attributes = {}
    
    # If no custom span name provided, use the url
    if span_name is None:
        span_name = f"{method} {url}"
    
    # Start a new span
    with tracer.start_as_current_span(
        span_name,
        kind=trace.SpanKind.CLIENT,
        attributes={
            SpanAttributes.HTTP_METHOD: method,
            SpanAttributes.HTTP_URL: url,
            **span_attributes
        }
    ) as span:
        # Inject trace context into headers
        inject(headers)
        
        # Add additional attributes for the request
        if params:
            span.set_attribute("http.params", str(params))
        
        if json_data:
            span.set_attribute("http.request.body", json.dumps(json_data))
        
        # Send the request
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_data,
                    timeout=timeout
                )
                
                # Add response information to the span
                span.set_attribute(SpanAttributes.HTTP_STATUS_CODE, response.status_code)
                
                # Record if there was an error
                if response.status_code >= 400:
                    span.set_status(trace.Status(
                        trace.StatusCode.ERROR,
                        f"HTTP request failed with status {response.status_code}"
                    ))
                    span.record_exception(Exception(f"HTTP {response.status_code}: {response.text}"))
                
                return response
                
        except Exception as e:
            # Record the exception in the span
            span.record_exception(e)
            span.set_status(trace.Status(
                trace.StatusCode.ERROR,
                str(e)
            ))
            raise 