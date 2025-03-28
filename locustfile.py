#!/usr/bin/env python3

from locust import HttpUser, task, between, events
import random
import json
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("API-LoadTest")

class ApiUser(HttpUser):
    """
    Base user class that simulates a user interacting with the API.
    This class provides common behaviors and configuration for all users.
    """
    # Wait between 1 to 5 seconds between tasks
    wait_time = between(1, 5)
    
    # Track user's items for use in update/delete operations
    user_items = []
    
    def on_start(self):
        """
        Initialize the user and perform any setup needed before the test begins.
        """
        self.client.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        logger.info(f"User started with ID: {id(self)}")

    @task(3)
    def get_items(self):
        """
        Get all items - this is a common operation, so weighted higher.
        """
        with self.client.get("/api/v1/items", name="Get Items") as response:
            if response.status_code == 200:
                # Store items for later use in update/delete operations
                data = response.json()
                if "items" in data and data["items"]:
                    self.user_items = [item["id"] for item in data["items"]]
            else:
                logger.error(f"Failed to get items: {response.status_code} - {response.text}")

    @task(2)
    def get_single_item(self):
        """
        Get a single item - slightly less common than listing all items.
        """
        # Either use an item we know about, or generate a random ID
        if self.user_items and random.random() < 0.7:
            item_id = random.choice(self.user_items)
        else:
            item_id = random.randint(1, 100)
            
        with self.client.get(f"/api/v1/items/{item_id}", name="Get Single Item") as response:
            if response.status_code not in [200, 404]:  # 404 is expected sometimes
                logger.error(f"Unexpected error getting item {item_id}: {response.status_code} - {response.text}")

    @task(1)
    def create_item(self):
        """
        Create a new item - less frequent operation.
        """
        # Generate random item data
        item_data = {
            "name": f"Test Item {random.randint(1000, 9999)}",
            "description": f"Created during load test at {time.time()}"
        }
        
        # Occasionally send invalid data to test error handling
        if random.random() < 0.1:
            item_data.pop("name")
            
        with self.client.post("/api/v1/items", 
                             json=item_data,
                             name="Create Item") as response:
            if response.status_code == 200:
                # Store the ID for later operations
                data = response.json()
                if "id" in data:
                    self.user_items.append(data["id"])
            elif response.status_code != 400:  # 400 is expected for invalid data
                logger.error(f"Unexpected error creating item: {response.status_code} - {response.text}")

    @task(1)
    def update_item(self):
        """
        Update an existing item - less frequent operation.
        """
        if not self.user_items:
            return
            
        item_id = random.choice(self.user_items)
        item_data = {
            "name": f"Updated Item {random.randint(1000, 9999)}",
            "description": f"Updated during load test at {time.time()}"
        }
        
        with self.client.put(f"/api/v1/items/{item_id}",
                            json=item_data,
                            name="Update Item") as response:
            if response.status_code not in [200, 404]:  # 404 is expected sometimes
                logger.error(f"Unexpected error updating item {item_id}: {response.status_code} - {response.text}")

    @task(1)
    def delete_item(self):
        """
        Delete an item - less frequent operation.
        """
        if not self.user_items:
            return
            
        item_id = random.choice(self.user_items)
        
        with self.client.delete(f"/api/v1/items/{item_id}", name="Delete Item") as response:
            if response.status_code == 200:
                # Remove the item from our list
                if item_id in self.user_items:
                    self.user_items.remove(item_id)
            elif response.status_code not in [404, 500]:  # 404 and 500 are expected sometimes
                logger.error(f"Unexpected error deleting item {item_id}: {response.status_code} - {response.text}")

    @task(10)
    def check_health(self):
        """
        Check API health - very frequent operation to monitor system health.
        """
        with self.client.get("/health", name="Health Check") as response:
            if response.status_code != 200:
                logger.error(f"Health check failed: {response.status_code} - {response.text}")


class LightLoadUser(ApiUser):
    """
    User that performs light load on the system.
    Makes fewer requests with longer wait times.
    """
    wait_time = between(3, 7)
    weight = 3

class MediumLoadUser(ApiUser):
    """
    User that performs medium load on the system.
    Standard behavior defined in the parent class.
    """
    weight = 2

class HeavyLoadUser(ApiUser):
    """
    User that generates heavy load on the system.
    Makes more frequent requests with shorter wait times.
    """
    wait_time = between(0.5, 3)
    weight = 1


# Event hooks for collecting and exporting metrics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """
    Called when a test is starting
    """
    logger.info("Load test starting")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """
    Called when a test is ending
    """
    logger.info("Load test ending")


if __name__ == "__main__":
    logger.info("Locustfile loaded directly - run with 'locust -f locustfile.py'") 