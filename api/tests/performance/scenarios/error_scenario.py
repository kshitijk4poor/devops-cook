"""
Error scenario for load testing.
This simulates users accessing the error-prone endpoints of the application.
"""

import random
import time
from locust import HttpUser, task, between
from typing import Dict, Any


class ErrorScenarioUser(HttpUser):
    """
    User class simulating interactions with error-prone endpoints.
    Focuses on testing error handling and system resilience.
    """
    
    # Set scenario name for reporting
    scenario = "error_scenario"
    
    # Configure shorter wait times to increase error frequency (1-3 seconds)
    wait_time = between(1, 3)
    
    # Track user state
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_prefix = "/api/v1"
        self.user_id = random.randint(1000, 9999)
        self.session_data = {}
        self.error_types = ["server", "timeout", "validation"]
    
    def on_start(self):
        """
        Initialize user session.
        Called when a virtual user starts.
        """
        self.client.headers.update({"X-User-ID": str(self.user_id)})
        self.client.headers.update({"Content-Type": "application/json"})
        self.client.headers.update({"X-Test-Scenario": "error"})
    
    @task(5)  # Higher weight for the main error endpoint
    def access_error_prone_endpoint(self):
        """
        Access the error-prone endpoint with varying error probabilities.
        This is the main focus of this user type.
        """
        # Randomize error probability between 0.3 and 0.7
        error_probability = round(random.uniform(0.3, 0.7), 2)
        
        # Randomly select error type
        error_type = random.choice(self.error_types)
        
        params = {
            "error_probability": error_probability,
            "error_type": error_type
        }
        
        with self.client.get(
            f"{self.api_prefix}/demo/error-prone",
            params=params,
            name=f"Error-Prone ({error_type})",
            catch_response=True
        ) as response:
            # If we expect to get an error (based on error_probability)
            # and we actually got one (4xx or 5xx), mark it as success
            expected_error = random.random() < error_probability
            actual_error = response.status_code >= 400
            
            if expected_error and actual_error:
                # This is an expected error, so mark it as a success for the test
                response.success()
                self.session_data["last_error"] = {
                    "type": error_type,
                    "status_code": response.status_code,
                    "response": response.text
                }
            elif expected_error and not actual_error:
                # Expected an error but didn't get one
                response.failure(f"Expected {error_type} error but got success")
            elif not expected_error and actual_error:
                # Got an unexpected error
                response.failure(f"Got unexpected {error_type} error with status {response.status_code}")
            else:
                # No error expected, no error received - normal success
                response_data = response.json()
                self.session_data["last_success"] = response_data
    
    @task(2)
    def simulate_bad_request(self):
        """
        Send malformed data to the echo endpoint to test error handling.
        """
        # Intentionally malformed JSON (missing required fields)
        payload = {
            # Missing "message" field which may be required
            "timestamp": time.time(),
            "malformed": True
        }
        
        with self.client.post(
            f"{self.api_prefix}/demo/echo",
            json=payload,
            name="Echo Endpoint (Bad Request)",
            catch_response=True
        ) as response:
            # Check if API properly handles bad requests
            if 400 <= response.status_code < 500:
                # This is the expected behavior for bad requests
                response.success()
            elif response.status_code >= 500:
                # Server error is not expected for a bad request
                response.failure(f"Server error {response.status_code} for bad request test")
            else:
                # API should have rejected this request
                response.failure(f"API accepted malformed request with status {response.status_code}")
    
    @task(1)
    def request_with_high_timeout(self):
        """
        Access the slow endpoint with high delay parameters to test timeouts.
        """
        params = {
            "delay_min": 5.0,  # Higher than normal for testing timeouts
            "delay_max": 8.0,  # May exceed client timeout
            "simulate_processing": True
        }
        
        # Use a shorter timeout to increase chances of timeout error
        with self.client.get(
            f"{self.api_prefix}/demo/slow",
            params=params,
            name="Slow Endpoint (Timeout Test)",
            timeout=3.0,  # Shorter than the delay parameters
            catch_response=True
        ) as response:
            if hasattr(response, "exc") and response.exc:
                if "timeout" in str(response.exc).lower():
                    # This is an expected timeout, mark as success for the test
                    response.success()
                    self.session_data["timeout_occurred"] = True
                else:
                    # Other exception occurred
                    response.failure(f"Non-timeout exception: {response.exc}")
            else:
                # No timeout occurred (request completed)
                response.failure("Expected timeout did not occur")
    
    def on_stop(self):
        """
        Clean up user session.
        Called when a virtual user stops.
        """
        # Perform any cleanup if needed
        self.session_data.clear() 