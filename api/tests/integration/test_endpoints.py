"""Integration tests for API endpoints."""

import json
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


def test_health_endpoint(client):
    """Test the health endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "healthy"
    assert "timestamp" in response_data
    assert "version" in response_data


def test_metrics_endpoint(client):
    """Test the Prometheus metrics endpoint."""
    # Note: metrics endpoint redirects to /metrics/
    response = client.get("/metrics/", follow_redirects=True)
    assert response.status_code == 200
    # Check for typical metric names present in the response
    assert "http_requests_total" in response.text
    assert "http_request_duration_seconds" in response.text
    assert "python_info" in response.text  # Python metrics instead of process_cpu_seconds_total


def test_request_id_header(client):
    """Test that request ID header is added to responses."""
    response = client.get("/api/health")
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 0


def test_error_handling(client):
    """Test error handling for non-existent endpoints."""
    response = client.get("/api/nonexistent")
    assert response.status_code == 404
    assert "X-Request-ID" in response.headers


def test_request_flow(client):
    """Test a complete request flow."""
    # Make an initial request to check basic functionality
    response = client.get("/api/health")
    assert response.status_code == 200
    
    # Store the request ID
    request_id = response.headers["X-Request-ID"]
    assert len(request_id) > 0
    
    # Check metrics endpoint to verify request was counted
    metrics_response = client.get("/metrics/", follow_redirects=True)
    assert metrics_response.status_code == 200
    
    # Verify the health endpoint request was recorded in metrics
    assert 'http_requests_total{endpoint="/api/health",method="GET",status="200"}' in metrics_response.text
    
    # Verify metrics requests are also recorded
    # The metrics endpoint could be /metrics/ instead of /metrics due to trailing slash handling
    assert ('http_requests_total{endpoint="/metrics/",method="GET",status="200"}' in metrics_response.text or
            'http_requests_total{endpoint="/metrics",method="GET",status="200"}' in metrics_response.text) 