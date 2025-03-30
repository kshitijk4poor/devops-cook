# Observability Stack

This document provides detailed information about the observability components integrated into the API Observability Platform.

## Executive Summary

Modern API platforms require comprehensive observability to maintain reliability and performance. This document explains:

- **What**: The core observability components (metrics, logs, traces)
- **How**: Their implementation in this platform
- **Why**: The specific design choices made
- **When**: Usage patterns for different scenarios

By understanding these elements, teams can effectively monitor, debug, and optimize their applications.

## Table of Contents
1. [Overview](#overview)
2. [Metrics](#metrics)
3. [Logging](#logging)
4. [Tracing](#tracing)
5. [Alerting](#alerting)
6. [Correlation](#correlation)
7. [Best Practices](#best-practices)
8. [Advanced Topics](#advanced-topics)

## Overview

The API Observability Platform follows the **three pillars of observability** approach:

1. **Metrics**: Numerical data points that provide system health and performance information
2. **Logs**: Detailed records of events that occurred in the system
3. **Traces**: Information about the path of a request through various components

These three components together provide a comprehensive view of the system's behavior and performance.

### Observability vs. Monitoring

It's important to distinguish between monitoring and observability:

- **Monitoring**: Watching known indicators for predefined problems
- **Observability**: Having enough context to understand previously unknown issues

This platform implements true observability by providing rich context and correlation between components.

## Metrics

### Metrics Collection

The platform uses Prometheus for metrics collection. Metrics are exposed by the FastAPI application using the `prometheus_client` library.

### Key Metrics

The following key metrics are collected:

#### Request Metrics
- `http_requests_total`: Total number of HTTP requests
  - **Why it matters**: Tracks traffic patterns and potential abnormal spikes
  - **Common patterns**: Day/night cycles, weekly patterns, event-driven spikes

- `http_request_duration_seconds`: HTTP request latency (seconds)
  - **Why it matters**: Primary indicator of user experience
  - **Alert thresholds**: Based on p95 values (typically 300-500ms)

#### Business Metrics
- `api_items_created_total`: Total number of items created
- `api_items_updated_total`: Total number of items updated
- `api_items_deleted_total`: Total number of items deleted
- `api_active_users`: Gauge for number of active users

#### System Metrics
- `process_cpu_seconds_total`: Total user and system CPU time spent in seconds
- `process_open_fds`: Number of open file descriptors
- `process_max_fds`: Maximum number of open file descriptors
- `process_virtual_memory_bytes`: Virtual memory size in bytes
- `process_resident_memory_bytes`: Resident memory size in bytes

#### Database Metrics
- `database_connections`: Number of active database connections
- `database_queries_total`: Total number of database queries
- `database_query_duration_seconds`: Database query latency (seconds)

### Metric Types

Prometheus supports four main metric types:

1. **Counter**: Cumulative metric that only increases (e.g., request count)
2. **Gauge**: Metric that can increase and decrease (e.g., memory usage)
3. **Histogram**: Samples observations and counts them in buckets (e.g., request duration)
4. **Summary**: Similar to histogram, but calculates quantiles over a sliding time window

### Sample Code for Custom Metrics

```python
from prometheus_client import Counter, Gauge, Histogram, Summary

# Counter example
item_counter = Counter(
    'api_items_created_total',
    'Total number of items created',
    ['item_type']
)

# Usage
item_counter.labels(item_type='standard').inc()

# Gauge example
active_users = Gauge(
    'api_active_users',
    'Number of active users'
)

# Usage
active_users.inc()  # Increment
active_users.dec()  # Decrement
active_users.set(15)  # Set to specific value

# Histogram example
request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration in seconds',
    ['endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# Usage with context manager
with request_duration.labels(endpoint='/api/v1/items').time():
    # Code to be measured
    process_request()

# Summary example
request_latency = Summary(
    'api_request_processing_seconds',
    'API request processing time in seconds',
    ['endpoint']
)

# Usage with decorator
@request_latency.labels(endpoint='/api/v1/items').time()
def process_request():
    # Process the request
    pass
```

### Metric Selection Philosophy

The metrics in this platform were carefully selected based on:

1. **Signal-to-noise ratio**: Each metric provides actionable information
2. **Performance impact**: Collection overhead is minimized
3. **Cardinality management**: Labels are designed to avoid explosion
4. **Aggregation potential**: Metrics can be meaningfully combined

This approach ensures that metrics provide maximum value while minimizing storage and query complexity.

### Advanced Prometheus Usage

Beyond basic metrics, this platform implements:

1. **Recording rules**: Pre-calculated expensive queries
2. **Custom histograms**: Tailored bucket boundaries for accurate percentiles
3. **Exemplars**: Links from metrics to traces for specific data points
4. **Multi-dimensional data**: Strategic use of labels for rich context

## Logging

### Log Collection

The platform uses the ELK stack (Elasticsearch, Logstash, Kibana) for log collection and analysis.

### Log Levels

- **ERROR**: Error events that might still allow the application to continue running
  - **When to use**: Application errors that require investigation
  - **Example**: Database connection failures, API validation errors

- **WARNING**: Potentially harmful situations that should be addressed
  - **When to use**: Issues that don't immediately impact users but need attention
  - **Example**: Deprecated API usage, resource threshold warnings

### Structured Logging

All logs are structured in JSON format to enable better searching and filtering. Each log entry contains:

- Timestamp
- Log level
- Message
- Service name
- Trace ID (for correlation with traces)
- Request ID
- User ID (if authenticated)
- Additional contextual information

### Sample Code for Structured Logging

```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "service": "api-service",
            "logger": record.name,
            "path": record.pathname,
            "line": record.lineno
        }
        
        # Add exception info if available
        if record.exc_info:
            log_record["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
            
        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key.startswith('_') or key in log_record:
                continue
            log_record[key] = value
            
        return json.dumps(log_record)

# Configure logger
logger = logging.getLogger("api")
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Usage example
logger.info("User logged in", extra={
    "user_id": "user123",
    "request_id": "req-456",
    "trace_id": "trace-789",
    "client_ip": "192.168.1.1"
})
```

### Log Shipping

Logs are shipped to Logstash using the Filebeat agent, which monitors log files and forwards them to Logstash. Logstash processes the logs and sends them to Elasticsearch for storage and indexing.

### Log Sampling Strategy

To manage high log volumes while preserving visibility:

1. **INFO logs**: Sampled at 10% during normal operation, 100% during issues
2. **ERROR logs**: Always captured at 100%
3. **DEBUG logs**: Dynamically enabled for specific components when needed
4. **High-volume endpoints**: Implement adaptive sampling based on traffic

This strategy ensures comprehensive visibility during issues while controlling storage costs.

## Tracing

### Distributed Tracing

The platform uses OpenTelemetry and Jaeger for distributed tracing. Tracing provides visibility into the full request lifecycle, from client to database and back.

### Span and Trace Concepts

- **Trace**: A trace represents the entire journey of a request through the system
- **Span**: A single operation within a trace (e.g., API call, database query)
- **Parent Span**: The operation that triggered one or more child operations
- **Child Span**: An operation triggered by a parent span
- **Span Context**: Information that identifies a span and its trace

### Trace Information

Each trace contains:
- Service name
- Operation name
- Timestamp
- Duration
- Tags (key-value pairs for search and filtering)
- Logs (time-stamped events during the span)
- References to parent spans

### Sample Code for Tracing

```python
from opentelemetry import trace
from opentelemetry.trace.status import Status, StatusCode
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

# Configure tracer
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Configure Jaeger exporter
jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831,
)

# Add span processor to tracer provider
span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Usage example
@app.get("/api/v1/items/{item_id}")
async def get_item(item_id: str):
    with tracer.start_as_current_span("get_item") as span:
        # Add attributes to the span
        span.set_attribute("item.id", item_id)
        
        try:
            # Create a child span for database operation
            with tracer.start_as_current_span("db_query") as db_span:
                db_span.set_attribute("db.query", f"SELECT * FROM items WHERE id = {item_id}")
                item = await database.fetch_one(f"SELECT * FROM items WHERE id = {item_id}")
                
                if not item:
                    span.set_status(Status(StatusCode.NOT_FOUND))
                    return {"error": "Item not found"}
                    
                return {"item": item}
        except Exception as e:
            # Record the error
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR))
            return {"error": str(e)}
```

## Alerting

The platform uses Grafana Alerting for configuring and managing alerts based on metric thresholds.

### Alert Types

1. **Threshold Alerts**: Trigger when a metric crosses a defined threshold
2. **Anomaly Alerts**: Trigger when a metric deviates significantly from normal behavior
3. **Absence Alerts**: Trigger when expected data is missing

### Alert Channels

Alerts can be sent through various channels:
- Email
- Slack
- PagerDuty
- Webhook

### Alert Rules Examples

```yaml
# High Error Rate Alert
groups:
  - name: api-alerts
    rules:
      - alert: HighErrorRate
        expr: sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High Error Rate"
          description: "Error rate is above 5% (current value: {{ $value }})"

# Service Latency Alert
      - alert: HighLatency
        expr: histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint)) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High Latency"
          description: "95th percentile latency is above 1s for endpoint {{ $labels.endpoint }}"

# Database Connection Alert
      - alert: HighDatabaseConnections
        expr: database_connections > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High Database Connections"
          description: "Database connections are above 80 (current value: {{ $value }})"
```

## Correlation

One of the most powerful features of the platform is the ability to correlate data across metrics, logs, and traces.

### Correlation Identifiers

Each request is assigned the following identifiers:

- **Request ID**: Unique identifier for each request
- **Trace ID**: Identifier for the trace in the distributed tracing system
- **User ID**: Identifier for the authenticated user (if applicable)

These identifiers are included in:
- HTTP response headers
- Log entries
- Span attributes
- Metrics labels

### Example Workflow

1. Notice an issue in a Grafana dashboard (high latency for a specific endpoint)
2. Drill down to find the requests with high latency
3. Use the trace ID to view the distributed trace in Jaeger
4. Identify which specific operation is causing the delay
5. Use the request ID to find related log entries in Kibana
6. Analyze the logs to understand the root cause

## Best Practices

### Metrics Best Practices

1. **Naming Convention**: Use a consistent naming pattern (e.g., `application_subsystem_operation_unit`)
2. **Labels**: Use labels for dimensions but avoid high cardinality
3. **Documentation**: Add clear metric descriptions
4. **Aggregation**: Ensure metrics can be meaningfully aggregated

### Logging Best Practices

1. **Structured Format**: Use JSON or another structured format
2. **Context**: Include enough context to understand the log
3. **Sensitive Data**: Never log sensitive information
4. **Log Levels**: Use appropriate log levels
5. **Rate Limiting**: Implement log rate limiting for high-volume events

### Tracing Best Practices

1. **Sampling**: Use appropriate sampling rates
2. **Naming**: Use consistent span naming conventions
3. **Attributes**: Add useful attributes but avoid excessive spans
4. **Error Handling**: Properly mark spans as errored
5. **Context Propagation**: Ensure trace context is propagated across services

### General Observability Principles

1. **Design for Observability**: Consider observability from the design phase
2. **SLOs/SLIs**: Define clear Service Level Objectives and Indicators
3. **USE Method**: Monitor Utilization, Saturation, and Errors for resources
4. **RED Method**: Monitor Rate, Errors, and Duration for services
5. **Correlation**: Ensure correlation between metrics, logs, and traces
6. **Actionable Alerts**: Create alerts that are actionable and avoid alert fatigue

## Advanced Topics

### Observability Testing

This platform includes tests to ensure observability components function correctly:

1. **Metric verification**: Tests that confirm metrics are exposed correctly
2. **Log validation**: Tests that validate log structure and content
3. **Trace completeness**: Tests that verify trace propagation
4. **Alert triggering**: Tests that confirm alerts fire correctly

### Cost Optimization

Observability can become expensive. This platform implements:

1. **Tiered storage**: Recent data in hot storage, older data in cold storage
2. **Intelligent sampling**: Adaptive sampling rates based on system state
3. **Retention policies**: Data lifecycle management across components
4. **Compression strategies**: Optimized storage formats for different data types

### Observability as Code

This platform treats observability as code:

1. **Version-controlled configuration**: All observability settings are in git
2. **Automated deployment**: Changes to dashboards deploy automatically
3. **Testable alerts**: Alert rules are tested in CI/CD pipelines
4. **Documentation generation**: Dashboards and alerts self-document

This approach ensures observability evolves alongside the application and remains maintainable.

### Business vs. Technical Observability

This platform bridges the gap between technical and business metrics:

1. **Business KPIs**: Key performance indicators tied to business outcomes
2. **User experience metrics**: Direct measures of user satisfaction
3. **SLOs/SLIs**: Clear service level objectives and indicators
4. **Cost attribution**: Resource usage mapped to business functions

By connecting technical metrics to business outcomes, the platform helps align engineering and business priorities 