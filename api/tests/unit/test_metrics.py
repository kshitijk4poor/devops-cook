"""Unit tests for metrics middleware."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi import Request, Response, FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, Gauge

from app.middleware.metrics import PrometheusMiddleware, REQUEST_COUNT, REQUEST_LATENCY, ACTIVE_REQUESTS, ERROR_COUNT


class TestPrometheusMiddleware:
    """Test the PrometheusMiddleware class."""

    @pytest.fixture
    def app(self):
        """Create a test FastAPI application."""
        return MagicMock(spec=FastAPI)

    @pytest.fixture
    def middleware(self, app):
        """Create a PrometheusMiddleware instance."""
        return PrometheusMiddleware(app)

    @pytest.fixture
    def mock_request(self):
        """Create a mock Request object."""
        mock_req = MagicMock(spec=Request)
        mock_req.method = "GET"
        mock_req.url.path = "/test"
        return mock_req

    @pytest.fixture
    def mock_response(self):
        """Create a mock Response object."""
        mock_resp = MagicMock(spec=Response)
        mock_resp.status_code = 200
        return mock_resp

    @pytest.fixture
    def mock_metrics(self):
        """Mock all Prometheus metric objects."""
        with patch("app.middleware.metrics.REQUEST_COUNT") as mock_count, \
             patch("app.middleware.metrics.REQUEST_LATENCY") as mock_latency, \
             patch("app.middleware.metrics.ACTIVE_REQUESTS") as mock_active, \
             patch("app.middleware.metrics.ERROR_COUNT") as mock_error:
            
            # Configure the mock metrics
            mock_count.labels.return_value.inc = MagicMock()
            mock_latency.labels.return_value.observe = MagicMock()
            mock_active.labels.return_value.inc = MagicMock()
            mock_active.labels.return_value.dec = MagicMock()
            mock_error.labels.return_value.inc = MagicMock()
            
            yield {
                "count": mock_count,
                "latency": mock_latency,
                "active": mock_active,
                "error": mock_error
            }

    @pytest.mark.asyncio
    async def test_successful_request(self, middleware, mock_request, mock_response, mock_metrics):
        """Test metrics are recorded for successful requests."""
        # Setup mock call_next coroutine that returns the mock response
        async def mock_call_next(_):
            return mock_response

        # Execute the middleware
        response = await middleware.dispatch(mock_request, mock_call_next)

        # Assert the response passes through unchanged
        assert response == mock_response

        # Check that metrics were incremented properly
        mock_metrics["active"].labels.assert_called_with(method="GET", endpoint="/test")
        mock_metrics["active"].labels.return_value.inc.assert_called_once()
        mock_metrics["active"].labels.return_value.dec.assert_called_once()
        
        mock_metrics["count"].labels.assert_called_with(method="GET", endpoint="/test", status=200)
        mock_metrics["count"].labels.return_value.inc.assert_called_once()
        
        mock_metrics["latency"].labels.assert_called_with(method="GET", endpoint="/test")
        mock_metrics["latency"].labels.return_value.observe.assert_called_once()
        
        # Error metric should not be called
        mock_metrics["error"].labels.assert_not_called()

    @pytest.mark.asyncio
    async def test_failed_request(self, middleware, mock_request, mock_metrics):
        """Test metrics are recorded for failed requests."""
        # Setup mock call_next that raises an exception
        test_exception = ValueError("Test exception")
        
        async def mock_call_next_error(_):
            raise test_exception

        # Execute the middleware and expect exception to propagate
        with pytest.raises(ValueError):
            await middleware.dispatch(mock_request, mock_call_next_error)

        # Check that metrics were incremented properly
        mock_metrics["active"].labels.assert_called_with(method="GET", endpoint="/test")
        mock_metrics["active"].labels.return_value.inc.assert_called_once()
        mock_metrics["active"].labels.return_value.dec.assert_called_once()
        
        # Request count should not be called (as it's only called on success)
        mock_metrics["count"].labels.assert_not_called()
        
        # Error metric should be called
        mock_metrics["error"].labels.assert_called_with(
            method="GET", 
            endpoint="/test", 
            error_type="ValueError"
        )
        mock_metrics["error"].labels.return_value.inc.assert_called_once() 