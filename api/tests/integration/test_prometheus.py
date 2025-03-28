"""Integration tests for Prometheus metrics."""

import pytest
import time
from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

from app.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


def test_prometheus_endpoint_accessible(client):
    """Verify that the Prometheus metrics endpoint is accessible."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


def test_default_metrics_present(client):
    """Verify that default process and Python metrics are present."""
    response = client.get("/metrics")
    assert response.status_code == 200
    
    # Check for default process metrics
    assert "process_cpu_seconds_total" in response.text
    assert "process_open_fds" in response.text
    assert "process_resident_memory_bytes" in response.text
    
    # Check for Python-specific metrics
    assert "python_info" in response.text
    assert "python_gc_objects_collected_total" in response.text


def test_http_request_metrics_incremented(client):
    """Test that HTTP request metrics are incremented properly."""
    # Get initial values
    initial_count = float(REGISTRY.get_sample_value(
        "http_requests_total",
        {"method": "GET", "endpoint": "/api/health", "status": "200"}
    ) or 0)
    
    # Make a request
    response = client.get("/api/health")
    assert response.status_code == 200
    
    # Verify count increased
    final_count = float(REGISTRY.get_sample_value(
        "http_requests_total",
        {"method": "GET", "endpoint": "/api/health", "status": "200"}
    ) or 0)
    
    assert final_count == initial_count + 1


def test_http_request_latency_recorded(client):
    """Test that HTTP request latency is properly recorded."""
    # Make a request
    response = client.get("/api/health")
    assert response.status_code == 200
    
    # Check that latency was recorded
    latency_sum = float(REGISTRY.get_sample_value(
        "http_request_duration_seconds_sum",
        {"method": "GET", "endpoint": "/api/health"}
    ) or 0)
    
    latency_count = float(REGISTRY.get_sample_value(
        "http_request_duration_seconds_count",
        {"method": "GET", "endpoint": "/api/health"}
    ) or 0)
    
    assert latency_sum > 0
    assert latency_count > 0


def test_error_metrics_incremented(client):
    """Test that error metrics are incremented for failed requests."""
    # Get initial values for 404 errors
    initial_count = float(REGISTRY.get_sample_value(
        "http_requests_total",
        {"method": "GET", "endpoint": "/api/nonexistent", "status": "404"}
    ) or 0)
    
    # Make a request to non-existent endpoint
    response = client.get("/api/nonexistent")
    assert response.status_code == 404
    
    # Verify count increased
    final_count = float(REGISTRY.get_sample_value(
        "http_requests_total",
        {"method": "GET", "endpoint": "/api/nonexistent", "status": "404"}
    ) or 0)
    
    assert final_count == initial_count + 1


def test_active_requests_metric(client):
    """Test that active requests metric is properly maintained."""
    # Get initial value
    initial_active = float(REGISTRY.get_sample_value(
        "http_requests_active",
        {"method": "GET", "endpoint": "/api/health"}
    ) or 0)
    
    # Make a request
    response = client.get("/api/health")
    assert response.status_code == 200
    
    # The active count should be back to the initial value after the request is done
    final_active = float(REGISTRY.get_sample_value(
        "http_requests_active",
        {"method": "GET", "endpoint": "/api/health"}
    ) or 0)
    
    assert final_active == initial_active 