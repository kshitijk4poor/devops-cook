import os
from typing import Callable, Dict, List, Optional

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware
from opentelemetry.semconv.trace import SpanAttributes

from app.core.trace_config import get_trace_config

def setup_tracing(app: FastAPI, service_name: str = "api-service", excluded_endpoints: Optional[List[str]] = None) -> None:
    """
    Set up OpenTelemetry tracing middleware for FastAPI application.
    
    Args:
        app: FastAPI application
        service_name: Name of the service for tracing
        excluded_endpoints: List of endpoints to exclude from tracing
    """
    # Default excluded endpoints
    if excluded_endpoints is None:
        excluded_endpoints = ["/metrics"]  # Remove /health from excluded to get it in traces
    
    # Make sure we're not excluding the health endpoint
    if "/health" in excluded_endpoints:
        excluded_endpoints.remove("/health")
    if "/api/health" in excluded_endpoints:
        excluded_endpoints.remove("/api/health")
    
    # Convert excluded_endpoints list to comma-separated string for FastAPIInstrumentor
    excluded_urls = ",".join(excluded_endpoints) if excluded_endpoints else ""
    
    # Get Jaeger configuration from environment variables
    jaeger_host = os.getenv("JAEGER_HOST", "localhost")
    jaeger_port = int(os.getenv("JAEGER_PORT", 6831))
    
    # Override service name with environment variable if available
    service_name = os.getenv("OTEL_SERVICE_NAME", service_name)
    
    # Configure sampling rate - use 1.0 (100%) to ensure we catch all traces
    sampling_rate = 1.0
    sampler = TraceIdRatioBased(sampling_rate)

    # Create resource with explicit service name
    resource = Resource.create({
        SERVICE_NAME: service_name,
        SERVICE_VERSION: "1.0.0",
        "deployment.environment": os.getenv("ENVIRONMENT", "development")
    })
    
    # Set the tracer provider with resource
    provider = TracerProvider(resource=resource, sampler=sampler)
    trace.set_tracer_provider(provider)
    
    # Set up Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name=jaeger_host,
        agent_port=jaeger_port,
    )
    
    # Add span processors to the tracer provider
    provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
    
    # Always add console exporter for debugging health endpoint traces
    provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    
    # Add logging to help diagnose the issue
    print(f"Setting up tracing with service name: {service_name}")
    print(f"Excluded endpoints: {excluded_endpoints}")
    print(f"Jaeger configuration: Host={jaeger_host}, Port={jaeger_port}")
    print(f"Sampling rate: {sampling_rate}")
    
    # Create an explicit list of all expected operations
    expected_operations = [
        "GET /api/health",
        "GET /api/demo/random",
        "POST /api/demo/echo"
    ]
    print(f"Expected operations: {expected_operations}")
    
    # Custom span name callback for better operation naming
    def custom_span_name(scope):
        if scope and scope.get("type") == "http" and scope.get("request"):
            method = scope.get("request").get("method", "").upper()
            path = scope.get("request").get("path", "")
            
            print(f"Trace request: {method} {path}")
            
            # Special handling for health endpoint
            if path.endswith("/health"):
                print(f"Health endpoint detected in custom_span_name: {method} {path}")
                print(f"Scope details for health endpoint: {scope}")
                return f"{method} {path}"
                
            # For FastAPI routes, remove any patterns like {id:int} to make cleaner operation names
            if scope.get("route"):
                # Use a standardized name format for all operations
                return f"{method} {path}"
            else:
                # For requests without an explicit route
                return f"{method} {path}"
            
        # For non-HTTP spans, preserve the original span names (like manual spans from application code)
        return scope.get("name", "unknown")
    
    # Span details callback to add attributes to spans
    def span_details_callback(span, scope):
        if scope.get("type") == "http":
            # Add HTTP attributes
            if scope.get("request"):
                span.set_attribute(SpanAttributes.HTTP_METHOD, scope.get("request").get("method", ""))
                span.set_attribute(SpanAttributes.HTTP_URL, scope.get("request").get("url", ""))
                span.set_attribute(SpanAttributes.HTTP_TARGET, scope.get("request").get("path", ""))
                span.set_attribute(SpanAttributes.HTTP_CLIENT_IP, scope.get("request").get("client", {}).get("ip", ""))
                
                # Add request_id if available in headers
                headers = scope.get("request").get("headers", {})
                if headers.get("x-request-id"):
                    span.set_attribute("request.id", headers.get("x-request-id"))
                
                # Add route name if available
                if scope.get("route"):
                    span.set_attribute("fastapi.route", scope.get("route"))
                
                # Explicitly set service name in each span
                span.set_attribute("service.name", service_name)
                    
            # Add response attributes
            if scope.get("response"):
                span.set_attribute(SpanAttributes.HTTP_STATUS_CODE, scope.get("response").get("status_code", 0))
                
                # Mark error spans for filtering
                status_code = scope.get("response").get("status_code", 0)
                if status_code >= 400:
                    span.set_attribute("error", True)
                    span.set_attribute("error.type", "server_error" if status_code >= 500 else "client_error")
    
    # Instrument FastAPI with custom settings
    FastAPIInstrumentor.instrument_app(
        app,
        excluded_urls=excluded_urls,
        tracer_provider=provider,
        span_callback=span_details_callback,
        name_callback=custom_span_name,
        meter_provider=None,
        trace_execution_time=True  # This helps ensure operations appear in the UI
    )
    
    print(f"FastAPI instrumentation complete with excluded_urls={excluded_urls}")
    
    # Create a filter for request/response body inclusion in spans
    def should_include_request_body(req):
        # Don't include bodies for specific endpoints or content types
        if req.url.path in excluded_endpoints:
            return False
        return True
    
    def should_include_response_body(resp):
        # Don't include bodies for specific endpoints or content types
        if hasattr(resp, 'url') and resp.url.path in excluded_endpoints:
            return False
        return True 