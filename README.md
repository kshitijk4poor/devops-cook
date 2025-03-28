# API Observability Platform

This project demonstrates a comprehensive API observability solution using modern tools and techniques. It provides monitoring, logging, tracing, and visualization capabilities for a FastAPI application.

## Components

- **FastAPI Application**: A demo API with various endpoints that simulate different scenarios
- **Prometheus**: For metrics collection and storage
- **Grafana**: For metrics visualization and dashboards
- **OpenTelemetry & Jaeger**: For distributed tracing
- **ELK Stack**: For log aggregation and analysis
  - **Elasticsearch**: Log storage and indexing
  - **Logstash**: Log processing pipeline
  - **Kibana**: Log visualization

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.11+

### Installation

1. Clone the repository
2. Run `docker-compose up -d` to start all services
3. Access the various dashboards:
   - API: http://localhost:8001
   - Prometheus: http://localhost:9091
   - Grafana: http://localhost:3000
   - Kibana: http://localhost:5601
   - Jaeger UI: http://localhost:16686

## Observability Components

### 1. Metrics with Prometheus & Grafana

The API is instrumented with Prometheus metrics that track:
- Request counts by endpoint and status code
- Response times (histograms with percentiles)
- Error rates and exception counts
- Custom application metrics
- System metrics (CPU, memory, network)

#### Using Prometheus

1. Access the Prometheus UI at http://localhost:9091
2. Use PromQL to query metrics:
   - `http_request_duration_seconds_count` - Total number of requests
   - `http_request_duration_seconds_bucket` - Request duration histograms
   - `http_requests_total{status="500"}` - Count of 500 error responses
   - `process_resident_memory_bytes` - Memory usage

#### Using Grafana

1. Access Grafana at http://localhost:3000 (login: admin/admin)
2. Prometheus is already configured as a data source
3. Explore pre-built dashboards:
   - **API Overview**: General health and performance metrics
   - **Endpoint Performance**: Detailed per-endpoint metrics
   - **Error Analysis**: Focus on error patterns and rates

#### Custom Metrics

The API exposes custom business metrics:
- `api_db_operation_duration_seconds`: Database operation timing
- `api_external_request_duration_seconds`: External API call timing
- `api_business_metrics`: Custom domain-specific metrics

### 2. Logging with ELK Stack

The API uses structured JSON logging with context enrichment:

#### Log Structure

```json
{
  "timestamp": "2023-07-20T15:04:05.123Z",
  "level": "INFO",
  "logger": "app.routes.demo",
  "message": "Request processed successfully",
  "request_id": "a1b2c3d4",
  "method": "GET",
  "path": "/demo/random",
  "status_code": 200,
  "duration_ms": 45,
  "additional_context": {...}
}
```

#### Using Kibana

1. Access Kibana at http://localhost:5601
2. Navigate to "Discover" to search and filter logs
3. Sample queries:
   - `status_code:500`: Find error responses
   - `duration_ms>500`: Find slow requests
   - `path:"/demo/random"`: Find specific endpoint logs

#### Pre-built Dashboards

Kibana includes pre-configured dashboards:
- **API Overview**: General API activity and health
- **Error Analysis**: Detailed view of error patterns
- **Performance Tracking**: Response time analysis

#### Testing Logs

Generate test logs using the provided script:
```bash
./test_elk.sh
```

### 3. Distributed Tracing with OpenTelemetry & Jaeger

The API is instrumented with OpenTelemetry to provide distributed tracing:

#### Trace Structure

- Each API request creates a parent span
- Operations like database queries and external API calls create child spans
- Spans contain attributes like:
  - HTTP method, URL, and status code
  - Database query parameters
  - Error information
  - Business context

#### Using Jaeger UI

1. Access Jaeger at http://localhost:16686
2. Search for traces by:
   - Service: "fastapi"
   - Operation: Endpoint name (e.g., "/demo/random")
   - Tags: Filter by attributes like status_code
   - Duration: Find slow traces

#### Analyzing Traces

- View the complete request flow, including nested operations
- Identify performance bottlenecks 
- Correlate traces with logs using the request_id
- Understand error propagation across services

### 4. Unified Observability

#### Correlation Between Systems

All observability data is linked through common identifiers:
- `request_id`: Connects logs and traces
- `timestamp`: Allows time-based correlation
- `endpoint`: Groups metrics, logs, and traces by functionality

#### Troubleshooting Workflows

1. **Metrics-First Approach**:
   - Start with Grafana dashboards to identify anomalies
   - Drill down to specific time periods and endpoints
   - Pivot to logs or traces for detailed investigation

2. **Logs-First Approach**:
   - Search for errors or patterns in Kibana
   - Extract request_ids from interesting logs
   - Find corresponding traces in Jaeger

