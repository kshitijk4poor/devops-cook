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

# Generate test logs
echo "Generating test logs..."
python tests/generate_logs.py --count 50 --delay 0.1

echo ""
echo "ELK Stack Verification Complete"
echo "You can access Kibana at: http://localhost:5601"
echo "Elasticsearch is available at: http://localhost:9200"
echo "Logstash stats are available at: http://localhost:9600" 