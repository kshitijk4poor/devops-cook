"""
Mixed scenario for load testing.
This simulates realistic user traffic with a mix of different API calls.
"""

import random
import time
from locust import HttpUser, task, between, tag
from typing import Dict, Any, List
import logging


class MixedScenarioUser(HttpUser):
    """
    User class simulating realistic mixed traffic patterns.
    Provides the most realistic simulation of production traffic.
    """
    
    # Set scenario name for reporting
    scenario = "mixed_scenario"
    
    # Configure realistic wait times between requests (1-8 seconds)
    wait_time = between(1, 8)
    
    # Track user state
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_prefix = "/api/v1"
        self.user_id = random.randint(1000, 9999)
        self.session_data = {}
        self.request_count = 0
        self.error_probability = 0.1  # 10% chance of accessing error endpoints
        self.error_types = ["server", "timeout", "validation"]
    
    def on_start(self):
        """
        Initialize user session.
        Called when a virtual user starts.
        """
        self.session_data = {}
        self.task_count = 0
        self.start_time = time.time()
        
        # Configure scenario
        self.client.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "LoadTest/1.0"
        }
        
        self.client.headers.update({"X-User-ID": str(self.user_id)})
        self.client.headers.update({"X-Test-Scenario": "mixed"})
        
        # Start with a health check
        with self.client.get(f"{self.api_prefix}/health", name="Health Check", catch_response=True) as response:
            if response.status_code == 200:
                self.session_data["health_check_passed"] = True
            else:
                self.session_data["health_check_passed"] = False
                response.failure(f"Health check failed with status code: {response.status_code}")
    
    @tag("normal")
    @task(10)  # Higher weight for normal endpoint
    def get_normal_endpoint(self):
        """
        Access the normal endpoint.
        This is the most common task in production.
        """
        self.request_count += 1
        
        with self.client.get(
            f"{self.api_prefix}/demo/normal",
            name="Normal Endpoint",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response_data = response.json()
                self.session_data["last_normal_response"] = response_data
            else:
                response.failure(f"Normal endpoint failed with status {response.status_code}")
    
    @tag("data")
    @task(5)
    def echo_data(self):
        """
        Send and receive data through the echo endpoint.
        """
        self.request_count += 1
        
        # Create more realistic payload with varying data
        payload = {
            "message": f"Test message {self.request_count} from user {self.user_id}",
            "timestamp": time.time(),
            "data": {
                "user_agent": self.client.headers.get("User-Agent", ""),
                "session_id": f"test-session-{random.randint(1000, 9999)}",
                "request_id": f"req-{random.randint(10000, 99999)}",
                "metadata": {
                    "client_type": random.choice(["web", "mobile", "api"]),
                    "version": f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
                }
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
                
                # Basic validation
                if "message" not in response_data:
                    response.failure("Echo response missing message field")
            else:
                response.failure(f"Echo endpoint failed with status {response.status_code}")
    
    @tag("slow")
    @task(3)
    def slow_endpoint_request(self):
        """
        Access the slow endpoint with varying delay parameters.
        """
        self.request_count += 1
        
        # Vary the delay parameters to simulate different types of users/requests
        delay_min = random.uniform(0.5, 3.0)
        delay_max = delay_min + random.uniform(0.5, 2.0)
        
        params = {
            "delay_min": round(delay_min, 2),
            "delay_max": round(delay_max, 2),
            "simulate_processing": random.choice([True, False])
        }
        
        with self.client.get(
            f"{self.api_prefix}/demo/slow",
            params=params,
            name="Slow Endpoint (Variable)",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response_data = response.json()
                self.session_data["last_slow_response"] = response_data
            else:
                response.failure(f"Slow endpoint failed with status {response.status_code}")
    
    @tag("error")
    @task(2)
    def error_prone_request(self):
        """
        Occasionally access the error-prone endpoint.
        """
        self.request_count += 1
        
        # Only access error endpoint sometimes
        if random.random() < self.error_probability:
            # Lower error probability than the error scenario
            error_probability = round(random.uniform(0.1, 0.3), 2)
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
                # Any response is fine here since we're simulating real traffic
                if response.status_code >= 400:
                    # Mark as success for the load test since errors are expected
                    response.success()
                    self.session_data["last_error"] = {
                        "type": error_type,
                        "status_code": response.status_code
                    }
        else:
            # Skip this request this time
            pass
    
    @tag("external")
    @task(1)
    def external_dependent_request(self):
        """
        Occasionally test external service dependencies.
        """
        self.request_count += 1
        
        # 50% chance of using traced client
        use_traced = random.choice([True, False])
        
        with self.client.get(
            f"{self.api_prefix}/demo/external/{use_traced}",
            name=f"External Dependency (traced={use_traced})",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response_data = response.json()
                self.session_data["last_external_response"] = response_data
            else:
                # External dependencies might fail sometimes
                if response.status_code >= 500:
                    response.failure(f"External dependency failed with status {response.status_code}")
                else:
                    # 4xx errors might be expected in some cases
                    response.success()
    
    def on_stop(self):
        """
        Called when a user stops during a test
        """
        # Log additional metrics at the end of the user's session
        try:
            # Calculate and log session metrics
            elapsed = time.time() - self.start_time
            
            # Log custom metrics about this user session
            self.environment.runner.stats.log_request(
                request_method="USER",
                name="Session Duration",
                response_time=int(elapsed * 1000),
                response_length=0,
                exception=None,
            )
        except Exception as e:
            logging.error(f"Error in on_stop: {e}")
        
        # Perform any cleanup if needed
        self.session_data.clear()
        
        # Log final stats
        self.environment.runner.stats.log_request(
            request_type="INFO",
            name="Session Summary",
            response_time=0,
            response_length=0,
            exception=None,
            context={
                "user_id": self.user_id,
                "total_requests": self.request_count
            }
        ) 