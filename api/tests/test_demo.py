"""Tests for demo API endpoints."""

import time
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import httpx

from app.main import app
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

client = TestClient(app)


@pytest.fixture
def memory_exporter():
    """Fixture to create in-memory trace exporter for testing."""
    # Create in-memory exporter
    exporter = InMemorySpanExporter()
    
    # Configure test trace provider
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    
    # Set as global provider for testing
    previous_provider = trace.get_tracer_provider()
    trace.set_tracer_provider(provider)
    
    yield exporter
    
    # Restore previous provider
    trace.set_tracer_provider(previous_provider)
    
    # Clear spans
    exporter.clear()


def test_normal_endpoint():
    """Test the normal endpoint returns 200 and correct data structure."""
    response = client.get("/api/demo/normal")
    assert response.status_code == 200
    data = response.json()
    
    assert "message" in data
    assert "timestamp" in data
    assert "endpoint_type" in data
    assert "data" in data
    assert data["endpoint_type"] == "normal"


def test_normal_endpoint_tracing(memory_exporter):
    """Test that the normal endpoint creates the expected spans and attributes."""
    # Make request
    response = client.get("/api/demo/normal")
    assert response.status_code == 200
    
    # Get exported spans
    spans = memory_exporter.get_finished_spans()
    
    # Find our custom span
    processing_span = None
    for span in spans:
        if span.name == "normal_request_processing":
            processing_span = span
            break
    
    # Verify span exists
    assert processing_span is not None
    
    # Verify span attributes
    attributes = processing_span.attributes
    assert attributes.get("business.endpoint_type") == "normal"
    assert attributes.get("business.importance") == "low"
    assert attributes.get("business.expected_latency_ms") == 5
    assert attributes.get("business.domain") == "demo"
    
    # Verify events
    events = processing_span.events
    assert len(events) == 2
    assert events[0].name == "processing_started"
    assert events[1].name == "processing_completed"
    assert "timestamp" in events[0].attributes
    assert "duration_ms" in events[1].attributes


def test_slow_endpoint():
    """Test the slow endpoint returns 200 and includes processing time."""
    start_time = time.time()
    response = client.get("/api/demo/slow")
    end_time = time.time()
    
    assert response.status_code == 200
    data = response.json()
    
    # Check response format
    assert "message" in data
    assert "timestamp" in data
    assert "endpoint_type" in data
    assert "data" in data
    assert data["endpoint_type"] == "slow"
    
    # Verify the endpoint actually took some time
    assert end_time - start_time >= 2.0
    
    # Verify processing time is included in response
    assert "processing_time_ms" in data["data"]
    assert "simulated_component" in data["data"]
    assert data["data"]["simulated_component"] == "database"


def test_slow_endpoint_tracing(memory_exporter):
    """Test that the slow endpoint creates the expected spans and attributes."""
    # Mock sleep to speed up test
    with patch("asyncio.sleep", return_value=None):
        # Make request with custom parameters
        response = client.get("/api/demo/slow?delay_min=0.1&delay_max=0.2&simulate_processing=true")
        assert response.status_code == 200
        
        # Get exported spans
        spans = memory_exporter.get_finished_spans()
        
        # Find our custom spans
        main_span = None
        db_span = None
        processing_span = None
        
        for span in spans:
            if span.name == "slow_endpoint_operation":
                main_span = span
            elif span.name == "database_query":
                db_span = span
            elif span.name == "post_processing":
                processing_span = span
        
        # Verify main span exists and has correct attributes
        assert main_span is not None
        assert main_span.attributes.get("business.endpoint_type") == "slow"
        assert main_span.attributes.get("business.importance") == "medium"
        assert main_span.attributes.get("business.domain") == "demo"
        assert main_span.attributes.get("request.param.delay_min") == 0.1
        assert main_span.attributes.get("request.param.delay_max") == 0.2
        assert main_span.attributes.get("request.param.simulate_processing") is True
        
        # Verify database span exists and has correct attributes
        assert db_span is not None
        assert db_span.attributes.get("db.operation.type") == "query"
        assert db_span.attributes.get("db.system") == "postgres"
        assert db_span.attributes.get("db.name") == "demo_db"
        assert "db.statement" in db_span.attributes
        assert "db.execution_time_seconds" in db_span.attributes
        
        # Check events in DB span
        db_events = db_span.events
        assert len(db_events) >= 2
        assert db_events[0].name == "db_query_started"
        assert db_events[1].name == "db_query_completed"
        assert "records_fetched" in db_events[1].attributes
        
        # Verify processing span exists if simulate_processing is true
        assert processing_span is not None
        assert processing_span.attributes.get("processing.type") == "data_transformation"
        assert processing_span.attributes.get("processing.complexity") == "medium"
        
        # Check events in processing span
        proc_events = processing_span.events
        assert len(proc_events) >= 2
        assert proc_events[0].name == "processing_started"
        assert proc_events[1].name == "processing_completed"
        assert "duration_seconds" in proc_events[1].attributes


