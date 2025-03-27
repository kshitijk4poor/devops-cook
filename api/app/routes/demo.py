"""Demo API endpoints with various performance scenarios."""

import asyncio
import random
from datetime import datetime
from typing import Dict, Any

import httpx
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

# Create router
router = APIRouter(tags=["Demo"], prefix="/demo")


class DemoResponse(BaseModel):
    """Base response model for demo endpoints."""
    
    message: str
    timestamp: datetime
    endpoint_type: str
    data: Dict[str, Any] = {}


@router.get(
    "/normal",
    response_model=DemoResponse,
    status_code=status.HTTP_200_OK,
    summary="Normal Endpoint",
    description="A normal endpoint that returns quickly with standard response time.",
)
async def normal_endpoint() -> DemoResponse:
    """
    Normal endpoint with fast response time.
    
    Returns:
        DemoResponse: Standard response
    """
    return DemoResponse(
        message="This is a normal endpoint with standard response time",
        timestamp=datetime.utcnow(),
        endpoint_type="normal",
        data={"processing_time_ms": 5},
    )


@router.get(
    "/slow",
    response_model=DemoResponse,
    status_code=status.HTTP_200_OK,
    summary="Slow Endpoint",
    description="A slow endpoint that simulates database delay (2-5 seconds).",
)
async def slow_endpoint() -> DemoResponse:
    """
    Slow endpoint that simulates database delay.
    
    Returns:
        DemoResponse: Delayed response
    """
    # Simulate database delay (2-5 seconds)
    delay_seconds = random.uniform(2.0, 5.0)
    await asyncio.sleep(delay_seconds)
    
    return DemoResponse(
        message="This is a slow endpoint simulating database delay",
        timestamp=datetime.utcnow(),
        endpoint_type="slow",
        data={
            "processing_time_ms": delay_seconds * 1000,
            "simulated_component": "database",
        },
    )


@router.get(
    "/error-prone",
    response_model=DemoResponse,
    status_code=status.HTTP_200_OK,
    summary="Error-Prone Endpoint",
    description="An error-prone endpoint that randomly returns 500 errors (30% of requests).",
)
async def error_prone_endpoint() -> DemoResponse:
    """
    Error-prone endpoint that randomly returns server errors.
    
    Returns:
        DemoResponse: Response or error
        
    Raises:
        HTTPException: Random server error
    """
    # Randomly fail 30% of the time
    if random.random() < 0.3:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Random server error occurred",
        )
    
    return DemoResponse(
        message="This is an error-prone endpoint that successfully responded",
        timestamp=datetime.utcnow(),
        endpoint_type="error-prone",
        data={"error_probability": 0.3},
    )


@router.get(
    "/external",
    response_model=DemoResponse,
    status_code=status.HTTP_200_OK,
    summary="External-Dependent Endpoint",
    description="An endpoint that makes calls to an external service (httpbin).",
)
async def external_dependent_endpoint() -> DemoResponse:
    """
    External-dependent endpoint that calls an external service.
    
    Returns:
        DemoResponse: Response with external data
        
    Raises:
        HTTPException: If external service call fails
    """
    external_url = "https://httpbin.org/get"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            start_time = datetime.utcnow()
            response = await client.get(external_url)
            end_time = datetime.utcnow()
            
            response.raise_for_status()
            response_data = response.json()
            
            processing_time_ms = (end_time - start_time).total_seconds() * 1000
            
            return DemoResponse(
                message="Successfully called external service",
                timestamp=datetime.utcnow(),
                endpoint_type="external-dependent",
                data={
                    "external_service": "httpbin",
                    "processing_time_ms": processing_time_ms,
                    "external_data": response_data,
                },
            )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Timeout while calling external service",
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"External service error: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error while calling external service: {str(e)}",
        ) 