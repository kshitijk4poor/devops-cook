"""Tests for the health check endpoint."""

from datetime import datetime, timedelta, UTC
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check(client):
    """
    Test that the health check endpoint returns a 200 response with the expected format.
    """
    response = client.get("/api/health")
    
    # Check response status
    assert response.status_code == 200
    
    # Check response body
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data
    assert "hostname" in data
    assert "environment" in data
    
    # Verify timestamp is recent
    timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
    assert (datetime.now(UTC) - timestamp).total_seconds() < 60  # Within the last minute