def test_error_prone_endpoint_success():
    """Test the error-prone endpoint when it succeeds."""
    # Mock random to always return 0.5 (above error threshold of 0.3)
    with patch("random.random", return_value=0.5):
        response = client.get("/api/demo/error-prone")
        assert response.status_code == 200
        data = response.json()
        
        assert data["endpoint_type"] == "error-prone"
        assert data["data"]["error_probability"] == 0.3


def test_error_prone_endpoint_failure():
    """Test the error-prone endpoint when it fails."""
    # Mock random to always return 0.1 (below error threshold of 0.3)
    with patch("random.random", return_value=0.1):
        response = client.get("/api/demo/error-prone")
        assert response.status_code == 500
        data = response.json()
        
        assert "detail" in data
        assert data["detail"] == "Random server error occurred"


def test_error_prone_endpoint_tracing_success(memory_exporter):
    """Test tracing for error-prone endpoint on success."""
    # Mock random to ensure success
    with patch("random.random", return_value=0.5):
        # Make request with custom parameters
        response = client.get("/api/demo/error-prone?error_probability=0.4&error_type=timeout")
        assert response.status_code == 200
        
        # Get exported spans
        spans = memory_exporter.get_finished_spans()
        
        # Find our span
        error_span = None
        for span in spans:
            if span.name == "error_prone_operation":
                error_span = span
                break
        
        # Verify span exists and has correct attributes
        assert error_span is not None
        assert error_span.attributes.get("business.endpoint_type") == "error-prone"
        assert error_span.attributes.get("business.importance") == "high"
        assert error_span.attributes.get("business.domain") == "demo"
        assert error_span.attributes.get("error.probability") == 0.4
        assert error_span.attributes.get("error.type") == "timeout"
        
        # Verify events
        events = error_span.events
        assert len(events) >= 2
        assert events[0].name == "operation_started"
        assert events[-1].name == "operation_completed"
        
        # Verify status
        assert error_span.status.status_code == trace.StatusCode.OK


def test_error_prone_endpoint_tracing_failure(memory_exporter):
    """Test tracing for error-prone endpoint on failure."""
    # Mock random to ensure failure
    with patch("random.random", return_value=0.1):
        # Make request with custom parameters
        response = client.get("/api/demo/error-prone?error_type=validation")
        assert response.status_code == 400  # Validation error returns 400
        
        # Get exported spans
        spans = memory_exporter.get_finished_spans()
        
        # Find our span
        error_span = None
        for span in spans:
            if span.name == "error_prone_operation":
                error_span = span
                break
        
        # Verify span exists and has correct attributes
        assert error_span is not None
        assert error_span.attributes.get("error.type") == "ValidationError"
        assert error_span.attributes.get("error.message") == "Validation error in request"
        assert error_span.attributes.get("error.status_code") == 400
        
        # Verify error events
        events = error_span.events
        assert len(events) >= 3
        assert events[0].name == "operation_started"
        assert "error_condition_detected" in [e.name for e in events]
        assert "error_occurred" in [e.name for e in events]
        
        # Verify status
        assert error_span.status.status_code == trace.StatusCode.ERROR


