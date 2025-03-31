import requests
import time
import random
import argparse
import uuid
import json
import concurrent.futures

def generate_logs(base_url, count=100, delay=0.1):
    """Generate sample logs by making API requests with varying characteristics."""
    print(f"Generating {count} log entries with diverse patterns...")
    
    # Standard working endpoints
    endpoints = [
        "/api/health",
        "/api/demo/random",
        "/api/demo/metrics",
        "/api/demo/data-echo"  # Use the new data-echo endpoint
    ]
    
    # Error-prone and potentially slow endpoints
    error_endpoints = [
        "/api/demo/error-prone",
        "/api/demo/not-found"
    ]

    # Track trace IDs to create related request sequences
    trace_ids = []
    
    # Define error scenarios for more 5xx responses
    error_scenarios = [
        # Server errors (500)
        {"error_probability": 1.0, "error_type": "server_error", "sleep": 0},
        # Timeout-like errors that also are slow
        {"error_probability": 0.9, "error_type": "timeout", "sleep": 1.5},
        # Validation errors that might cause 400s but sometimes 500s
        {"error_probability": 0.7, "error_type": "validation_error", "sleep": 0.2},
        # Overload simulation - high latency + high error rate
        {"error_probability": 0.95, "error_type": "server_error", "sleep": 2.5},
        # Database-like errors (slow + server error)
        {"error_probability": 0.85, "error_type": "database_error", "sleep": 1.8}
    ]
    
    # Request types with adjusted weights to generate more errors
    request_types = {
        "standard": 0.35,  # Reduced from 0.5
        "error": 0.35,     # Increased from 0.25
        "slow": 0.15,
        "trace": 0.10,
        "burst": 0.05      # New type: burst of requests to create spikes
    }
    
    # Enhanced tracing with parent-child relationships
    trace_hierarchy = {}  # Store trace hierarchies
    
    # Function to make a single request
    def make_request(endpoint, method="GET", params=None, headers=None, json_data=None, timeout=3):
        url = f"{base_url}{endpoint}"
        try:
            if method.upper() == "GET":
                response = requests.get(url, params=params, headers=headers, timeout=timeout)
            elif method.upper() == "POST":
                response = requests.post(url, params=params, headers=headers, json=json_data, timeout=timeout)
            return response
        except requests.exceptions.RequestException as e:
            return f"Exception: {str(e)[:50]}..."
    
    for i in range(count):
        # Generate a trace ID for this request
        trace_id = str(uuid.uuid4())
        
        # Select request type based on weights
        request_type = random.choices(
            list(request_types.keys()),
            weights=list(request_types.values()),
            k=1
        )[0]
        
        # Base headers with trace information
        headers = {
            "X-Request-ID": trace_id,
            "X-Test-Type": request_type
        }
        
        # STANDARD REQUESTS - Basic API calls
        if request_type == "standard":
            endpoint = random.choice(endpoints)
            if endpoint == "/api/demo/data-echo":
                try:
                    payload = {"test_data": f"Sample data {i}", "trace_id": trace_id}
                    response = requests.post(
                        f"{base_url}{endpoint}",
                        json=payload,
                        headers=headers,
                        timeout=2
                    )
                    print(f"POST request to {endpoint} - Status: {response.status_code} - Trace: {trace_id}")
                except requests.exceptions.RequestException as e:
                    print(f"Failed POST request to {endpoint} - Exception: {str(e)[:50]}... - Trace: {trace_id}")
            else:
                try:
                    response = requests.get(
                        f"{base_url}{endpoint}",
                        headers=headers,
                        timeout=2
                    )
                    print(f"GET request to {endpoint} - Status: {response.status_code} - Trace: {trace_id}")
                except requests.exceptions.RequestException as e:
                    print(f"Failed GET request to {endpoint} - Exception: {str(e)[:50]}... - Trace: {trace_id}")
        
        # ERROR REQUESTS - Deliberately causing errors
        elif request_type == "error":
            endpoint = random.choice(error_endpoints)
            
            # Select a random error scenario for more varied 5xx responses
            error_params = random.choice(error_scenarios)
            
            try:
                # Add jitter to sleep value to randomize response times
                if error_params["sleep"] > 0:
                    sleep_jitter = error_params["sleep"] * random.uniform(0.7, 1.3)
                    error_params["sleep"] = round(sleep_jitter, 2)
                
                # Custom timeout based on expected response time
                custom_timeout = max(3, error_params["sleep"] * 1.5)
                
                response = requests.get(
                    f"{base_url}{endpoint}",
                    params=error_params,
                    headers=headers,
                    timeout=custom_timeout
                )
                print(f"Error-prone request to {endpoint} - Status: {response.status_code} - Error Type: {error_params['error_type']} - Sleep: {error_params['sleep']}s - Trace: {trace_id}")
            except requests.exceptions.RequestException as e:
                print(f"Failed error-prone request to {endpoint} - Exception: {str(e)[:50]}... - Params: {error_params} - Trace: {trace_id}")

        # SLOW REQUESTS - Testing performance and timeouts
        elif request_type == "slow":
            # Use error-prone endpoint with sleep parameter
            endpoint = "/api/demo/error-prone"
            
            # Create variability in response times
            latency_profile = random.choice([
                {"sleep": random.uniform(0.5, 1.0), "error_probability": 0.05},  # Slightly slow
                {"sleep": random.uniform(1.0, 2.0), "error_probability": 0.1},   # Moderately slow
                {"sleep": random.uniform(2.0, 3.0), "error_probability": 0.2},   # Very slow
                {"sleep": random.uniform(3.0, 4.0), "error_probability": 0.4},   # Extremely slow with higher error chance
            ])
            
            try:
                # Custom timeout based on expected response time plus buffer
                custom_timeout = latency_profile["sleep"] * 1.5
                
                response = requests.get(
                    f"{base_url}{endpoint}",
                    params=latency_profile,
                    headers=headers,
                    timeout=custom_timeout
                )
                print(f"Slow request to {endpoint} - Status: {response.status_code} - Delay: {latency_profile['sleep']}s - Trace: {trace_id}")
            except requests.exceptions.RequestException as e:
                print(f"Failed slow request to {endpoint} - Exception: {str(e)[:50]}... - Trace: {trace_id}")
                
        # TRACE REQUESTS - Creating request chains for distributed tracing
        elif request_type == "trace":
            # Store this trace ID
            trace_ids.append(trace_id)
            trace_hierarchy[trace_id] = []
            
            # Make an initial request
            primary_endpoint = random.choice(endpoints)
            try:
                response = requests.get(
                    f"{base_url}{primary_endpoint}",
                    headers=headers,
                    timeout=2
                )
                print(f"Primary trace request to {primary_endpoint} - Status: {response.status_code} - Trace: {trace_id}")
                
                # Make 1-4 related follow-up requests using the same trace ID
                for j in range(random.randint(1, 4)):
                    child_trace_id = str(uuid.uuid4())
                    trace_hierarchy[trace_id].append(child_trace_id)
                    
                    secondary_endpoint = random.choice(endpoints + error_endpoints)
                    follow_headers = {
                        "X-Request-ID": child_trace_id,
                        "X-Parent-Trace-ID": trace_id,
                        "X-Trace-Type": "follow-up",
                        "X-Trace-Step": str(j+1)
                    }
                    
                    # Slightly delay the follow-up request
                    time.sleep(random.uniform(0.05, 0.2))
                    
                    # For every third request in a trace, add a chance of error
                    if j % 3 == 2:  # 0-indexed, so this is the 3rd, 6th, etc.
                        params = {"error_probability": 0.6, "error_type": "server_error"}
                    else:
                        params = {}
                    
                    try:
                        follow_response = requests.get(
                            f"{base_url}{secondary_endpoint}",
                            params=params,
                            headers=follow_headers,
                            timeout=2
                        )
                        print(f"Follow-up request to {secondary_endpoint} - Status: {follow_response.status_code} - Parent: {trace_id} - Child: {child_trace_id}")
                    except requests.exceptions.RequestException as e:
                        print(f"Failed follow-up request to {secondary_endpoint} - Exception: {str(e)[:50]}... - Parent: {trace_id} - Child: {child_trace_id}")
                
            except requests.exceptions.RequestException as e:
                print(f"Failed primary trace request to {primary_endpoint} - Exception: {str(e)[:50]}... - Trace: {trace_id}")
        
        # BURST REQUESTS - Simulate sudden traffic spikes
        elif request_type == "burst":
            # Create a burst of 5-10 concurrent requests
            burst_size = random.randint(5, 10)
            burst_endpoint = random.choice(endpoints + error_endpoints)
            burst_trace_id = trace_id  # Use same trace ID for correlation
            
            print(f"Initiating burst of {burst_size} requests to {burst_endpoint} - Burst ID: {burst_trace_id}")
            
            # Use thread pool to make concurrent requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=burst_size) as executor:
                futures = []
                
                for b in range(burst_size):
                    burst_headers = {
                        "X-Request-ID": f"{burst_trace_id}-{b}",
                        "X-Burst-ID": burst_trace_id,
                        "X-Burst-Sequence": str(b),
                        "X-Test-Type": "burst"
                    }
                    
                    # Mix in some error scenarios
                    if burst_endpoint == "/api/demo/error-prone" and random.random() < 0.6:
                        params = {"error_probability": random.uniform(0.5, 1.0)}
                    else:
                        params = {}
                    
                    # Submit request to thread pool
                    futures.append(
                        executor.submit(
                            make_request,
                            burst_endpoint,
                            method="GET",
                            params=params,
                            headers=burst_headers,
                            timeout=3
                        )
                    )
                
                # Process results
                for i, future in enumerate(concurrent.futures.as_completed(futures)):
                    result = future.result()
                    if isinstance(result, requests.Response):
                        print(f"Burst request {i+1}/{burst_size} - Status: {result.status_code} - Burst ID: {burst_trace_id}")
                    else:
                        print(f"Burst request {i+1}/{burst_size} - Failed - {result} - Burst ID: {burst_trace_id}")
                
            # Add a slightly longer delay after a burst
            time.sleep(random.uniform(delay, delay * 2))
            
        # Occasionally reuse an existing trace ID to create complex request patterns
        if trace_ids and random.random() < 0.15:
            reused_trace_id = random.choice(trace_ids)
            headers["X-Request-ID"] = reused_trace_id
            headers["X-Trace-Type"] = "continuation"
            
            endpoint = random.choice(endpoints + error_endpoints)
            try:
                response = requests.get(
                    f"{base_url}{endpoint}",
                    headers=headers,
                    timeout=2
                )
                print(f"Continuation request to {endpoint} - Status: {response.status_code} - Trace: {reused_trace_id}")
            except requests.exceptions.RequestException as e:
                print(f"Failed continuation request to {endpoint} - Exception: {str(e)[:50]}... - Trace: {reused_trace_id}")
            
        # Add a variable delay between requests to simulate real traffic patterns
        time.sleep(random.uniform(delay * 0.5, delay * 1.5))
    
    print("Done generating logs!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate test logs for API')
    parser.add_argument('--url', default='http://localhost:8001', help='Base URL for the API')
    parser.add_argument('--count', type=int, default=100, help='Number of log entries to generate')
    parser.add_argument('--delay', type=float, default=0.1, help='Delay between requests in seconds')
    
    args = parser.parse_args()
    generate_logs(args.url, args.count, args.delay)
