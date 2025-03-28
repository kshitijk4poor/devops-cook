# Observability Stack

This document describes the observability components used in this platform and how they integrate with each other.

> Note: All diagrams are available in both Mermaid (.mmd) format for interactive viewing and PNG format for static viewing. To generate PNG images from Mermaid files, run `./scripts/generate_images.sh`.

## Architecture Overview

![Observability Architecture](images/architecture.mmd)

## Components

### Metrics: Prometheus and Grafana

#### Prometheus

Prometheus is a time-series database that collects and stores metrics data. In our setup, it:

- Scrapes metrics from the FastAPI backend every 15 seconds
- Stores metrics in its internal time-series database
- Provides a query language (PromQL) for data retrieval

**Configuration:** [prometheus.yml](../prometheus.yml)

**Key metrics:**
- HTTP request count by endpoint
- Response time percentiles (p50, p90, p99)
- Error rates and counts
- System metrics (CPU, memory)

#### Grafana

Grafana provides visualization dashboards for metrics. Our implementation includes:

- Pre-configured dashboards for API monitoring
- Alerts based on metric thresholds
- Custom panels for key performance indicators

**Sample Dashboard:**

![Metrics Dashboard](images/metrics_dashboard.mmd)

**Configuration:** [grafana/provisioning](../grafana/provisioning)

**Default credentials:**
- Username: admin
- Password: admin

### Logging: ELK Stack

The ELK (Elasticsearch, Logstash, Kibana) stack handles structured logging:

#### Elasticsearch

Elasticsearch stores and indexes log data for efficient querying.

**Configuration:** [elasticsearch/elasticsearch.yml](../elasticsearch/elasticsearch.yml)

#### Logstash

Logstash processes incoming log data, applying transformations and enrichment before sending to Elasticsearch.

**Pipeline configuration:** [logstash/pipeline](../logstash/pipeline)

Our pipeline:
1. Receives JSON-formatted logs
2. Parses timestamps and log levels
3. Adds service metadata
4. Forwards to Elasticsearch

#### Kibana

Kibana provides a web interface for searching, analyzing, and visualizing logs.

**Sample Log Explorer:**

![Kibana Log Explorer](images/log_explorer.mmd)

**Configuration:** [kibana/dashboards](../kibana/dashboards)

**Features:**
- Full-text search across logs
- Structured query language (KQL)
- Pre-configured dashboards for log analysis
- Visualizations for log patterns and anomalies

### Tracing: Jaeger

Jaeger implements distributed tracing to track requests across service boundaries.

**Sample Trace View:**

![Jaeger Trace View](images/trace_view.mmd)

**Trace Details:**

![Trace Details](images/trace_details.mmd)

**Key capabilities:**
- Trace context propagation
- Span collection and storage
- Web UI for trace visualization
- Trace filtering and analysis

## Integration Points

Our observability components are integrated in several ways:

1. **Trace ID propagation:** Trace IDs are included in logs for correlation
2. **Metrics linking:** Metrics dashboards link to related logs and traces
3. **Common metadata:** Service name, environment, and version are shared across all telemetry

## Sample Queries

### PromQL (Prometheus)

**Request Rate by Endpoint:**
```
sum(rate(http_requests_total[5m])) by (endpoint)
```

**95th Percentile Response Time:**
```
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint))
```

**Error Rate Percentage:**
```
sum(rate(http_requests_total{status_code=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100
```

### Elasticsearch Query DSL

**Find Errors in a Time Range:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"range": {"@timestamp": {"gte": "now-1h", "lt": "now"}}},
        {"match": {"level": "ERROR"}}
      ]
    }
  },
  "sort": [{"@timestamp": {"order": "desc"}}]
}
```

**Find All Logs for a Trace:**
```json
{
  "query": {
    "match": {
      "trace_id": "67d4bde511f84f1488ea608c27afb093"
    }
  },
  "sort": [{"@timestamp": {"order": "asc"}}]
}
```

## Jaeger Query

**Find Traces with High Latency:**
Filter options:
- Service: "api"
- Operation: "GET /demo/items"
- Duration: "> 500ms"
- Tags: 
  - "http.status_code=500"
  - "error=true"

## Troubleshooting

### Missing Metrics

If metrics are not appearing in Prometheus:
1. Check the Prometheus target status at `http://localhost:9091/targets`
2. Verify the API service is exposing metrics at `/metrics`
3. Confirm the scrape configuration in prometheus.yml

### Missing Logs

If logs are not appearing in Kibana:
1. Check Logstash is receiving logs: `docker-compose logs logstash`
2. Verify Elasticsearch indices: `curl -X GET "http://localhost:9200/_cat/indices"`
3. Check Kibana index patterns are configured

### Missing Traces

If traces are not appearing in Jaeger:
1. Verify the tracer is properly initialized in the API
2. Check Jaeger collector logs: `docker-compose logs jaeger`
3. Ensure trace sampling is enabled 