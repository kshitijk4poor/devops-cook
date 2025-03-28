import pytest
from fastapi.testclient import TestClient
from app.main import app
import time
import httpx

client = TestClient(app)

def test_metrics_endpoint():
    """Test that metrics endpoint is accessible"""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text

def test_fast_endpoint_metrics():
    """Test metrics for fast endpoint"""
    # Make request to fast endpoint
    response = client.get("/demo/fast")
    assert response.status_code == 200
    
    # Check metrics
    metrics = client.get("/metrics").text
    assert 'http_requests_total{endpoint="/demo/fast",method="GET",status_code="200"}' in metrics
    assert "http_request_duration_seconds" in metrics

def test_slow_endpoint_metrics():
    """Test metrics for slow endpoint"""
    # Make request to slow endpoint
    response = client.get("/demo/slow")
    assert response.status_code == 200
    
    # Check metrics
    metrics = client.get("/metrics").text
    assert 'http_requests_total{endpoint="/demo/slow",method="GET",status_code="200"}' in metrics
    assert "db_operation_duration_seconds" in metrics

def test_error_prone_endpoint_metrics():
    """Test metrics for error-prone endpoint"""
    # Make multiple requests to ensure we hit both success and error cases
    error_count = 0
    success_count = 0
    
    for _ in range(20):  # Increased to ensure we get both cases
        try:
            response = client.get("/demo/simple-error")
            if response.status_code == 200:
                success_count += 1
        except (httpx.HTTPError, ValueError, RuntimeError):
            error_count += 1
    
    assert error_count > 0, "Should have encountered at least one error"
    assert success_count > 0, "Should have had at least one success"
    
    # Check metrics
    metrics = client.get("/metrics").text
    assert "error_count_total" in metrics
    assert 'http_requests_total{endpoint="/demo/simple-error"' in metrics

def test_external_endpoint_metrics():
    """Test metrics for external-dependent endpoint"""
    # Make request to external endpoint
    response = client.get("/demo/external/false")
    assert response.status_code == 200
    
    # Check metrics
    metrics = client.get("/metrics").text
    assert "external_api_duration_seconds" in metrics
    assert 'service="httpbin"' in metrics

def test_active_requests_gauge():
    """Test active requests gauge"""
    # Start a slow request in the background
    with client.stream("GET", "/demo/slow") as response:
        # Give the request time to start
        time.sleep(0.5)
        
        # Check metrics while request is in progress
        metrics = client.get("/metrics").text
        assert 'active_requests{endpoint="/demo/slow"}' in metrics
        assert '0.0' not in metrics.split('\n')[-1]  # Should not be 0
    
    # After request completes, check that counter decreased
    time.sleep(0.1)  # Give metrics time to update
    metrics = client.get("/metrics").text
    assert 'active_requests{endpoint="/demo/slow"} 0.0' in metrics 