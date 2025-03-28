"""
Basic flow scenario for load testing.
This simulates users accessing the normal endpoints of the application.
"""

import random
import time
from locust import HttpUser, task, between
from typing import Dict, Any


class BasicFlowUser(HttpUser):
    """
    User class simulating basic flow through the API.
    Focuses on the primary happy path without errors.
    """
    
    # Set scenario name for reporting
    scenario = "basic_flow"
    
    # Configure realistic wait times between requests (2-5 seconds)
    wait_time = between(2, 5)
    
    # Track user state
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_prefix = "/api/v1"
        self.user_id = random.randint(1000, 9999)
        self.session_data = {}
    
    def on_start(self):
        """
        Initialize user session.
        Called when a virtual user starts.
        """
        self.client.headers.update({"X-User-ID": str(self.user_id)})
        self.client.headers.update({"Content-Type": "application/json"})
        
        # Start with a health check
        with self.client.get(f"{self.api_prefix}/health", name="Health Check", catch_response=True) as response:
            if response.status_code == 200:
                self.session_data["health_check_passed"] = True
            else:
                self.session_data["health_check_passed"] = False
                response.failure(f"Health check failed with status code: {response.status_code}")
    
    @task(3)
    def get_normal_endpoint(self):
        """
        Access the normal endpoint.
        This is the most common task performed by users.
        """
        with self.client.get(
            f"{self.api_prefix}/demo/normal",
            name="Normal Endpoint",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response_data = response.json()
                self.session_data["last_normal_response"] = response_data
                
                # Record custom measurement
                response_time_ms = response.elapsed.total_seconds() * 1000
                
                # Log additional data if needed
                if response_time_ms > 100:  # If response time is unexpectedly high
                    response.failure(f"Response time too high: {response_time_ms}ms")
            else:
                response.failure(f"Normal endpoint failed with status {response.status_code}")
    
    @task(1)
    def echo_data(self):
        """
        Send and receive data through the echo endpoint.
        """
        payload = {
            "message": f"Test message from user {self.user_id}",
            "timestamp": time.time(),
            "data": {
                "user_agent": self.client.headers.get("User-Agent", ""),
                "test_run": True
            }
        }
        
        with self.client.post(
            f"{self.api_prefix}/demo/echo",
            json=payload,
            name="Echo Endpoint",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response_data = response.json()
                
                # Verify the echoed data matches what we sent
                if response_data.get("message") != payload["message"]:
                    response.failure("Echo response did not match sent data")
            else:
                response.failure(f"Echo endpoint failed with status {response.status_code}")
    
    @task(1)
    def slow_endpoint_with_normal_delay(self):
        """
        Access the slow endpoint with reasonable delay parameters.
        """
        params = {
            "delay_min": 1.0,  # Lower than default for testing
            "delay_max": 2.0,  # Lower than default for testing
            "simulate_processing": True
        }
        
        with self.client.get(
            f"{self.api_prefix}/demo/slow",
            params=params,
            name="Slow Endpoint (Normal Delay)",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response_data = response.json()
                self.session_data["last_slow_response"] = response_data
            else:
                response.failure(f"Slow endpoint failed with status {response.status_code}")
    
    def on_stop(self):
        """
        Clean up user session.
        Called when a virtual user stops.
        """
        # Perform any cleanup if needed
        self.session_data.clear() 