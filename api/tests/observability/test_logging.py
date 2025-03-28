import json
import pytest
from fastapi.testclient import TestClient
import structlog
import logging
from app.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_logging(caplog):
    """Configure structlog for testing."""
    # Set up caplog to capture structlog output
    caplog.set_level(logging.INFO)
    
    # Configure structlog to output through standard logging
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

def test_request_logging(caplog):
    """Test that requests are properly logged with structured data."""
    response = client.get("/health")
    assert response.status_code == 200
    
    # Parse JSON logs from stderr output
    logs = []
    for record in caplog.records:
        try:
            if hasattr(record, 'message'):
                log_data = json.loads(record.message)
                logs.append(log_data)
        except (json.JSONDecodeError, AttributeError):
            continue
    
    assert len(logs) >= 2  # Should have start and end logs
    
    # Find request logs
    request_logs = [log for log in logs if 'request_id' in log]
    assert len(request_logs) >= 2
    
    # Check request started log
    start_log = request_logs[0]
    assert start_log['event'] == 'request_started'
    assert 'request_id' in start_log
    assert 'method' in start_log
    assert 'url' in start_log
    
    # Check request completed log
    end_log = request_logs[-1]
    assert end_log['event'] == 'request_completed'
    assert 'status_code' in end_log
    assert 'duration' in end_log
    assert end_log['status_code'] == 200

def test_error_logging(caplog):
    """Test that errors are properly logged with stack traces."""
    try:
        response = client.get("/demo/simple-error", params={"force_error": True})
    except Exception:
        pass  # We expect this to fail

    # Check that error was logged
    error_logs = [record for record in caplog.records 
                 if record.name.startswith('app.') and record.levelname == 'ERROR']
    assert len(error_logs) > 0, "No error logs found"
    
    # Check error log content
    error_log = error_logs[0]
    log_data = json.loads(error_log.message)
    assert log_data['event'] == 'request_failed'
    assert 'duration' in log_data
    assert 'exception' in log_data
    assert isinstance(log_data['exception'], list)
    assert len(log_data['exception']) > 0
    assert 'exc_type' in log_data['exception'][0]
    assert 'exc_value' in log_data['exception'][0]
    assert 'frames' in log_data['exception'][0]

def test_sensitive_data_filtering(caplog):
    """Test that sensitive data is properly filtered from logs."""
    sensitive_data = {
        "username": "test_user",
        "password": "secret123",
        "api_key": "very-secret-key",
        "normal_field": "visible-data"
    }

    try:
        response = client.post("/demo/echo", json=sensitive_data)
    except Exception:
        pass  # We don't care about the response, only the logs

    # Check that sensitive data is filtered from logs
    app_logs = [record for record in caplog.records if record.name.startswith('app.')]
    assert len(app_logs) > 0, "No application logs found"
    
    for record in app_logs:
        log_message = record.message
        assert "secret123" not in log_message, "Password was not filtered from logs"
        assert "very-secret-key" not in log_message, "API key was not filtered from logs"
        assert "***REDACTED***" in log_message, "Sensitive data was not properly redacted"
        assert "visible-data" in log_message, "Normal data was incorrectly filtered"
        assert "test_user" in log_message, "Username was incorrectly filtered" 