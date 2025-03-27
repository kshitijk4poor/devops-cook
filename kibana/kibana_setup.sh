#!/bin/bash

# Wait for Kibana to be ready
echo "Waiting for Kibana to start..."
until curl -s http://kibana:5601/api/status | grep -q "green"; do
    sleep 5
done

# Create index pattern
echo "Creating index pattern..."
curl -X POST "http://kibana:5601/api/saved_objects/index-pattern/fastapi-logs-*" \
  -H 'kbn-xsrf: true' \
  -H 'Content-Type: application/json' \
  -d '{
  "attributes": {
    "title": "fastapi-logs-*",
    "timeFieldName": "@timestamp"
  }
}'

# Import dashboard if needed
# curl -X POST "http://kibana:5601/api/saved_objects/_import" \
#   -H 'kbn-xsrf: true' \
#   --form file=@/usr/share/kibana/dashboards/api_logs.ndjson

echo "Kibana setup complete." 