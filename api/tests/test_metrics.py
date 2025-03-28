from fastapi.testclient import TestClient
import pytest
from prometheus_client import REGISTRY

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_metrics_endpoint_exists(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text


def test_request_count_metric(client):
    # Make a test request
    client.get("/api/health")
    
    # Get metrics
    response = client.get("/metrics")
    assert response.status_code == 200
    
    # Check if request was counted - use partial match since labels might have different order
    assert 'http_requests_total{' in response.text
    assert 'endpoint="/api/health"' in response.text
    assert 'method="GET"' in response.text
    assert 'status="200"' in response.text


def test_error_metric(client):
    # Make a request to non-existent endpoint
    client.get("/api/nonexistent")
    
    # Get metrics
    response = client.get("/metrics")
    assert response.status_code == 200
    
    # Check if error was counted - use partial match since labels might have different order
    assert 'http_requests_total{' in response.text
    assert 'endpoint="/api/nonexistent"' in response.text
    assert 'method="GET"' in response.text
    assert 'status="404"' in response.text


def test_latency_metric(client):
    # Make a test request
    client.get("/api/health")
    
    # Get metrics
    response = client.get("/metrics")
    assert response.status_code == 200
    
    # Check if latency was recorded - use partial match for histogram metrics
    assert 'http_request_duration_seconds_bucket{' in response.text
    assert 'endpoint="/api/health"' in response.text
    assert 'method="GET"' in response.text


def test_active_requests_metric(client):
    # Make test request
    client.get("/api/health")
    
    # Get metrics
    response = client.get("/metrics")
    assert response.status_code == 200
    
    # Check for the active requests metric in the response
    assert "http_requests_active" in response.text 