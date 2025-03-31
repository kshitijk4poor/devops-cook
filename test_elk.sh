#!/bin/bash

# Check Elasticsearch
echo -n "Checking Elasticsearch... "
es_status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:9200/_cluster/health")
echo "Status: $es_status"
if [[ "$es_status" == "200" ]]; then
  echo "✅ Elasticsearch is running"
else
  echo "❌ Elasticsearch is not running"
fi

# Check Kibana
echo -n "Checking Kibana... "
kibana_status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:5601/api/status")
echo "Status: $kibana_status"
if [[ "$kibana_status" == "200" ]]; then
  echo "✅ Kibana is running"
else
  echo "❌ Kibana is not running"
fi

# Check Logstash
echo -n "Checking Logstash... "
logstash_status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:9600")
echo "Status: $logstash_status"
if [[ "$logstash_status" == "200" ]]; then
  echo "✅ Logstash is running"
else
  echo "❌ Logstash is not running"
fi

# Check API Health
echo -n "Checking API Health... "
api_status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8001/api/health")
echo "Status: $api_status"
if [[ "$api_status" == "200" ]]; then
  echo "✅ API is running"
else
  echo "❌ API is not running"
fi

# Check API Demo Random Endpoint
echo -n "Checking Demo Random Endpoint... "
random_status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8001/api/demo/random")
echo "Status: $random_status"
if [[ "$random_status" == "200" ]]; then
  echo "✅ Demo Random Endpoint is working"
else
  echo "❌ Demo Random Endpoint is not working"
fi

# Check API Demo Metrics Endpoint
echo -n "Checking Demo Metrics Endpoint... "
metrics_status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8001/api/demo/metrics")
echo "Status: $metrics_status"
if [[ "$metrics_status" == "200" ]]; then
  echo "✅ Demo Metrics Endpoint is working"
else
  echo "❌ Demo Metrics Endpoint is not working"
fi

# Check API Demo Error-Prone Endpoint
echo -n "Checking Demo Error-Prone Endpoint... "
error_status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8001/api/demo/error-prone" || echo "Failed")
echo "Status: $error_status"
if [[ "$error_status" == "200" || "$error_status" == "500" ]]; then
  echo "✅ Demo Error-Prone Endpoint is accessible"
else
  echo "❌ Demo Error-Prone Endpoint is not accessible"
fi

# Check API Demo Data Echo Endpoint
echo -n "Checking Demo Data Echo Endpoint... "
echo_status=$(curl -s -o /dev/null -w "%{http_code}" -X POST "http://localhost:8001/api/demo/data-echo")
echo "Status: $echo_status"
if [[ "$echo_status" == "200" ]]; then
  echo "✅ Demo Data Echo Endpoint is working"
else
  echo "❌ Demo Data Echo Endpoint is not working"
fi

# Create log generation script
echo "Creating log generation script..."
cat > tests/generate_logs.py << 'EOF'
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
EOF

# Update the original API log generator in api/tests/observability/
echo "Updating API observability log generator script..."
cat > api/tests/observability/generate_logs.py << 'EOF'
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
EOF

# Generate test logs if endpoints are working
if [[ "$random_status" == "200" && "$metrics_status" == "200" && "$echo_status" == "200" ]]; then
  echo "All critical endpoints are operational."
  
  # Check if we're in test mode - don't prompt for input in that case
  if [ -t 0 ]; then  # Check if running interactively
    # In interactive mode, ask the user if they want to generate logs
    echo -n "Do you want to generate logs now? (y/n) "
    read answer
    if [[ "$answer" == "y" || "$answer" == "Y" ]]; then
      echo "Generating test logs with a mix of regular, slow and error-prone requests..."
      echo "This will include more 5xx errors and randomized response times..."
      
      # Run both log generators
      echo "Running primary advanced log generator (tests/generate_logs.py)..."
      python tests/generate_logs.py --count 50 --delay 0.15
      
      echo ""
      echo "Running API observability log generator (api/tests/observability/generate_logs.py)..."
      python api/tests/observability/generate_logs.py --count 30 --delay 0.2
    fi
  else
    # In non-interactive mode (e.g., in a CI/CD pipeline), generate logs automatically
    echo "Generating test logs automatically..."
    # Run both log generators
    python tests/generate_logs.py --count 50 --delay 0.15
    python api/tests/observability/generate_logs.py --count 30 --delay 0.2
  fi
else
  echo "Some API endpoints are not working properly. Skipping log generation."
fi

# Create a summary of status codes in Elasticsearch
echo ""
echo "Checking status code distribution in Elasticsearch..."
curl -s -X GET "http://localhost:9200/fastapi-logs-*/_search" -H 'Content-Type: application/json' -d'{
  "size": 0,
  "aggs": {
    "status_codes": {
      "terms": { "field": "status_code" }
    }
  }
}' | grep -oP '"key":\s*\K\d+.*?(?=,).*?"doc_count":\s*\K\d+' | awk '{print "HTTP " $1 ": " $2 " requests"}'

# Check for 5xx errors distribution
echo ""
echo "Checking 5xx errors distribution in Elasticsearch..."
curl -s -X GET "http://localhost:9200/fastapi-logs-*/_search" -H 'Content-Type: application/json' -d'{
  "size": 0,
  "query": {
    "range": {
      "status_code": {
        "gte": 500,
        "lt": 600
      }
    }
  },
  "aggs": {
    "response_times": {
      "stats": {
        "field": "response_time"
      }
    },
    "status_codes": {
      "terms": {
        "field": "status_code"
      }
    }
  }
}' | grep -o -E '"count":[0-9]+|"min":[0-9.]+|"max":[0-9.]+|"avg":[0-9.]+|"key":[0-9]+,"doc_count":[0-9]+'

echo ""
echo "ELK Stack Verification Complete"
echo "You can access Kibana at: http://localhost:5601"
echo "Elasticsearch is available at: http://localhost:9200"
echo "Logstash stats are available at: http://localhost:9600"
echo "API is available at: http://localhost:8001"
echo ""
echo "Enhanced observability data with more error scenarios and response time variations has been generated."
echo "You can view API logs in Kibana or view traces in Jaeger at: http://localhost:16686" 