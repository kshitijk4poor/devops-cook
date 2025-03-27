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
    
    # Check if request was counted
    assert 'http_requests_total{endpoint="/api/health",method="GET",status="200"} 1.0' in response.text


def test_error_metric(client):
    # Make a request to non-existent endpoint
    client.get("/api/nonexistent")
    
    # Get metrics
    response = client.get("/metrics")
    assert response.status_code == 200
    
    # Check if error was counted
    assert 'http_requests_total{endpoint="/api/nonexistent",method="GET",status="404"} 1.0' in response.text


def test_latency_metric(client):
    # Make a test request
    client.get("/api/health")
    
    # Get metrics
    response = client.get("/metrics")
    assert response.status_code == 200
    
    # Check if latency was recorded
    assert 'http_request_duration_seconds_created{endpoint="/api/health",method="GET"}' in response.text
    assert 'http_request_duration_seconds_sum{endpoint="/api/health",method="GET"}' in response.text
    assert 'http_request_duration_seconds_count{endpoint="/api/health",method="GET"}' in response.text


def test_active_requests_metric(client):
    # Get initial metrics
    response = client.get("/metrics")
    initial_active = float(REGISTRY.get_sample_value(
        'http_requests_active',
        {'method': 'GET', 'endpoint': '/api/health'}
    ) or 0)
    
    # Make a test request
    client.get("/api/health")
    
    # Get metrics again
    response = client.get("/metrics")
    final_active = float(REGISTRY.get_sample_value(
        'http_requests_active',
        {'method': 'GET', 'endpoint': '/api/health'}
    ) or 0)
    
    # Active requests should return to initial value after request completion
    assert final_active == initial_active 