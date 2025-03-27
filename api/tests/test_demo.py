"""Tests for demo API endpoints."""

import time
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import httpx

from app.main import app

client = TestClient(app)


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


def test_external_dependent_endpoint_success():
    """Test the external-dependent endpoint when the external call succeeds."""
    # Use patch to avoid making actual HTTP requests during tests
    with patch("httpx.AsyncClient.get") as mock_get:
        # Configure mock response
        mock_response = mock_get.return_value
        mock_response.json.return_value = {"mock": "data"}
        mock_response.raise_for_status.return_value = None
        
        response = client.get("/api/demo/external")
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
        response = client.get("/api/demo/external")
        assert response.status_code == 504
        data = response.json()
        
        assert "detail" in data
        assert data["detail"] == "Timeout while calling external service" 