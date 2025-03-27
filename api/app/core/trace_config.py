"""Tracing configuration for the API Observability Platform."""

import os
from typing import Dict, Optional, Any

# Default sampling ratio (0.0 to 1.0)
DEFAULT_SAMPLING_RATIO = 1.0

# Trace configuration
TRACE_CONFIG = {
    # Enable or disable tracing
    "enabled": os.getenv("OTEL_TRACES_ENABLED", "false").lower() in ("true", "1", "yes"),
    
    # Sampling configuration
    "sampling": {
        # Sampling ratio (0.0 to 1.0)
        "ratio": float(os.getenv("OTEL_SAMPLING_RATIO", DEFAULT_SAMPLING_RATIO)),
        
        # Parent-based sampling configuration
        "parent_based": True,
        
        # Endpoints with custom sampling ratios
        "endpoint_specific": {
            # Example: Sample 20% of requests to the slow endpoint
            "/demo/slow": 0.2,
            
            # Example: Sample all requests to the trace endpoint
            "/demo/trace": 1.0,
            
            # Example: Sample 50% of requests to the external endpoint
            "/demo/external": 0.5,
        }
    },
    
    # Exporter configuration
    "exporter": {
        "type": "jaeger",
        "host": os.getenv("JAEGER_HOST", "localhost"),
        "port": int(os.getenv("JAEGER_PORT", 6831)),
        "protocol": os.getenv("JAEGER_PROTOCOL", "thrift"),
    },
    
    # Resource attributes
    "resource_attributes": {
        "service.name": os.getenv("SERVICE_NAME", "api-service"),
        "service.version": os.getenv("SERVICE_VERSION", "1.0.0"),
        "deployment.environment": os.getenv("ENVIRONMENT", "development"),
    },
    
    # Performance settings
    "performance": {
        # Maximum number of spans to buffer before export
        "max_queue_size": int(os.getenv("OTEL_BSP_MAX_QUEUE_SIZE", 2048)),
        
        # Maximum batch size for export
        "max_export_batch_size": int(os.getenv("OTEL_BSP_MAX_EXPORT_BATCH_SIZE", 512)),
        
        # Export interval in seconds
        "export_interval_ms": int(os.getenv("OTEL_BSP_SCHEDULE_DELAY", 5000)),
    },
    
    # Excluded endpoints from tracing
    "excluded_endpoints": [
        "/metrics",
        "/health",
    ],
}


def get_trace_config() -> Dict[str, Any]:
    """Get the tracing configuration."""
    return TRACE_CONFIG


def get_sampling_ratio_for_endpoint(endpoint_path: str) -> float:
    """
    Get the sampling ratio for a specific endpoint.
    
    Args:
        endpoint_path: The endpoint path
        
    Returns:
        float: The sampling ratio (0.0 to 1.0)
    """
    endpoint_specific = TRACE_CONFIG["sampling"]["endpoint_specific"]
    
    # Check for exact match
    if endpoint_path in endpoint_specific:
        return endpoint_specific[endpoint_path]
    
    # Check for prefix matches
    for path, ratio in endpoint_specific.items():
        if endpoint_path.startswith(path):
            return ratio
    
    # Default to global sampling ratio
    return TRACE_CONFIG["sampling"]["ratio"] 