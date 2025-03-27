"""Tests for the logging middleware."""

import json
import logging
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from app.middleware.logging import (
    RequestContextMiddleware, 
    RequestLoggingMiddleware, 
    setup_logging, 
    add_logging_middleware
)


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
def client(app):
    """Create a test client for the FastAPI application."""
    # Patch the setup_logging function to prevent actual logging setup
    with patch("app.middleware.logging.setup_logging"):
        add_logging_middleware(app)
        return TestClient(app)


def test_request_id_middleware(app):
    """Test that RequestContextMiddleware adds request ID."""
    # Add only the request context middleware
    app.add_middleware(RequestContextMiddleware)
    client = TestClient(app)
    
    # Make a request
    response = client.get("/test")
    
    # Check that X-Request-ID header is present
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 0


@patch("logging.Logger.info")
def test_request_logging_success(mock_info, client):
    """Test that RequestLoggingMiddleware logs successful requests."""
    # Make a request
    response = client.get("/test")
    assert response.status_code == 200
    
    # Check that logger.info was called at least twice (could include startup log)
    assert mock_info.call_count >= 2
    
    # Find the request_started and request_completed logs
    start_log = None
    completed_log = None
    
    # Parse and check each log call
    for args in mock_info.call_args_list:
        log_arg = args[0][0]
        # Skip if not JSON
        if not (isinstance(log_arg, str) and log_arg.startswith('{')):
            continue
            
        log_data = json.loads(log_arg)
        if log_data.get("event") == "request_started":
            start_log = log_data
        elif log_data.get("event") == "request_completed":
            completed_log = log_data
    
    # Verify request_started log
    assert start_log is not None, "request_started log not found"
    assert start_log["path"] == "/test"
    assert start_log["method"] == "GET"
    assert "request_id" in start_log
    
    # Verify request_completed log
    assert completed_log is not None, "request_completed log not found"
    assert completed_log["path"] == "/test"
    assert completed_log["method"] == "GET"
    assert completed_log["status_code"] == 200
    assert "duration" in completed_log
    assert "request_id" in completed_log


@patch("logging.Logger.error")
def test_request_logging_error(mock_error, client):
    """Test that RequestLoggingMiddleware logs failed requests."""
    # Make a request that will cause an error
    with pytest.raises(Exception):
        client.get("/error")
    
    # Check that logger.error was called
    mock_error.assert_called_once()
    
    # Check call arguments
    call_args = mock_error.call_args[0][0]
    log_data = json.loads(call_args)
    assert log_data["event"] == "request_failed"
    assert log_data["path"] == "/error"
    assert log_data["method"] == "GET"
    assert "error" in log_data
    assert "duration" in log_data
    assert "request_id" in log_data


@patch("logging.Logger.setLevel")
@patch("logging.StreamHandler")
def test_setup_logging(mock_handler, mock_set_level):
    """Test setup_logging function."""
    # Call setup_logging
    with patch("logging.getLogger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        setup_logging()
        
        # Check that loggers were configured
        assert mock_get_logger.call_count >= 2
        mock_logger.setLevel.assert_called() 