3. **Trace-First Approach**:
   - Analyze slow or error traces in Jaeger
   - Understand the full request context
   - Examine detailed logs for each span

## Demo Endpoints

The API provides several endpoints to test observability features:

- `/health`: Simple health check endpoint
- `/demo/random`: Returns random numbers with trace context
- `/demo/metrics`: Returns simulated metrics data
- `/demo/echo`: Echoes back JSON payloads
- `/demo/data-echo`: Returns a fixed JSON response (good for testing)
- `/demo/slow`: Simulates slow responses with random delays
- `/demo/simple-error`: Endpoint that can generate errors on demand
- `/demo/external/{error}`: Simulates external API calls with optional errors

## Future Considerations

### Unified Dashboarding

Currently, metrics and logs are visualized in separate systems (Grafana for metrics, Kibana for logs). For a unified observability experience, consider:

- **Adding Elasticsearch as a Grafana Data Source**: This would allow visualizing logs alongside metrics in Grafana dashboards, providing a single pane of glass for all observability data.
- **Creating Combined Dashboards**: Build Grafana dashboards that show correlated metrics and logs for easier troubleshooting.
- **Implementing Alerts**: Set up alerts in Grafana based on both metrics and log patterns.

This integration would eliminate the need to switch between Grafana and Kibana when investigating issues, streamlining the monitoring and troubleshooting workflow.

## Testing

Run the included test script to verify the ELK stack and observability setup:

```bash
./test_elk.sh
```

This will check the health of all services and generate test logs and traces.

## Troubleshooting

### Common Issues

#### Services Not Starting

If any service fails to start:
1. Check the logs: `docker-compose logs [service-name]`
2. Verify port availability: `netstat -an | grep [port]`
3. Check resource constraints (memory/CPU)

#### Missing Data in Observability Tools

1. **No metrics in Prometheus**:
   - Verify the API is running: `curl http://localhost:8001/health`
   - Check Prometheus targets: http://localhost:9091/targets
   - Verify scrape configuration in prometheus.yml

2. **No logs in Kibana**:
   - Verify Logstash is receiving logs: `curl http://localhost:9600`
   - Check Elasticsearch indices: `curl http://localhost:9200/_cat/indices`
   - Generate test logs: `python tests/generate_logs.py --count 10`

3. **No traces in Jaeger**:
   - Verify Jaeger collector is running: `curl http://localhost:14268/`
   - Check environment variables for OpenTelemetry in docker-compose
   - Generate traffic with demo endpoints: `curl http://localhost:8001/demo/random`

#### Container Modifications Not Taking Effect

If your code changes aren't reflected in the running container:
1. Check if the code is mounted as a volume or built into the image
2. For mounted volumes, changes should apply immediately
3. For built images, you need to rebuild: `docker-compose build api`
4. Restart the container: `docker restart atlan-devop-api-1`

### Data Not Persisting

If your observability data disappears after restarts:
1. Check volume configuration in docker-compose.yml
2. Verify persistence settings in Elasticsearch, Prometheus

### Performance Issues

If you experience slow performance:
1. Check resource allocation for containers
2. Monitor container stats: `docker stats`
3. Review sampling rates for tracing
4. Consider scaling Elasticsearch/Prometheus for production deployments

## Security and Production Considerations

This platform is set up as a demonstration environment. For production deployments, consider these additional measures:

### Security Enhancements

1. **Authentication & Authorization**:
   - Enable authentication for all observability tools
   - Set up proper user management and role-based access
   - Replace default credentials (particularly in Grafana and Kibana)

2. **Network Security**:
   - Restrict access to observability tools with proper network policies
   - Use TLS for all communications
   - Consider placing tools behind a reverse proxy with proper access controls

3. **Data Protection**:
   - Implement data retention policies for logs and metrics
   - Consider data anonymization for sensitive information in logs
   - Review what is being captured in traces to avoid leaking sensitive data

### Production Readiness

1. **High Availability**:
   - Set up clustered deployments for Elasticsearch
   - Configure Prometheus for high availability
   - Use load balancing for ingest components

2. **Resource Planning**:
   - Size containers based on expected traffic and data retention
   - Set up resource limits and requests for all containers
   - Monitor resource usage and scale accordingly

3. **Backup & Recovery**:
   - Implement regular backups for Elasticsearch and Prometheus
   - Document disaster recovery procedures
   - Test recovery scenarios regularly

4. **Monitoring the Monitoring**:
   - Set up alerts for the health of your observability tools
   - Monitor disk space for data stores
   - Create dashboards for observability platform metrics

### Compliance Considerations

Depending on your industry and location, consider:
- Data retention limitations
- Privacy requirements (GDPR, CCPA, etc.)
- Audit trail requirements
- Data residency concerns

By addressing these considerations, you can transform this demonstration environment into a production-ready observability platform suitable for critical applications. 