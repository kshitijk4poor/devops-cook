"""Main application module for the API Observability Platform."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from app.core.config import settings
from app.middleware.logging import add_logging_middleware
from app.middleware.metrics import PrometheusMiddleware
from app.middleware.tracing import setup_tracing
from app.routes import health, demo


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured application instance
    """
    # Create FastAPI app
    application = FastAPI(
        title=settings.APP_NAME,
        description="API Observability Platform for monitoring and debugging APIs",
        version=settings.VERSION,
        debug=settings.DEBUG,
    )
    
    # Add logging middleware
    add_logging_middleware(application)
    
    # Add Prometheus middleware
    application.add_middleware(PrometheusMiddleware)
    
    # Mount Prometheus metrics endpoint
    metrics_app = make_asgi_app()
    application.mount("/metrics", metrics_app)
    
    # Configure CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, replace with specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Set up OpenTelemetry tracing if enabled
    if os.getenv("OTEL_TRACES_ENABLED", "false").lower() in ("true", "1", "yes"):
        setup_tracing(
            application,
            service_name=settings.APP_NAME,
            excluded_endpoints=["/metrics", "/health"]
        )
    
    # Include routers
    application.include_router(
        health.router,
        prefix=settings.API_PREFIX,
    )
    
    application.include_router(
        demo.router,
        prefix=settings.API_PREFIX,
    )
    
    return application


# Create app instance
app = create_application()
