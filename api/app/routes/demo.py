"""Demo API endpoints with various performance scenarios."""

import asyncio
import random
import time
from datetime import datetime, UTC
from typing import Dict, Any, Optional

import httpx
from fastapi import APIRouter, HTTPException, status, Query, Request
from pydantic import BaseModel
from opentelemetry import trace
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from app.utils.tracing import traced_http_request

# Create router
router = APIRouter(tags=["Demo"], prefix="/demo")

# Get tracer
tracer = trace.get_tracer(__name__)

# Create propagator for distributed tracing
propagator = TraceContextTextMapPropagator()
inject = propagator.inject  # For use in context propagation


class DemoResponse(BaseModel):
    """Base response model for demo endpoints."""
    
    message: str
    timestamp: datetime
    endpoint_type: str
    data: Dict[str, Any] = {}


class EchoRequest(BaseModel):
    """Request model for the echo endpoint."""
    message: str
    timestamp: Optional[float] = None
    data: Dict[str, Any] = {}


@router.post(
    "/echo",
    status_code=status.HTTP_200_OK,
    summary="Echo Endpoint",
    description="Echoes back the JSON payload sent to it.",
)
async def echo_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Echo endpoint that returns the JSON payload sent to it.
    
    Args:
        payload: The JSON payload to echo back
        
    Returns:
        Dict[str, Any]: The JSON payload sent to the endpoint
    """
    # Start a span for processing the echo request
    with tracer.start_as_current_span("echo_request_processing") as span:
        span.set_attribute("endpoint_type", "echo")
        span.set_attribute("business.importance", "low")
        
        # Add payload info to span
        if "message" in payload:
            span.set_attribute("echo.message", str(payload["message"]))
        if "timestamp" in payload:
            span.set_attribute("echo.timestamp", str(payload["timestamp"]))
        
        # Add an event to mark successful processing
        span.add_event("echo_processing_completed", {
            "timestamp": datetime.now(UTC).isoformat()
        })
        
        # Return the payload as-is
        return payload


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
    # Start a custom span for request processing
    with tracer.start_as_current_span("normal_request_processing") as span:
        # Add business context attributes
        span.set_attribute("business.endpoint_type", "normal")
        span.set_attribute("business.importance", "low")
        span.set_attribute("business.expected_latency_ms", 5)
        span.set_attribute("business.domain", "demo")
        
        # Add an event to mark processing start
        span.add_event("processing_started", {
            "timestamp": datetime.now(UTC).isoformat()
        })
        
        # Simulate minimal processing
        await asyncio.sleep(0.005)  # 5ms of processing time
        
        # Add an event to mark processing completion
        span.add_event("processing_completed", {
            "timestamp": datetime.now(UTC).isoformat(),
            "duration_ms": 5
        })
    
    return DemoResponse(
        message="This is a normal endpoint with standard response time",
        timestamp=datetime.now(UTC),
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
async def slow_endpoint(
    delay_min: Optional[float] = Query(2.0, description="Minimum delay in seconds"),
    delay_max: Optional[float] = Query(5.0, description="Maximum delay in seconds"),
    simulate_processing: Optional[bool] = Query(True, description="Simulate additional processing steps")
) -> DemoResponse:
    """
    Slow endpoint that simulates database delay.
    
    Args:
        delay_min: Minimum delay in seconds
        delay_max: Maximum delay in seconds
        simulate_processing: Whether to simulate additional processing steps
    
    Returns:
        DemoResponse: Delayed response
    """
    # Start a main operation span
    with tracer.start_as_current_span("slow_endpoint_operation") as main_span:
        # Add business context attributes to main span
        main_span.set_attribute("business.endpoint_type", "slow")
        main_span.set_attribute("business.importance", "medium")
        main_span.set_attribute("business.domain", "demo")
        
        # Track query parameters as span attributes
        main_span.set_attribute("request.param.delay_min", delay_min)
        main_span.set_attribute("request.param.delay_max", delay_max)
        main_span.set_attribute("request.param.simulate_processing", simulate_processing)
        
        # Add event for request received
        main_span.add_event("request_received", {
            "timestamp": datetime.now(UTC).isoformat(),
            "params": {
                "delay_min": delay_min,
                "delay_max": delay_max,
                "simulate_processing": simulate_processing
            }
        })
        
        # Start a new span for the database operation
        with tracer.start_as_current_span("database_query") as span:
            # Simulate database delay based on parameters
            delay_seconds = random.uniform(delay_min, delay_max)
            
            # Add database-specific attributes
            span.set_attribute("db.operation.type", "query")
            span.set_attribute("db.system", "postgres")
            span.set_attribute("db.name", "demo_db")
            span.set_attribute("db.statement", "SELECT * FROM large_table WHERE complex_condition = true")
            span.set_attribute("db.statement.params", f"delay_range={delay_min}-{delay_max}")
            span.set_attribute("db.execution_time_seconds", delay_seconds)
            
            # Add event for query start
            span.add_event("db_query_started", {
                "timestamp": datetime.now(UTC).isoformat(),
                "estimated_duration_seconds": delay_seconds
            })
            
            # Simulate the database delay
            await asyncio.sleep(delay_seconds)
            
            # Generate random result metrics
            records_fetched = random.randint(100, 1000)
            query_complexity = "high"
            
            # Add event for query completion
            span.add_event("db_query_completed", {
                "timestamp": datetime.now(UTC).isoformat(),
                "records_fetched": records_fetched,
                "query_complexity": query_complexity
            })
            
            # Update main span with result information
            main_span.set_attribute("business.records_processed", records_fetched)
        
        # Simulate additional processing if requested
        if simulate_processing:
            with tracer.start_as_current_span("post_processing") as proc_span:
                proc_span.set_attribute("processing.type", "data_transformation")
                proc_span.set_attribute("processing.complexity", "medium")
                
                # Add event for processing start
                proc_span.add_event("processing_started", {
                    "timestamp": datetime.now(UTC).isoformat()
                })
                
                # Simulate processing delay
                process_time = delay_seconds * 0.1  # 10% of the database time
                await asyncio.sleep(process_time)
                
                # Add event for processing completion
                proc_span.add_event("processing_completed", {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "duration_seconds": process_time
                })
                
                # Update main span attributes
                main_span.set_attribute("business.processing_time_seconds", process_time)
        
        # Add final event for request completion
        main_span.add_event("request_completed", {
            "timestamp": datetime.now(UTC).isoformat(),
            "total_duration_seconds": delay_seconds + (delay_seconds * 0.1 if simulate_processing else 0)
        })
    
    return DemoResponse(
        message="This is a slow endpoint simulating database delay",
        timestamp=datetime.now(UTC),
        endpoint_type="slow",
        data={
            "processing_time_ms": delay_seconds * 1000,
            "simulated_component": "database",
            "records_processed": records_fetched if simulate_processing else None,
        },
    )


@router.get(
    "/error-prone",
    response_model=DemoResponse,
    status_code=status.HTTP_200_OK,
    summary="Error-Prone Endpoint",
    description="An error-prone endpoint that randomly returns 500 errors (30% of requests).",
)
async def error_prone_endpoint(
    error_probability: Optional[float] = Query(0.3, description="Probability of error (0.0-1.0)"),
    error_type: Optional[str] = Query("server", description="Type of error to simulate (server, timeout, validation)")
) -> DemoResponse:
    """
    Error-prone endpoint that randomly returns server errors.
    
    Args:
        error_probability: Probability of error (0.0-1.0)
        error_type: Type of error to simulate
    
    Returns:
        DemoResponse: Response or error
        
    Raises:
        HTTPException: Random server error
    """
    # Start the main operation span
    with tracer.start_as_current_span("error_prone_operation") as span:
        # Add business context attributes
        span.set_attribute("business.endpoint_type", "error-prone")
        span.set_attribute("business.importance", "high")
        span.set_attribute("business.domain", "demo")
        
        # Track error configuration as span attributes
        span.set_attribute("error.probability", error_probability)
        span.set_attribute("error.type", error_type)
        span.set_attribute("operation.type", "risky_operation")
        
        # Add event for operation start
        span.add_event("operation_started", {
            "timestamp": datetime.now(UTC).isoformat(),
            "configuration": {
                "error_probability": error_probability,
                "error_type": error_type
            }
        })
        
        # Simulate processing
        await asyncio.sleep(0.1)
        
        # Determine if an error should occur
        should_error = random.random() < error_probability
        
        if should_error:
            # Record pre-error state
            span.add_event("error_condition_detected", {
                "timestamp": datetime.now(UTC).isoformat(),
                "random_value": random.random(),
                "threshold": error_probability
            })
            
            # Create error details based on error type
            if error_type == "timeout":
                error_msg = "Operation timed out"
                status_code = status.HTTP_504_GATEWAY_TIMEOUT
                exception_type = "TimeoutError"
            elif error_type == "validation":
                error_msg = "Validation error in request"
                status_code = status.HTTP_400_BAD_REQUEST
                exception_type = "ValidationError"
            else:  # Default to server error
                error_msg = "Random server error occurred"
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                exception_type = "ServerError"
            
            # Create a custom exception for better tracing
            error = Exception(f"{exception_type}: {error_msg}")
            
            # Record detailed error information in the span
            span.record_exception(error)
            span.set_status(trace.Status(trace.StatusCode.ERROR, error_msg))
            
            # Add error attributes for better filtering
            span.set_attribute("error.type", exception_type)
            span.set_attribute("error.message", error_msg)
            span.set_attribute("error.status_code", status_code)
            
            # Add a detailed error event
            span.add_event("error_occurred", {
                "timestamp": datetime.now(UTC).isoformat(),
                "error_type": exception_type,
                "error_message": error_msg,
                "status_code": status_code
            })
            
            # Raise the appropriate HTTP exception
            raise HTTPException(
                status_code=status_code,
                detail=error_msg,
            )
        
        # Operation was successful
        span.set_status(trace.Status(trace.StatusCode.OK))
        span.add_event("operation_completed", {
            "timestamp": datetime.now(UTC).isoformat(),
            "result": "success"
        })
    
    return DemoResponse(
        message="This is an error-prone endpoint that successfully responded",
        timestamp=datetime.now(UTC),
        endpoint_type="error-prone",
        data={
            "error_probability": error_probability,
            "error_type": error_type,
            "result": "success"
        },
    )


@router.get(
    "/external/{use_traced_client}",
    response_model=DemoResponse,
    status_code=status.HTTP_200_OK,
    summary="External-Dependent Endpoint",
    description="An endpoint that makes calls to an external service (httpbin).",
)
async def external_dependent_endpoint(
    use_traced_client: bool,
    service_url: Optional[str] = Query("https://httpbin.org/get", description="URL of the external service"),
    timeout_seconds: Optional[float] = Query(10.0, description="Timeout for external request in seconds"),
    add_headers: Optional[bool] = Query(True, description="Add custom headers for context propagation")
) -> DemoResponse:
    """
    External-dependent endpoint that calls an external service.
    
    Args:
        use_traced_client: Whether to use the traced HTTP client
        service_url: URL of the external service
        timeout_seconds: Timeout for external request in seconds
        add_headers: Add custom headers for context propagation
    
    Returns:
        DemoResponse: Response with external data
        
    Raises:
        HTTPException: If external service call fails
    """
    # Start the main operation span
    with tracer.start_as_current_span("external_service_operation") as main_span:
        # Add business context attributes
        main_span.set_attribute("business.endpoint_type", "external-dependent")
        main_span.set_attribute("business.importance", "high")
        main_span.set_attribute("business.domain", "demo")
        
        # Track configuration as span attributes
        main_span.set_attribute("external_service.url", service_url)
        main_span.set_attribute("external_service.timeout_seconds", timeout_seconds)
        main_span.set_attribute("request.use_traced_client", use_traced_client)
        main_span.set_attribute("request.add_headers", add_headers)
        
        # Add event for operation start
        main_span.add_event("external_operation_started", {
            "timestamp": datetime.now(UTC).isoformat(),
            "configuration": {
                "service_url": service_url,
                "timeout_seconds": timeout_seconds,
                "use_traced_client": use_traced_client,
                "add_headers": add_headers
            }
        })
        
        # Prepare for the external service request
        start_time = datetime.now(UTC)
        
        # Create a nested span for the external service request
        with tracer.start_as_current_span("external_service_request") as span:
            # Add detailed external service information
            span.set_attribute("external_service.name", service_url.split("//")[1].split("/")[0])
            span.set_attribute("external_service.url", service_url)
            span.set_attribute("external_service.timeout", timeout_seconds)
            span.set_attribute("external_service.protocol", service_url.split(":")[0])
            
            # Create custom headers for context propagation if requested
            custom_headers = {}
            if add_headers:
                # Add trace context headers
                inject(custom_headers)
                
                # Add business context headers
                custom_headers["X-Business-Domain"] = "demo"
                custom_headers["X-Request-Source"] = "api-service"
            
            # Add event for request preparation
            span.add_event("external_request_prepared", {
                "timestamp": datetime.now(UTC).isoformat(),
                "headers": str(custom_headers)
            })
            
            try:
                if use_traced_client:
                    # Use our traced HTTP client with span attributes
                    span.add_event("using_traced_client", {
                        "timestamp": datetime.now(UTC).isoformat()
                    })
                    
                    # Add detailed business attributes for the traced request
                    business_attributes = {
                        "business.importance": "high",
                        "business.transaction_type": "external_api_call",
                        "business.service_name": service_url.split("//")[1].split("/")[0],
                        "business.timeout_configured": timeout_seconds
                    }
                    
                    # Make the request using traced client
                    response = await traced_http_request(
                        url=service_url,
                        method="GET",
                        headers=custom_headers,
                        timeout=timeout_seconds,
                        span_name="external_http_request",
                        span_attributes=business_attributes
                    )
                    response_data = response.json()
                    
                else:
                    # Use the regular HTTP client but still maintain some tracing
                    span.add_event("using_standard_client", {
                        "timestamp": datetime.now(UTC).isoformat()
                    })
                    
                    # Create sub-span for the regular client request
                    with tracer.start_as_current_span("http_client_request") as client_span:
                        client_span.set_attribute("http.url", service_url)
                        client_span.set_attribute("http.method", "GET")
                        client_span.set_attribute("http.timeout", timeout_seconds)
                        
                        # Make the request with regular client
                        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                            response = await client.get(service_url, headers=custom_headers)
                            response.raise_for_status()
                            response_data = response.json()
                
                # Calculate response time
                end_time = datetime.now(UTC)
                processing_time_ms = (end_time - start_time).total_seconds() * 1000
                
                # Add response attributes to the request span
                span.set_attribute("external_service.response_time_ms", processing_time_ms)
                span.set_attribute("external_service.response_size_bytes", len(response.content))
                span.set_attribute("external_service.status_code", response.status_code)
                
                # Add successful response event
                span.add_event("external_service_response_received", {
                    "timestamp": end_time.isoformat(),
                    "status_code": response.status_code,
                    "content_length": len(response.content),
                    "processing_time_ms": processing_time_ms
                })
                
                # Update main span with success information
                main_span.set_attribute("external_service.success", True)
                main_span.set_attribute("external_service.response_time_ms", processing_time_ms)
                
                # Add completion event to main span
                main_span.add_event("external_operation_completed", {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "success": True,
                    "total_duration_ms": processing_time_ms
                })
                
                return DemoResponse(
                    message="Successfully called external service",
                    timestamp=datetime.now(UTC),
                    endpoint_type="external-dependent",
                    data={
                        "external_service": service_url.split("//")[1].split("/")[0],
                        "processing_time_ms": processing_time_ms,
                        "external_data": response_data,
                        "status_code": response.status_code
                    },
                )
                
            except httpx.TimeoutException as e:
                # Handle timeout error with detailed tracing
                end_time = datetime.now(UTC)
                error_time_ms = (end_time - start_time).total_seconds() * 1000
                
                # Record exception in span
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, "Timeout"))
                span.set_attribute("error.type", "timeout")
                span.set_attribute("error.timeout_seconds", timeout_seconds)
                span.set_attribute("error.duration_ms", error_time_ms)
                
                # Add error event with details
                span.add_event("external_service_timeout", {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "timeout_setting_seconds": timeout_seconds,
                    "elapsed_ms": error_time_ms
                })
                
                # Update main span with error information
                main_span.set_attribute("external_service.success", False)
                main_span.set_attribute("error.type", "timeout")
                main_span.set_attribute("error.message", str(e))
                
                # Add error completion event to main span
                main_span.add_event("external_operation_error", {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "error_type": "timeout",
                    "error_message": str(e),
                    "total_duration_ms": error_time_ms
                })
                
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="Timeout while calling external service",
                )
                
            except httpx.HTTPStatusError as e:
                # Handle HTTP error status with detailed tracing
                end_time = datetime.now(UTC)
                error_time_ms = (end_time - start_time).total_seconds() * 1000
                
                # Record exception in span
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, f"HTTP error: {e.response.status_code}"))
                span.set_attribute("error.type", "http_status")
                span.set_attribute("error.status_code", e.response.status_code)
                span.set_attribute("error.duration_ms", error_time_ms)
                
                # Add error event with details
                span.add_event("external_service_http_error", {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "status_code": e.response.status_code,
                    "response_text": e.response.text,
                    "elapsed_ms": error_time_ms
                })
                
                # Update main span with error information
                main_span.set_attribute("external_service.success", False)
                main_span.set_attribute("error.type", "http_status")
                main_span.set_attribute("error.status_code", e.response.status_code)
                main_span.set_attribute("error.message", str(e))
                
                # Add error completion event to main span
                main_span.add_event("external_operation_error", {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "error_type": "http_status",
                    "status_code": e.response.status_code,
                    "error_message": str(e),
                    "total_duration_ms": error_time_ms
                })
                
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"External service error: {str(e)}",
                )
                
            except Exception as e:
                # Handle unexpected errors with detailed tracing
                end_time = datetime.now(UTC)
                error_time_ms = (end_time - start_time).total_seconds() * 1000
                
                # Record exception in span
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                span.set_attribute("error.type", "unexpected")
                span.set_attribute("error.duration_ms", error_time_ms)
                
                # Add error event with details
                span.add_event("external_service_unexpected_error", {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "error_type": type(e).__name__,
                    "elapsed_ms": error_time_ms
                })
                
                # Update main span with error information
                main_span.set_attribute("external_service.success", False)
                main_span.set_attribute("error.type", "unexpected")
                main_span.set_attribute("error.class", type(e).__name__)
                main_span.set_attribute("error.message", str(e))
                
                # Add error completion event to main span
                main_span.add_event("external_operation_error", {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "error_type": "unexpected",
                    "error_class": type(e).__name__,
                    "error_message": str(e),
                    "total_duration_ms": error_time_ms
                })
                
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Unexpected error while calling external service: {str(e)}",
                )


@router.get(
    "/trace",
    response_model=DemoResponse,
    status_code=status.HTTP_200_OK,
    summary="Trace Demo Endpoint",
    description="A demo endpoint to showcase distributed tracing with multiple spans.",
)
async def trace_demo_endpoint(
    sleep_time: Optional[float] = Query(0.5, description="Time to sleep in seconds"),
    add_child_spans: Optional[int] = Query(2, description="Number of child spans to add"),
    add_events: Optional[bool] = Query(True, description="Whether to add span events")
) -> DemoResponse:
    """
    Tracing demo endpoint with multiple spans and events.
    
    Args:
        sleep_time: Time to sleep in seconds
        add_child_spans: Number of child spans to add
        add_events: Whether to add span events
    
    Returns:
        DemoResponse: Response with trace details
    """
    start_time = time.time()
    
    # Start parent span
    with tracer.start_as_current_span("trace_demo_operation") as parent_span:
        parent_span.set_attribute("operation.total_child_spans", add_child_spans)
        parent_span.set_attribute("operation.sleep_time", sleep_time)
        parent_span.set_attribute("business.value", "high")
        
        if add_events:
            parent_span.add_event("operation_started", {
                "timestamp": datetime.now(UTC).isoformat(),
                "parameters": {
                    "sleep_time": sleep_time,
                    "add_child_spans": add_child_spans,
                    "add_events": add_events
                }
            })
        
        # Create child spans
        for i in range(add_child_spans):
            with tracer.start_as_current_span(f"child_operation_{i+1}") as child_span:
                child_span.set_attribute("child.index", i)
                child_span.set_attribute("child.sleep_time", sleep_time / (i + 1))
                
                # Simulate some work
                await asyncio.sleep(sleep_time / (i + 1))
                
                if add_events:
                    child_span.add_event(f"child_{i+1}_operation_completed", {
                        "duration_ms": (sleep_time / (i + 1)) * 1000
                    })
        
        # One more async operation
        with tracer.start_as_current_span("async_operation") as async_span:
            async_span.set_attribute("async.type", "background_task")
            await asyncio.sleep(sleep_time / 2)
            async_span.add_event("async_operation_completed")
        
        end_time = time.time()
        total_duration = (end_time - start_time) * 1000
        
        if add_events:
            parent_span.add_event("operation_completed", {
                "total_duration_ms": total_duration
            })
    
    return DemoResponse(
        message="Trace demo completed successfully",
        timestamp=datetime.now(UTC),
        endpoint_type="trace-demo",
        data={
            "processing_time_ms": total_duration,
            "child_spans_created": add_child_spans,
            "events_added": add_events
        },
    )


@router.get(
    "/random",
    response_model=DemoResponse,
    status_code=status.HTTP_200_OK,
    summary="Random Data Endpoint",
    description="Returns random data for testing.",
)
async def random_endpoint() -> DemoResponse:
    """
    Random data endpoint for testing.
    
    Returns:
        DemoResponse: Random data response
    """
    # Create a span for tracking
    with tracer.start_as_current_span("random_data_generation") as span:
        span.set_attribute("endpoint_type", "random")
        
        # Generate random data
        random_data = {
            "random_number": random.randint(1, 1000),
            "random_float": random.random(),
            "random_bool": random.choice([True, False]),
            "timestamp_ms": time.time() * 1000
        }
        
        # Add random data to span
        for key, value in random_data.items():
            span.set_attribute(f"random.{key}", str(value))
    
    return DemoResponse(
        message="Random data generated successfully",
        timestamp=datetime.now(UTC),
        endpoint_type="random",
        data=random_data,
    )


@router.get(
    "/metrics",
    response_model=DemoResponse,
    status_code=status.HTTP_200_OK,
    summary="Metrics Demo Endpoint",
    description="Returns some mock metrics for demonstration.",
)
async def metrics_endpoint() -> DemoResponse:
    """
    Metrics demo endpoint.
    
    Returns:
        DemoResponse: Mock metrics data
    """
    # Create a span for tracking
    with tracer.start_as_current_span("metrics_collection") as span:
        span.set_attribute("endpoint_type", "metrics")
        
        # Generate mock metrics
        metrics_data = {
            "system": {
                "cpu_usage": random.uniform(0.1, 0.9),
                "memory_usage": random.uniform(0.2, 0.8),
                "disk_usage": random.uniform(0.3, 0.7),
            },
            "application": {
                "requests_per_second": random.randint(10, 100),
                "average_response_time_ms": random.randint(50, 500),
                "error_rate": random.uniform(0.01, 0.05),
            },
            "database": {
                "connections": random.randint(5, 20),
                "queries_per_second": random.randint(5, 50),
                "average_query_time_ms": random.randint(10, 100),
            }
        }
        
        # Add an event for metrics collection
        span.add_event("metrics_collected", {
            "timestamp": datetime.now(UTC).isoformat(),
        })
    
    return DemoResponse(
        message="System metrics collected",
        timestamp=datetime.now(UTC),
        endpoint_type="metrics",
        data=metrics_data,
    )


@router.post(
    "/data-echo",
    response_model=DemoResponse,
    status_code=status.HTTP_200_OK,
    summary="Data Echo Endpoint",
    description="Echoes back the data received with a timestamp.",
)
async def data_echo_endpoint(request: Request) -> DemoResponse:
    """
    Data echo endpoint that returns the data received with a timestamp.
    
    Args:
        request: The incoming request
        
    Returns:
        DemoResponse: Echo response with timestamp
    """
    # Create a span for tracking
    with tracer.start_as_current_span("data_echo_processing") as span:
        span.set_attribute("endpoint_type", "data_echo")
        
        # Try to parse the request body if available
        try:
            body = await request.json()
        except:
            body = {}
        
        # Create response data
        echo_data = {
            "received_data": body,
            "received_at": datetime.now(UTC).isoformat(),
            "headers": dict(request.headers)
        }
    
    return DemoResponse(
        message="Data echoed successfully",
        timestamp=datetime.now(UTC),
        endpoint_type="data_echo",
        data=echo_data,
    ) 