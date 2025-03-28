from fastapi import APIRouter, HTTPException, Request
from app.middleware.metrics import record_db_operation_duration, record_external_api_metrics
import httpx
import asyncio
import random
import time
from app.core.logging_config import get_logger, bind_request_context, get_request_id

router = APIRouter(prefix="/demo", tags=["demo"])
logger = get_logger("app.demo")

@router.get("/fast")
async def fast_endpoint():
    """Fast API response."""
    return {"message": "This is a fast endpoint"}

@router.get("/slow")
async def slow_endpoint():
    """Slow API response with random delay."""
    delay = random.uniform(0.5, 3.0)
    await asyncio.sleep(delay)
    return {"message": f"Slow response after {delay:.2f} seconds"}

@router.get("/random")
async def get_random():
    """Return a random number."""
    request_id = get_request_id()
    logger = bind_request_context(get_logger("app.demo"), request_id)
    
    logger.info("Generating random number", request_id=request_id)
    value = random.randint(1, 100)
    logger.info("Random number generated", value=value, request_id=request_id)
    
    return {"value": value}

@router.get("/metrics")
async def get_metrics():
    """Get some fake metrics data."""
    request_id = get_request_id()
    logger = bind_request_context(get_logger("app.demo"), request_id)
    
    logger.info("Collecting metrics", request_id=request_id)
    metrics = {
        "cpu_usage": random.uniform(0, 100),
        "memory_usage": random.uniform(0, 100),
        "active_users": random.randint(1, 1000)
    }
    logger.info("Metrics collected", metrics=metrics, request_id=request_id)
    
    return metrics

@router.post("/echo")
async def echo(payload: dict):
    """Echo back the JSON payload."""
    request_id = get_request_id()
    logger = bind_request_context(get_logger("app.demo"), request_id)
    
    logger.info("Received echo request", request_id=request_id)
    logger.info("Echo payload", payload=payload, request_id=request_id)
    return payload

@router.post("/data-echo")
async def data_echo():
    """Echo back a simple fixed response."""
    request_id = get_request_id()
    logger = bind_request_context(get_logger("app.demo"), request_id)
    
    logger.info("Received data-echo request", request_id=request_id)
    
    # Return a fixed response that doesn't require parsing request body
    return {
        "message": "This is a test echo response",
        "timestamp": time.time(),
        "status": "success"
    }

@router.get("/external/{error}")
@router.post("/external/{error}")
async def external_api_error(error: bool = False):
    """
    Simulates an external API call that might fail
    """
    # Record the duration of the external API call using our metrics middleware
    with record_external_api_metrics("demo_external_api"):
        if error:
            # Simulate a failed external API call
            try:
                async with httpx.AsyncClient() as client:
                    # Try to call a non-existent service
                    await client.get("http://non-existent-service", timeout=1)
            except Exception as e:
                raise HTTPException(
                    status_code=502,
                    detail=f"External service call failed: {str(e)}"
                )

@router.get("/simple-error")
async def simple_error(force_error: bool = False):
    """Endpoint that may generate errors."""
    request_id = get_request_id()
    logger = bind_request_context(get_logger("app.demo"), request_id)
    
    logger.info("Received error-prone request", force_error=force_error, request_id=request_id)
    
    if force_error:
        logger.error("Forced error triggered", request_id=request_id)
        raise HTTPException(status_code=500, detail="Forced error")
    
    # Randomly generate an error
    if random.random() < 0.2:
        logger.error("Random error occurred", request_id=request_id)
        raise HTTPException(status_code=500, detail="Random error occurred")
    
    logger.info("No error occurred", request_id=request_id)
    return {"status": "ok"} 