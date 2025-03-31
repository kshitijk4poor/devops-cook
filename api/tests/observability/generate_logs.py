import requests
import time
import random
import argparse
import uuid
import json

def generate_logs(base_url, count=100, delay=0.1):
    """Generate sample logs by making API requests."""
    print(f"Generating {count} basic API log entries...")
    
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

    # Add 5xx response types
    error_types = [
        {"error_probability": 1.0, "error_type": "server_error"},
        {"error_probability": 0.9, "error_type": "timeout"},
        {"error_probability": 0.95, "error_type": "database_error"}
    ]

    for i in range(count):
        # Generate request ID for tracing
        request_id = str(uuid.uuid4())
        headers = {"X-Request-ID": request_id}
        
        # Increase error probability to 40% (was 20%)
        if random.random() < 0.4:
            endpoint = random.choice(error_endpoints)
            
            # Select random error type for more diverse 5xx errors
            error_type = random.choice(error_types)
            
            # Add random sleep time to test response time variations
            sleep_time = random.uniform(0, 3.0)
            if sleep_time > 0:
                error_type["sleep"] = round(sleep_time, 2)
                
            try:
                response = requests.get(
                    f"{base_url}{endpoint}", 
                    params=error_type, 
                    headers=headers,
                    timeout=max(3, sleep_time * 1.5)
                )
                print(f"Error request to {endpoint} - Status: {response.status_code} - Type: {error_type['error_type']} - ReqID: {request_id}")
            except requests.exceptions.RequestException as e:
                print(f"Error request to {endpoint} - Exception: {str(e)[:50]}... - ReqID: {request_id}")
        else:
            endpoint = random.choice(endpoints)
            
            # Add chance of slow but successful requests
            params = {}
            if random.random() < 0.3:
                params["sleep"] = round(random.uniform(0.1, 1.5), 2)
                
            if endpoint == "/demo/data-echo":
                try:
                    payload = {"test_data": f"Data {i}", "request_id": request_id}
                    response = requests.post(
                        f"{base_url}{endpoint}", 
                        json=payload,
                        headers=headers,
                        params=params,
                        timeout=5
                    )
                    print(f"POST request to {endpoint} - Status: {response.status_code} - ReqID: {request_id}")
                except requests.exceptions.RequestException as e:
                    print(f"Failed POST request to {endpoint} - Exception: {str(e)[:50]}... - ReqID: {request_id}")
            else:
                try:
                    response = requests.get(
                        f"{base_url}{endpoint}", 
                        headers=headers,
                        params=params,
                        timeout=5
                    )
                    print(f"GET request to {endpoint} - Status: {response.status_code} - ReqID: {request_id}")
                except requests.exceptions.RequestException as e:
                    print(f"Failed GET request to {endpoint} - Exception: {str(e)[:50]}... - ReqID: {request_id}")
            
        # Add a randomized delay between requests
        time.sleep(random.uniform(delay * 0.5, delay * 2.0))
    
    print("Done generating basic API logs!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate test logs for API')
    parser.add_argument('--url', default='http://localhost:8001', help='Base URL for the API')
    parser.add_argument('--count', type=int, default=100, help='Number of log entries to generate')
    parser.add_argument('--delay', type=float, default=0.1, help='Delay between requests in seconds')
    
    args = parser.parse_args()
    generate_logs(args.url, args.count, args.delay)
