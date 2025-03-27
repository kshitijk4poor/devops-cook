#!/bin/bash

# Wait for Elasticsearch to be ready
echo "Waiting for Elasticsearch..."
until curl -s http://elasticsearch:9200 > /dev/null; do
    sleep 1
done

# Create index template for logs
echo "Creating index template..."
curl -X PUT "http://elasticsearch:9200/_template/fastapi-logs" -H 'Content-Type: application/json' -d'
{
  "index_patterns": ["fastapi-logs-*"],
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0
  },
  "mappings": {
    "properties": {
      "@timestamp": { "type": "date" },
      "level": { "type": "keyword" },
      "message": { "type": "text" },
      "request_id": { "type": "keyword" },
      "method": { "type": "keyword" },
      "url": { "type": "keyword" },
      "status_code": { "type": "integer" },
      "duration": { "type": "float" },
      "event": { "type": "keyword" }
    }
  }
}'

echo "Setup complete." 