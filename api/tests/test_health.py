"""Tests for the health check endpoint."""

from fastapi.testclient import TestClient
import pytest
from datetime import datetime

from app.main import app


client = TestClient(app)


def test_health_check():
    """Test that the health check endpoint returns the expected response."""
    response = client.get("/api/health")
    
    # Check status code
    assert response.status_code == 200
    
    # Check response data
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data
    
    # Optional: Verify timestamp is recent
    timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
    assert (datetime.utcnow() - timestamp).total_seconds() < 60  # Within the last minute
