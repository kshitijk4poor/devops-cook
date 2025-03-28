from locust import HttpUser, task, between, events
import random
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("API-Test")

class SimpleApiUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(10)
    def health_check(self):
        with self.client.get("/api/health", name="Health Check") as response:
            if response.status_code != 200:
                logger.error(f"Health check failed: {response.status_code} - {response.text}")
    
    @task(3)
    def normal_endpoint(self):
        with self.client.get("/api/demo/normal", name="Normal Endpoint") as response:
            if response.status_code != 200:
                logger.error(f"Normal endpoint failed: {response.status_code} - {response.text}")
                
    @task(2)
    def slow_endpoint(self):
        params = {
            "delay_min": 0.5,
            "delay_max": 2.0
        }
        with self.client.get("/api/demo/slow", name="Slow Endpoint", params=params) as response:
            if response.status_code != 200:
                logger.error(f"Slow endpoint failed: {response.status_code} - {response.text}")
    
    @task(1)
    def error_prone_endpoint(self):
        with self.client.get("/api/demo/error-prone", name="Error Endpoint") as response:
            pass  # This endpoint sometimes returns errors by design

# Event hooks
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    logger.info("Load test starting")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    logger.info("Load test ending") 