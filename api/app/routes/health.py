"""Health check endpoints for the API."""

from fastapi import APIRouter, status
from pydantic import BaseModel
from datetime import datetime

# Create router
router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    
    status: str
    version: str
    timestamp: datetime


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Endpoint to check if the API is running correctly.",
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns:
        HealthResponse: Health status information
    """
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        timestamp=datetime.utcnow(),
    )
