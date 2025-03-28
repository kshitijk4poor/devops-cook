#!/usr/bin/env python3

"""
Main Locust configuration file for load testing the API.
This file imports the scenarios and sets up the test environment.
"""

import os
import logging
import datetime
from locust import HttpUser, task, between, events
from scenarios.basic_flow import BasicFlowUser
from scenarios.error_scenario import ErrorScenarioUser
from scenarios.mixed_scenario import MixedScenarioUser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("API-LoadTest")

# Root directory for results
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")

class ApiUser(HttpUser):
    """Base user class for API load testing"""
    wait_time = between(1, 3)
    
    def on_start(self):
        """Called when a user starts."""
        logger.info(f"User started with ID: {id(self)}")
        
    @task
    def health_check(self):
        with self.client.get("/api/v1/health", name="Health Check", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Health check failed with status code: {response.status_code}")
            
class LightLoadUser(ApiUser):
    """Simulates light load testing"""
    wait_time = between(3, 5)
    
    @task(3)
    def get_items(self):
        self.client.get("/api/v1/items", name="Get Items")
        
    @task(1)
    def get_single_item(self):
        self.client.get("/api/v1/items/1", name="Get Single Item")

class MediumLoadUser(ApiUser):
    """Simulates medium load testing"""
    wait_time = between(2, 4)
    
    @task(2)
    def get_items(self):
        self.client.get("/api/v1/items", name="Get Items")
        
    @task(1)
    def create_item(self):
        self.client.post(
            "/api/v1/items",
            json={"name": "Test Item", "description": "Created during load test"},
            name="Create Item"
        )

class HeavyLoadUser(ApiUser):
    """Simulates heavy load testing"""
    wait_time = between(1, 2)
    
    @task(3)
    def get_items(self):
        self.client.get("/api/v1/items", name="Get Items")
        
    @task(2)
    def get_single_item(self):
        self.client.get("/api/v1/items/1", name="Get Single Item")
        
    @task(1)
    def update_item(self):
        self.client.put(
            "/api/v1/items/1",
            json={"name": "Updated Item", "description": "Updated during load test"},
            name="Update Item"
        )
        
    @task(1)
    def delete_item(self):
        with self.client.delete("/api/v1/items/1", name="Delete Item", catch_response=True) as response:
            if response.status_code not in [200, 204]:
                response.failure(f"Delete operation failed with status {response.status_code}")

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """
    This is called when a test is started.
    """
    logger.info("Initializing load test environment")
    
    # Create results directory if it doesn't exist
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
        
    # Create timestamp for this test run
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    environment.timestamp = timestamp
    environment.results_dir = os.path.join(RESULTS_DIR, timestamp)
    
    if not os.path.exists(environment.results_dir):
        os.makedirs(environment.results_dir)
        
    logger.info(f"Results will be stored in {environment.results_dir}")
    logger.info("Load test starting")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """
    This is called when a test is stopped.
    """
    logger.info("Load test ending")
    
    # Instead of using the undefined method, we can manually handle stats if needed
    try:
        # If additional stats processing is needed, it could be implemented here
        pass
    except Exception as e:
        logger.error(f"Error processing test results: {e}")

# For importing in other scripts
__all__ = ["BasicFlowUser", "ErrorScenarioUser", "MixedScenarioUser"]

if __name__ == "__main__":
    logger.info("Locustfile loaded directly - run with 'locust -f locustfile.py'") 