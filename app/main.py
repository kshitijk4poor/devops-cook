from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
from app.middleware.metrics import MetricsMiddleware
from app.middleware.logging import StructuredLoggingMiddleware
from app.core.logging_config import configure_standard_logging, configure_structlog
from app.routes import demo

# Configure logging
configure_standard_logging()
configure_structlog()

# Create FastAPI app
app = FastAPI(title="API Observability Demo")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add structured logging middleware
app.add_middleware(StructuredLoggingMiddleware)

# Add metrics middleware
app.add_middleware(MetricsMiddleware)

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include demo routes
app.include_router(demo.router)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"} 