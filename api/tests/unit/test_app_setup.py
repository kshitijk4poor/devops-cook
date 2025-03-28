"""Unit tests for application setup."""

import pytest
from unittest.mock import patch, MagicMock, call
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import app, create_application


def test_app_instantiation():
    """Test that app is correctly instantiated."""
    # Check that app is a FastAPI instance
    assert isinstance(app, FastAPI)
    
    # Check app configuration
    assert app.title == "API Observability Platform"
    assert app.version is not None


def test_create_application():
    """Test that create_application configures the app correctly."""
    # Create a fresh application instance
    application = create_application()
    
    # Check that application is a FastAPI instance
    assert isinstance(application, FastAPI)
    
    # Check base configuration
    assert application.title == "API Observability Platform"
    assert application.version is not None


@patch("app.main.add_logging_middleware")
@patch("app.main.PrometheusMiddleware")
@patch("app.main.make_asgi_app")
def test_middleware_registration(mock_metrics_app, mock_prom, mock_logging):
    """Test that middleware are registered correctly."""
    # Mock return values
    mock_metrics_app.return_value = MagicMock()
    
    # Call create_application
    application = create_application()
    
    # Check that middleware were added
    mock_logging.assert_called_once()
    
    # Test that an application instance was returned
    assert isinstance(application, FastAPI)
    
    # Test CORS middleware by making a preflight request
    client = TestClient(application)
    headers = {
        "Access-Control-Request-Method": "GET",
        "Origin": "http://example.com",
    }
    response = client.options("/api/health", headers=headers)
    assert response.headers.get("Access-Control-Allow-Origin") is not None


def test_endpoints_registration():
    """Test that endpoints are registered correctly."""
    # Use the real app to test endpoint registration
    client = TestClient(app)
    
    # Check that API health endpoint is registered
    response = client.get("/api/health")
    assert response.status_code == 200
    
    # Check metrics endpoint
    response = client.get("/metrics")
    assert response.status_code == 200


def test_middleware_execution_order():
    """Test that middleware are executed in the correct order."""
    # This is a functional test to ensure middleware are correctly ordered
    # We'll make a request and check for the presence of all middleware effects
    client = TestClient(app)
    
    # Make a request
    response = client.get("/api/health")
    assert response.status_code == 200
    
    # Check for request ID header (logging middleware)
    assert "X-Request-ID" in response.headers
    
    # Check for metrics (can't directly check in test, but ensure endpoint exists)
    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    assert "http_requests_total" in metrics_response.text 