"""Unit tests for logging middleware."""

import json
import logging
import uuid
from unittest.mock import MagicMock, patch, call

import pytest
from fastapi import Request, Response, FastAPI
from starlette.middleware.base import BaseHTTPMiddleware

from app.middleware.logging import (
    RequestContextMiddleware,
    RequestLoggingMiddleware,
    setup_logging,
    add_logging_middleware
)


class TestRequestContextMiddleware:
    """Test RequestContextMiddleware class."""

    @pytest.fixture
    def app(self):
        """Create a test FastAPI application."""
        return MagicMock(spec=FastAPI)

    @pytest.fixture
    def middleware(self, app):
        """Create middleware instance."""
        return RequestContextMiddleware(app)

    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        mock_req = MagicMock(spec=Request)
        mock_req.state = MagicMock()
        return mock_req

    @pytest.fixture
    def mock_response(self):
        """Create mock response."""
        mock_resp = MagicMock(spec=Response)
        mock_resp.headers = {}
        return mock_resp

    @pytest.mark.asyncio
    async def test_adds_request_id(self, middleware, mock_request, mock_response):
        """Test that middleware adds request ID to state and response headers."""
        # Setup mock call_next
        async def mock_call_next(request):
            return mock_response

        # Call middleware
        response = await middleware.dispatch(mock_request, mock_call_next)

        # Verify request ID was added to state
        assert hasattr(mock_request.state, "request_id")
        assert isinstance(mock_request.state.request_id, str)
        assert len(mock_request.state.request_id) > 0

        # Verify request ID was added to response headers
        assert "X-Request-ID" in response.headers
        assert response.headers["X-Request-ID"] == mock_request.state.request_id


class TestRequestLoggingMiddleware:
    """Test RequestLoggingMiddleware class."""

    @pytest.fixture
    def app(self):
        """Create a test FastAPI application."""
        return MagicMock(spec=FastAPI)

    @pytest.fixture
    def middleware(self, app):
        """Create middleware instance."""
        return RequestLoggingMiddleware(app)

    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        mock_req = MagicMock(spec=Request)
        mock_req.url.path = "/test"
        mock_req.method = "GET"
        mock_req.client = MagicMock()
        mock_req.client.host = "127.0.0.1"
        
        # Set request_id in state
        mock_req.state = MagicMock()
        mock_req.state.request_id = str(uuid.uuid4())
        
        return mock_req

    @pytest.fixture
    def mock_response(self):
        """Create mock response."""
        mock_resp = MagicMock(spec=Response)
        mock_resp.status_code = 200
        mock_resp.headers = {}
        return mock_resp

    @pytest.mark.asyncio
    async def test_logs_successful_request(self, middleware, mock_request, mock_response, mock_logger):
        """Test that middleware logs successful requests."""
        # Setup mock call_next
        async def mock_call_next(request):
            return mock_response

        # Need to provide enough time mock returns for all calls in the middleware
        # First for start_time, then for timestamp in first log, then for end calculation, then for timestamp in second log
        mock_time = MagicMock()
        mock_time.side_effect = [100.0, 100.0, 100.5, 100.5]

        # Call middleware
        with patch("app.middleware.logging.time.time", mock_time):
            response = await middleware.dispatch(mock_request, mock_call_next)

        # Verify response was returned
        assert response == mock_response

        # Check that logs were created
        assert mock_logger["info"].call_count == 2
        
        # Check start log
        start_log_call = mock_logger["info"].call_args_list[0]
        start_log = json.loads(start_log_call[0][0])
        assert start_log["event"] == "request_started"
        assert start_log["path"] == "/test"
        assert start_log["method"] == "GET"
        assert start_log["client_host"] == "127.0.0.1"
        assert start_log["request_id"] == mock_request.state.request_id
        
        # Check end log
        end_log_call = mock_logger["info"].call_args_list[1]
        end_log = json.loads(end_log_call[0][0])
        assert end_log["event"] == "request_completed"
        assert end_log["path"] == "/test"
        assert end_log["method"] == "GET"
        assert end_log["status_code"] == 200
        assert end_log["request_id"] == mock_request.state.request_id
        assert end_log["duration"] == 0.5  # Mocked time difference

    @pytest.mark.asyncio
    async def test_logs_failed_request(self, middleware, mock_request, mock_logger):
        """Test that middleware logs failed requests."""
        # Setup mock call_next that raises an exception
        async def mock_call_next(request):
            raise ValueError("Test error")

        # Need enough mock time returns for all calls
        mock_time = MagicMock()
        mock_time.side_effect = [100.0, 100.0, 100.5, 100.5]

        # Call middleware and expect exception to propagate
        with patch("app.middleware.logging.time.time", mock_time), pytest.raises(ValueError):
            await middleware.dispatch(mock_request, mock_call_next)

        # Check that error was logged
        mock_logger["error"].assert_called_once()
        
        # Check error log
        error_log_call = mock_logger["error"].call_args
        error_log = json.loads(error_log_call[0][0])
        assert error_log["event"] == "request_failed"
        assert error_log["path"] == "/test"
        assert error_log["method"] == "GET"
        assert error_log["request_id"] == mock_request.state.request_id
        assert error_log["error"] == "Test error"
        assert error_log["duration"] == 0.5  # Mocked time difference


class TestSetupLogging:
    """Test the setup_logging function."""

    @patch("logging.getLogger")
    @patch("logging.StreamHandler")
    @patch("logging.Formatter")
    def test_setup_logging(self, mock_formatter_class, mock_handler_class, mock_get_logger):
        """Test the setup_logging function configures loggers."""
        # Setup mocks
        mock_root_logger = MagicMock()
        mock_api_logger = MagicMock()
        # Return different loggers for different calls
        mock_get_logger.side_effect = lambda name=None: mock_root_logger if name is None else mock_api_logger
        
        mock_handler = MagicMock()
        mock_handler_class.return_value = mock_handler
        
        mock_formatter = MagicMock()
        mock_formatter_class.return_value = mock_formatter
        
        # Call setup_logging
        setup_logging()
        
        # Verify the basics - loggers were created and handlers added
        assert mock_get_logger.call_count >= 2
        assert mock_root_logger.setLevel.called
        assert mock_root_logger.addHandler.called 