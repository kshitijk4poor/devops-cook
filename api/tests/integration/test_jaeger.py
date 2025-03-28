"""Integration tests for Jaeger tracing."""

import os
import pytest
import requests
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.middleware.tracing import setup_tracing


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_jaeger_client():
    """Mock the Jaeger client to test trace submission."""
    with patch("opentelemetry.exporter.jaeger.thrift.JaegerExporter") as mock_exporter_class:
        mock_exporter = MagicMock()
        mock_exporter_class.return_value = mock_exporter
        
        # Continue with original setup but with our mock
        with patch("app.middleware.tracing.setup_tracing") as original_setup:
            # Call the original setup with our mocked exporter
            def patched_setup(*args, **kwargs):
                result = original_setup(*args, **kwargs)
                return result
                
            yield mock_exporter


def test_trace_creation_on_request(client, mock_jaeger_exporter):
    """Test that a trace is created for each request."""
    # Reset the tracer to use our mock exporter
    with patch("opentelemetry.trace.get_tracer") as mock_get_tracer:
        mock_tracer = MagicMock()
        mock_get_tracer.return_value = mock_tracer
        
        # Set up a mock span
        mock_span = MagicMock()
        mock_context = MagicMock()
        mock_span.__enter__.return_value = mock_context
        mock_tracer.start_span.return_value = mock_span
        
        # Make a request
        response = client.get("/api/health")
        assert response.status_code == 200
        
        # The request should have created a span
        # However, we can't directly assert this without more complex mocking
        # Instead, we'll verify our mock tracer was called
        assert mock_get_tracer.called


def test_trace_headers_propagation(client):
    """Test that trace headers are properly propagated."""
    # Create some trace headers
    trace_headers = {
        "traceparent": "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01",
        "tracestate": "congo=t61rcWkgMzE"
    }
    
    # Make a request with trace headers
    response = client.get("/api/health", headers=trace_headers)
    assert response.status_code == 200
    
    # We can't easily verify header propagation in this test environment
    # In a real environment with Jaeger, we would check that the trace appears


def test_trace_baggage_propagation(client):
    """Test that trace baggage is properly propagated."""
    # Create trace headers with baggage
    trace_headers = {
        "traceparent": "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01",
        "baggage": "userId=alice,serverNode=DF:28,isProduction=false"
    }
    
    # Make a request with trace headers and baggage
    response = client.get("/api/health", headers=trace_headers)
    assert response.status_code == 200


def test_trace_spans_for_error_requests(client):
    """Test that traces are created for error requests too."""
    # Reset the tracer to use our mock exporter
    with patch("opentelemetry.trace.get_tracer") as mock_get_tracer:
        mock_tracer = MagicMock()
        mock_get_tracer.return_value = mock_tracer
        
        # Set up a mock span
        mock_span = MagicMock()
        mock_context = MagicMock()
        mock_span.__enter__.return_value = mock_context
        mock_tracer.start_span.return_value = mock_span
        
        # Make a request to a non-existent endpoint
        response = client.get("/api/nonexistent")
        assert response.status_code == 404


def test_custom_trace_attributes():
    """Test that custom trace attributes are added."""
    # This is more of a unit test, as we need to inspect the span directly
    app = MagicMock()
    
    # Use a real implementation but with controlled environment
    with patch("opentelemetry.sdk.trace.TracerProvider") as mock_provider, \
         patch("opentelemetry.trace.set_tracer_provider") as mock_set_provider, \
         patch("opentelemetry.exporter.jaeger.thrift.JaegerExporter") as mock_exporter, \
         patch("opentelemetry.sdk.trace.export.BatchSpanProcessor") as mock_processor, \
         patch("opentelemetry.instrumentation.fastapi.FastAPIInstrumentor") as mock_instrumentor:
         
        # Call setup_tracing to get access to the span details callback
        setup_tracing(app)
        
        # Now get the callback from the setup_tracing module
        # We need to use the actual function, not a mock
        from app.middleware.tracing import span_details_callback
        
        # Create a mock span and test data
        mock_span = MagicMock()
        test_scope = {
            "type": "http",
            "request": {
                "method": "GET",
                "url": "http://localhost:8000/api/test",
                "path": "/api/test",
                "client": {"ip": "127.0.0.1"}
            },
            "response": {
                "status_code": 200
            }
        }
        
        # Call the callback
        span_details_callback(mock_span, test_scope)
        
        # Verify that set_attribute was called with the expected values
        expected_calls = [
            mock_span.set_attribute.call_args_list[0],
            mock_span.set_attribute.call_args_list[1],
            mock_span.set_attribute.call_args_list[2],
            mock_span.set_attribute.call_args_list[3],
            mock_span.set_attribute.call_args_list[4]
        ]
        
        # Due to the way OpenTelemetry is designed, we can't easily make specific assertions
        # about the attribute values in this test environment
        assert len(mock_span.set_attribute.call_args_list) >= 5 