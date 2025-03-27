"""Main application module for the API Observability Platform."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
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
    
    # Configure CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, replace with specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
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
