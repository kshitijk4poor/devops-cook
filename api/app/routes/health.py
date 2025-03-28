"""Health check endpoints for the API."""

from fastapi import APIRouter, status
from pydantic import BaseModel
from datetime import datetime, UTC
import platform
import os

# Create router
router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    
    status: str
    version: str
    timestamp: datetime
    hostname: str
    environment: str


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Endpoint to check if the API is running correctly.",
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint that returns basic system information.
    
    Returns:
        HealthResponse: Health status and system information
    """
    return HealthResponse(
        status="healthy",
        version=os.getenv("VERSION", "1.0.0"),
        timestamp=datetime.now(UTC),
        hostname=platform.node(),
        environment=os.getenv("ENVIRONMENT", "development")
    )