def test_external_dependent_endpoint_success():
    """Test the external-dependent endpoint when the external call succeeds."""
    # Use patch to avoid making actual HTTP requests during tests
    with patch("httpx.AsyncClient.get") as mock_get:
        # Configure mock response
        mock_response = mock_get.return_value
        mock_response.json.return_value = {"mock": "data"}
        mock_response.raise_for_status.return_value = None
        mock_response.status_code = 200
        mock_response.content = b'{"mock": "data"}'
        
        response = client.get("/api/demo/external/false")
        assert response.status_code == 200
        data = response.json()
        
        assert data["endpoint_type"] == "external-dependent"
        assert "external_service" in data["data"]
        assert "processing_time_ms" in data["data"]
        assert "external_data" in data["data"]


def test_external_dependent_endpoint_timeout():
    """Test the external-dependent endpoint when the external call times out."""
    # Simulate a timeout from the external service
    with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("Timeout")):
        response = client.get("/api/demo/external/false")
        assert response.status_code == 504
        data = response.json()
        
        assert "detail" in data
        assert data["detail"] == "Timeout while calling external service"


def test_external_dependent_endpoint_tracing_success(memory_exporter):
    """Test tracing for external-dependent endpoint on success."""
    # Mock traced_http_request
    mock_response = MagicMock()
    mock_response.json.return_value = {"mock": "data"}
    mock_response.status_code = 200
    mock_response.content = b'{"mock": "data"}'
    
    with patch("app.utils.tracing.traced_http_request", return_value=mock_response):
        # Make request with traced client
        response = client.get("/api/demo/external/true?service_url=https://test-api.com/data")
        assert response.status_code == 200
        
        # Get exported spans
        spans = memory_exporter.get_finished_spans()
        
        # Find our spans
        main_span = None
        request_span = None
        
        for span in spans:
            if span.name == "external_service_operation":
                main_span = span
            elif span.name == "external_service_request":
                request_span = span
        
        # Verify main span exists and has correct attributes
        assert main_span is not None
        assert main_span.attributes.get("business.endpoint_type") == "external-dependent"
        assert main_span.attributes.get("business.importance") == "high"
        assert main_span.attributes.get("business.domain") == "demo"
        assert main_span.attributes.get("external_service.url") == "https://test-api.com/data"
        assert main_span.attributes.get("external_service.success") is True
        
        # Verify request span exists and has correct attributes
        assert request_span is not None
        assert request_span.attributes.get("external_service.url") == "https://test-api.com/data"
        assert request_span.attributes.get("external_service.protocol") == "https"
        
        # Verify events in main span
        main_events = main_span.events
        assert len(main_events) >= 2
        assert main_events[0].name == "external_operation_started"
        assert main_events[-1].name == "external_operation_completed"
        
        # Verify status
        assert main_span.status.status_code == trace.StatusCode.UNSET  # Unset means no error


def test_external_dependent_endpoint_tracing_error(memory_exporter):
    """Test tracing for external-dependent endpoint on error."""
    # Simulate a timeout from the external service
    with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("Timeout")):
        # Make request without traced client
        response = client.get("/api/demo/external/false")
        assert response.status_code == 504
        
        # Get exported spans
        spans = memory_exporter.get_finished_spans()
        
        # Find our spans
        main_span = None
        request_span = None
        
        for span in spans:
            if span.name == "external_service_operation":
                main_span = span
            elif span.name == "external_service_request":
                request_span = span
        
        # Verify main span exists and has correct attributes
        assert main_span is not None
        assert main_span.attributes.get("external_service.success") is False
        assert main_span.attributes.get("error.type") == "timeout"
        
        # Verify request span exists and has correct attributes
        assert request_span is not None
        assert request_span.attributes.get("error.type") == "timeout"
        
        # Verify error events
        request_events = request_span.events
        timeout_events = [e for e in request_events if e.name == "external_service_timeout"]
        assert len(timeout_events) > 0
        
        # Verify status
        assert request_span.status.status_code == trace.StatusCode.ERROR 