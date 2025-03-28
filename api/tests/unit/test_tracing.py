"""Unit tests for tracing middleware."""

import os
from unittest.mock import patch, MagicMock, call

import pytest
from fastapi import FastAPI
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from app.middleware.tracing import setup_tracing


class TestTracingMiddleware:
    """Test the tracing middleware setup."""

    @pytest.fixture
    def app(self):
        """Create a test FastAPI application."""
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
            
        return app
        
    @pytest.fixture
    def mock_tracer_provider(self):
        """Mock the TracerProvider."""
        with patch("app.middleware.tracing.TracerProvider") as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider_class.return_value = mock_provider
            yield mock_provider
            
    @pytest.fixture
    def mock_trace(self):
        """Mock the trace module."""
        with patch("app.middleware.tracing.trace") as mock_trace:
            yield mock_trace
            
    @pytest.fixture
    def mock_batch_processor(self):
        """Mock the BatchSpanProcessor."""
        with patch("app.middleware.tracing.BatchSpanProcessor") as mock_batch:
            yield mock_batch
            
    @pytest.fixture
    def mock_jaeger_exporter(self):
        """Mock the JaegerExporter."""
        with patch("app.middleware.tracing.JaegerExporter") as mock_exporter_class:
            mock_exporter = MagicMock()
            mock_exporter_class.return_value = mock_exporter
            yield mock_exporter
            
    @pytest.fixture
    def mock_fastapi_instrumentor(self):
        """Mock the FastAPIInstrumentor."""
        with patch("app.middleware.tracing.FastAPIInstrumentor") as mock_instrumentor:
            yield mock_instrumentor

    def test_setup_tracing_default_config(
        self, 
        app, 
        mock_tracer_provider, 
        mock_trace, 
        mock_batch_processor, 
        mock_jaeger_exporter, 
        mock_fastapi_instrumentor
    ):
        """Test setup_tracing with default configuration."""
        # Call setup_tracing
        setup_tracing(app)
        
        # Check tracer provider was set up correctly
        mock_trace.set_tracer_provider.assert_called_once_with(mock_tracer_provider)
        
        # Check Jaeger exporter was created with default values
        from app.middleware.tracing import JaegerExporter
        JaegerExporter.assert_called_once_with(
            agent_host_name="localhost",
            agent_port=6831,
        )
        
        # Check batch processor was added
        mock_tracer_provider.add_span_processor.assert_called_once()
        args = mock_tracer_provider.add_span_processor.call_args[0]
        assert len(args) == 1
        assert isinstance(args[0], MagicMock)  # The mock batch processor
        
        # Check FastAPI instrumentation
        mock_fastapi_instrumentor.instrument_app.assert_called_once()
        kwargs = mock_fastapi_instrumentor.instrument_app.call_args[1]
        assert kwargs["excluded_urls"] == ["/metrics", "/health"]
        assert kwargs["tracer_provider"] == mock_tracer_provider

    def test_setup_tracing_custom_config(
        self, 
        app, 
        mock_tracer_provider, 
        mock_trace, 
        mock_batch_processor, 
        mock_jaeger_exporter, 
        mock_fastapi_instrumentor
    ):
        """Test setup_tracing with custom configuration."""
        # Set environment variables
        with patch.dict(os.environ, {
            "JAEGER_HOST": "jaeger-host",
            "JAEGER_PORT": "6832",
            "OTEL_SAMPLING_RATIO": "0.5",
            "ENVIRONMENT": "testing"
        }):
            # Call setup_tracing with custom params
            custom_service_name = "test-service"
            custom_excluded_endpoints = ["/custom", "/excluded"]
            setup_tracing(app, custom_service_name, custom_excluded_endpoints)
            
            # Check Jaeger exporter was created with custom values
            from app.middleware.tracing import JaegerExporter
            JaegerExporter.assert_called_once_with(
                agent_host_name="jaeger-host",
                agent_port=6832,
            )
            
            # Check FastAPI instrumentation with custom values
            mock_fastapi_instrumentor.instrument_app.assert_called_once()
            kwargs = mock_fastapi_instrumentor.instrument_app.call_args[1]
            assert kwargs["excluded_urls"] == custom_excluded_endpoints
            assert kwargs["tracer_provider"] == mock_tracer_provider

    def test_instrumentor_configuration(self, app):
        """Test that FastAPIInstrumentor is configured properly."""
        # Mock the instrumentor to capture its configuration
        mock_instrumentor = MagicMock()
        
        with patch("app.middleware.tracing.FastAPIInstrumentor.instrument_app", mock_instrumentor):
            # Call setup_tracing
            setup_tracing(app)
            
            # Check that the instrumentor was called
            assert mock_instrumentor.called
            
            # Check excluded URLs
            assert "/metrics" in mock_instrumentor.call_args[1]["excluded_urls"]
            assert "/health" in mock_instrumentor.call_args[1]["excluded_urls"] 