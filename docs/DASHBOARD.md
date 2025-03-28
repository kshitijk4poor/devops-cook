# Dashboard Usage Guide

This guide explains how to use the various dashboards provided in the observability platform.

> Note: All diagrams are available in both Mermaid (.mmd) format for interactive viewing and PNG format for static viewing. To generate PNG images from Mermaid files, run `./scripts/generate_images.sh`.

## Grafana Dashboards

Grafana provides metric visualizations through a series of pre-configured dashboards.

### Sample Metrics Dashboard

![Metrics Dashboard](images/metrics_dashboard.mmd)

### Access Grafana

1. Open your browser and navigate to http://localhost:3000
2. Log in with the default credentials:
   - Username: admin
   - Password: admin

### Available Dashboards

#### API Overview Dashboard

This dashboard provides a high-level overview of API performance and health.

**Key Panels:**
- Request Rate: The number of requests per second
- Error Rate: Percentage of requests resulting in errors
- Response Time: Average and percentile (50th, 90th, 99th) response times
- Status Code Distribution: Breakdown of responses by HTTP status code

**Usage:**
1. Navigate to Dashboards > API Overview
2. Use the time range selector at the top-right to adjust the view period
3. Filter by endpoint using the dropdown filters

#### System Metrics Dashboard

This dashboard displays system-level metrics for the API service.

**Key Panels:**
- CPU Usage: CPU utilization percentage
- Memory Usage: Memory consumption trends
- Disk I/O: Disk read/write operations
- Network Traffic: Inbound and outbound network traffic

**Usage:**
1. Navigate to Dashboards > System Metrics
2. Select the instance you want to monitor (if running multiple instances)

### Creating Custom Dashboards

To create a custom dashboard:

1. Click the "+" icon on the left sidebar
2. Select "Dashboard"
3. Add panels by clicking "Add panel"
4. Configure each panel with PromQL queries
5. Save the dashboard with a descriptive name

## Kibana Log Explorer

Kibana provides powerful log searching and visualization capabilities.

### Sample Log Explorer View

![Kibana Log Explorer](images/log_explorer.mmd)

### Access Kibana

1. Open your browser and navigate to http://localhost:5601
2. No login is required in the demo setup

### Log Exploration

#### Search Logs

**Basic Search:**
1. Navigate to Discover > Logs
2. Enter search terms in the search bar
3. Use the time picker to select the relevant time range

**Advanced Search with KQL (Kibana Query Language):**
```
level:ERROR AND message:*timeout*
```

**Common KQL Examples:**
- Find error logs: `level:ERROR`
- Find logs from a specific endpoint: `req.url:"/demo/items"`
- Find slow responses: `response_time:>500`
- Find logs for a specific trace: `trace_id:"abc123"`

#### Creating Visualizations

1. Navigate to Visualize
2. Click "Create visualization"
3. Select the visualization type (bar chart, line chart, etc.)
4. Configure the visualization with your data
5. Save and add to a dashboard

#### Log Patterns Dashboard

This dashboard shows common log patterns and anomalies.

**Key Panels:**
- Log Volume: Count of logs over time
- Error Rate: Percentage of error logs
- Top Endpoints: Most frequently accessed endpoints
- Slow Responses: Endpoints with the slowest response times

## Jaeger Trace Explorer

Jaeger provides distributed tracing visualization.

### Sample Trace View

![Jaeger Trace View](images/trace_view.mmd)

### Sample Trace Details

![Trace Details](images/trace_details.mmd)

### Access Jaeger

1. Open your browser and navigate to http://localhost:16686

### Trace Exploration

#### Search for Traces

1. Select the "api" service from the Service dropdown
2. Optionally select an Operation (endpoint)
3. Set the lookback period (e.g., "Last 1 hour")
4. Click "Find Traces"

#### Analyze a Trace

1. Click on a trace from the search results
2. View the trace timeline showing the duration of each span
3. Click on individual spans to see details:
   - Tags: Key-value metadata about the span
   - Logs: Events that occurred during the span
   - Process: Information about the service that generated the span

#### Understanding Trace Visualization

Traces are displayed as a hierarchy of spans:
- Root span: The top-level operation (usually the HTTP request)
- Child spans: Sub-operations (database queries, external API calls, etc.)
- Siblings: Operations that occur at the same level

**Color Coding:**
- Blue: Normal execution
- Red: Error occurred
- Yellow: Warning or slow execution

## Cross-Platform Navigation

The observability platform supports cross-navigation between tools:

### From Metrics to Logs

1. In Grafana, click on a spike in a metric graph
2. Select "View in Kibana"
3. Kibana will open with the corresponding time range selected

### From Logs to Traces

1. In Kibana, find a log entry with a trace_id
2. Click on the trace_id field
3. Select "View in Jaeger"
4. Jaeger will open showing the specific trace

## Sample Analysis Workflow

### Investigating an Error Spike

1. In Grafana, observe an increase in the error rate
2. Navigate to the corresponding logs in Kibana to identify the error type
3. Find a trace_id associated with an error
4. Examine the trace in Jaeger to pinpoint where the error occurred
5. Return to Grafana to correlate the error with system metrics

### Performance Optimization

1. Identify slow endpoints in Grafana's response time panels
2. View traces for slow requests in Jaeger
3. Analyze the time spent in each component
4. Focus optimization efforts on the most time-consuming spans 