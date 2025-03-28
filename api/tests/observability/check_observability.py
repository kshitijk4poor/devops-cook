#!/usr/bin/env python3
"""
Script to check if all observability components are working correctly.
This script performs simple health checks for each observability component.
"""

import requests
import sys
import time
import json

def check_api():
    """Check if the API is up and running."""
    try:
        response = requests.get("http://localhost:8001/health")
        if response.status_code == 200:
            print("✅ API is running")
            return True
        else:
            print(f"❌ API health check failed with status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ API health check failed: {str(e)}")
        return False

def check_prometheus():
    """Check if Prometheus is up and scraping metrics."""
    try:
        response = requests.get("http://localhost:9091/api/v1/targets")
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "success":
                targets = data["data"]["activeTargets"]
                up_targets = [t for t in targets if t["health"] == "up"]
                print(f"✅ Prometheus is running with {len(up_targets)}/{len(targets)} targets up")
                return True
            else:
                print(f"❌ Prometheus API returned an error: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Prometheus health check failed with status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Prometheus health check failed: {str(e)}")
        return False

def check_grafana():
    """Check if Grafana is up and running."""
    try:
        response = requests.get("http://localhost:3000/api/health")
        if response.status_code == 200:
            data = response.json()
            if data["database"] == "ok":
                print("✅ Grafana is running")
                return True
            else:
                print(f"❌ Grafana database status: {data['database']}")
                return False
        else:
            print(f"❌ Grafana health check failed with status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Grafana health check failed: {str(e)}")
        return False

def check_elasticsearch():
    """Check if Elasticsearch is up and running."""
    try:
        response = requests.get("http://localhost:9200/_cluster/health")
        if response.status_code == 200:
            data = response.json()
            status = data["status"]
            if status in ["green", "yellow"]:
                print(f"✅ Elasticsearch is running (status: {status})")
                return True
            else:
                print(f"❌ Elasticsearch cluster status: {status}")
                return False
        else:
            print(f"❌ Elasticsearch health check failed with status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Elasticsearch health check failed: {str(e)}")
        return False

def check_logstash():
    """Check if Logstash is up and running."""
    try:
        response = requests.get("http://localhost:9600/_node/stats")
        if response.status_code == 200:
            print("✅ Logstash is running")
            return True
        else:
            print(f"❌ Logstash health check failed with status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Logstash health check failed: {str(e)}")
        return False

def check_kibana():
    """Check if Kibana is up and running."""
    try:
        response = requests.get("http://localhost:5601/api/status")
        if response.status_code == 200:
            data = response.json()
            if data["status"]["overall"]["state"] == "green":
                print("✅ Kibana is running")
                return True
            else:
                print(f"❌ Kibana status: {data['status']['overall']['state']}")
                return False
        else:
            print(f"❌ Kibana health check failed with status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Kibana health check failed: {str(e)}")
        return False

def check_jaeger():
    """Check if Jaeger is up and running."""
    try:
        response = requests.get("http://localhost:16686/api/services")
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) or isinstance(data, dict):
                print(f"✅ Jaeger is running")
                if isinstance(data, list) and len(data) > 0:
                    print(f"   Found {len(data)} services")
                elif isinstance(data, dict) and "data" in data and len(data["data"]) > 0:
                    print(f"   Found {len(data['data'])} services")
                else:
                    print("   No services found yet (this is normal for new deployments)")
                return True
            else:
                print("❌ Jaeger API returned unexpected data format")
                return False
        else:
            print(f"❌ Jaeger health check failed with status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Jaeger health check failed: {str(e)}")
        return False

def check_all():
    """Run all checks and return overall status."""
    print("🔍 Checking observability components...\n")
    
    checks = [
        check_api,
        check_prometheus,
        check_grafana,
        check_elasticsearch,
        check_logstash,
        check_kibana,
        check_jaeger
    ]
    
    results = []
    for check in checks:
        result = check()
        results.append(result)
        time.sleep(0.5)  # Brief pause between checks
    
    print("\n" + "-" * 50)
    success = all(results)
    if success:
        print("✅ All observability components are running!")
    else:
        print("❌ Some observability components are not running properly")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(check_all()) 