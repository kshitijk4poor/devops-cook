import os
from typing import Callable, Dict, List, Optional

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased, ParentBased
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
        excluded_endpoints = ["/metrics", "/health"]
    
    # Convert excluded_endpoints list to comma-separated string for FastAPIInstrumentor
    excluded_urls = ",".join(excluded_endpoints) if excluded_endpoints else ""
    
    # Get Jaeger configuration from environment variables
    jaeger_host = os.getenv("JAEGER_HOST", "localhost")
    jaeger_port = int(os.getenv("JAEGER_PORT", 6831))
    
    # Configure sampling rate
    sampling_rate = float(os.getenv("OTEL_SAMPLING_RATIO", 1.0))
    sampler = TraceIdRatioBased(sampling_rate)

    # Create resource attributes
    resource = Resource.create({
        "service.name": service_name,
        "service.version": "1.0.0",
        "deployment.environment": os.getenv("ENVIRONMENT", "development")
    })
    
    # Set the tracer provider
    provider = TracerProvider(resource=resource, sampler=sampler)
    trace.set_tracer_provider(provider)
    
    # Set up Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name=jaeger_host,
        agent_port=jaeger_port,
    )
    
    # Add span processor to the tracer provider
    provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
    
    # Instrument FastAPI with excluded_urls as a string
    FastAPIInstrumentor.instrument_app(
        app,
        excluded_urls=excluded_urls,
        tracer_provider=provider,
    )
    
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
    
    def span_details_callback(span, scope):
        if scope.get("type") == "http":
            if scope.get("request"):
                span.set_attribute(SpanAttributes.HTTP_METHOD, scope.get("request").get("method", ""))
                span.set_attribute(SpanAttributes.HTTP_URL, scope.get("request").get("url", ""))
                span.set_attribute(SpanAttributes.HTTP_TARGET, scope.get("request").get("path", ""))
                span.set_attribute(SpanAttributes.HTTP_CLIENT_IP, scope.get("request").get("client", {}).get("ip", ""))
            if scope.get("response"):
                span.set_attribute(SpanAttributes.HTTP_STATUS_CODE, scope.get("response").get("status_code", 0)) 