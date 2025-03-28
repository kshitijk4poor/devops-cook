import requests
import time
import random
import argparse

def generate_logs(base_url, count=100, delay=0.1):
    """Generate sample logs by making API requests."""
    print(f"Generating {count} log entries...")
    
    # Include all working endpoints
    endpoints = [
        "/health",
        "/demo/random",
        "/demo/metrics",
        "/demo/data-echo"  # Use the new data-echo endpoint
    ]
    
    error_endpoints = [
        "/demo/error-prone",
        "/demo/not-found"
    ]

    for i in range(count):
        # Occasionally generate errors (20% of requests)
        if random.random() < 0.2:
            endpoint = random.choice(error_endpoints)
            params = {"force_error": True} if endpoint == "/demo/error-prone" else {}
            try:
                response = requests.get(f"{base_url}{endpoint}", params=params, timeout=2)
                print(f"Error request made to {endpoint} - Status: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"Error request made to {endpoint} - Exception: {str(e)[:50]}...")
        else:
            endpoint = random.choice(endpoints)
            if endpoint == "/demo/data-echo":
                try:
                    response = requests.post(f"{base_url}{endpoint}", timeout=2)
                    print(f"POST request to {endpoint} - Status: {response.status_code}")
                except requests.exceptions.RequestException as e:
                    print(f"Failed POST request to {endpoint} - Exception: {str(e)[:50]}...")
            else:
                try:
                    response = requests.get(f"{base_url}{endpoint}", timeout=2)
                    print(f"GET request to {endpoint} - Status: {response.status_code}")
                except requests.exceptions.RequestException as e:
                    print(f"Failed GET request to {endpoint} - Exception: {str(e)[:50]}...")
            
        # Add a small delay between requests
        time.sleep(delay)
    
    print("Done generating logs!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate test logs for API')
    parser.add_argument('--url', default='http://localhost:8001', help='Base URL for the API')
    parser.add_argument('--count', type=int, default=100, help='Number of log entries to generate')
    parser.add_argument('--delay', type=float, default=0.1, help='Delay between requests in seconds')
    
    args = parser.parse_args()
    generate_logs(args.url, args.count, args.delay)
