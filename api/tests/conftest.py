"""Common pytest fixtures for test suites."""

import json
import logging
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app as main_app
from app.middleware.logging import add_logging_middleware


@pytest.fixture
def app():
    """Create a test FastAPI application."""
    app = FastAPI()
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    @app.get("/error")
    async def error_endpoint():
        raise ValueError("Test error")
    
    return app


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    with patch("logging.Logger.info") as mock_info, \
         patch("logging.Logger.error") as mock_error, \
         patch("logging.Logger.warning") as mock_warning, \
         patch("logging.Logger.debug") as mock_debug:
        yield {
            "info": mock_info,
            "error": mock_error,
            "warning": mock_warning,
            "debug": mock_debug
        }


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI application with middleware."""
    # Patch the setup_logging function to prevent actual logging setup
    with patch("app.middleware.logging.setup_logging"):
        add_logging_middleware(app)
        return TestClient(app)


@pytest.fixture
def main_client():
    """Create a test client for the main application."""
    return TestClient(main_app)


@pytest.fixture
def mock_jaeger_exporter():
    """Mock the Jaeger exporter."""
    with patch("opentelemetry.exporter.jaeger.thrift.JaegerExporter") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_prometheus():
    """Mock Prometheus metrics."""
    with patch("prometheus_client.Counter") as mock_counter, \
         patch("prometheus_client.Histogram") as mock_histogram, \
         patch("prometheus_client.Gauge") as mock_gauge:
        yield {
            "counter": mock_counter,
            "histogram": mock_histogram,
            "gauge": mock_gauge
        } 