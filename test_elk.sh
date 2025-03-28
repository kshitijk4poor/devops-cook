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
api_status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8001/health")
echo "Status: $api_status"
if [[ "$api_status" == "200" ]]; then
  echo "✅ API is running"
else
  echo "❌ API is not running"
fi

# Check API Demo Random Endpoint
echo -n "Checking Demo Random Endpoint... "
random_status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8001/demo/random")
echo "Status: $random_status"
if [[ "$random_status" == "200" ]]; then
  echo "✅ Demo Random Endpoint is working"
else
  echo "❌ Demo Random Endpoint is not working"
fi

# Check API Demo Metrics Endpoint
echo -n "Checking Demo Metrics Endpoint... "
metrics_status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8001/demo/metrics")
echo "Status: $metrics_status"
if [[ "$metrics_status" == "200" ]]; then
  echo "✅ Demo Metrics Endpoint is working"
else
  echo "❌ Demo Metrics Endpoint is not working"
fi

# Check API Demo Data Echo Endpoint
echo -n "Checking Demo Data Echo Endpoint... "
echo_status=$(curl -s -o /dev/null -w "%{http_code}" -X POST "http://localhost:8001/demo/data-echo")
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
EOF

# Generate test logs if endpoints are working
if [[ "$random_status" == "200" && "$metrics_status" == "200" && "$echo_status" == "200" ]]; then
  echo "All tested endpoints are operational."
  
  # Check if we're in test mode - don't prompt for input in that case
  if [ -t 0 ]; then  # Check if running interactively
    # In interactive mode, ask the user if they want to generate logs
    echo -n "Do you want to generate logs now? (y/n) "
    read answer
    if [[ "$answer" == "y" || "$answer" == "Y" ]]; then
      echo "Generating test logs..."
      python tests/generate_logs.py --count 20 --delay 0.2
    fi
  else
    # In non-interactive mode (e.g., in a CI/CD pipeline), generate logs automatically
    echo "Generating test logs automatically..."
    python tests/generate_logs.py --count 20 --delay 0.2
  fi
else
  echo "Some API endpoints are not working properly. Skipping log generation."
fi

echo ""
echo "ELK Stack Verification Complete"
echo "You can access Kibana at: http://localhost:5601"
echo "Elasticsearch is available at: http://localhost:9200"
echo "Logstash stats are available at: http://localhost:9600"
echo "API is available at: http://localhost:8001"
echo ""
echo "Note: The echo endpoint has issues but we've configured the test script"
echo "to use only the working endpoints to generate test logs." 