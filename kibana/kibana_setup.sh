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

# Set the default index pattern for Discover
echo "Setting default index pattern..."
curl -X POST "http://kibana:5601/api/kibana/settings" \
  -H 'kbn-xsrf: true' \
  -H 'Content-Type: application/json' \
  -d '{
  "changes": {
    "defaultIndex": "fastapi-logs-*"
  }
}'

# Create visualization
echo "Creating visualization..."
curl -X POST "http://kibana:5601/api/saved_objects/visualization/api-request-count" \
  -H 'kbn-xsrf: true' \
  -H 'Content-Type: application/json' \
  -d '{
  "attributes": {
    "title": "API Request Count",
    "visState": "{\"title\":\"API Request Count\",\"type\":\"metric\",\"params\":{\"addTooltip\":true,\"addLegend\":false,\"type\":\"metric\",\"metric\":{\"percentageMode\":false,\"useRanges\":false,\"colorSchema\":\"Green to Red\",\"metricColorMode\":\"None\",\"colorsRange\":[{\"from\":0,\"to\":10000}],\"labels\":{\"show\":true},\"invertColors\":false,\"style\":{\"bgFill\":\"#000\",\"bgColor\":false,\"labelColor\":false,\"subText\":\"\",\"fontSize\":60}}},\"aggs\":[{\"id\":\"1\",\"enabled\":true,\"type\":\"count\",\"schema\":\"metric\",\"params\":{}}]}",
    "uiStateJSON": "{}",
    "description": "",
    "version": 1,
    "kibanaSavedObjectMeta": {
      "searchSourceJSON": "{\"index\":\"fastapi-logs-*\",\"query\":{\"query\":\"\",\"language\":\"kuery\"},\"filter\":[]}"
    }
  }
}'

# Create dashboard
echo "Creating dashboard..."
curl -X POST "http://kibana:5601/api/saved_objects/dashboard/api-dashboard" \
  -H 'kbn-xsrf: true' \
  -H 'Content-Type: application/json' \
  -d '{
  "attributes": {
    "title": "API Logs Dashboard",
    "hits": 0,
    "description": "Dashboard for API Logs",
    "panelsJSON": "[{\"embeddableConfig\":{},\"gridData\":{\"h\":15,\"i\":\"1\",\"w\":24,\"x\":0,\"y\":0},\"panelIndex\":\"1\",\"version\":\"7.17.0\",\"panelRefName\":\"panel_0\"}]",
    "optionsJSON": "{\"hidePanelTitles\":false,\"useMargins\":true}",
    "version": 1,
    "timeRestore": false,
    "kibanaSavedObjectMeta": {
      "searchSourceJSON": "{\"query\":{\"language\":\"kuery\",\"query\":\"\"},\"filter\":[]}"
    }
  },
  "references": [
    {
      "name": "panel_0",
      "type": "visualization",
      "id": "api-request-count"
    }
  ]
}'

# Import dashboard if needed
# curl -X POST "http://kibana:5601/api/saved_objects/_import" \
#   -H 'kbn-xsrf: true' \
#   --form file=@/usr/share/kibana/dashboards/api_logs.ndjson

echo "Kibana setup complete." 