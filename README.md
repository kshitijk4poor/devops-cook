# API Observability Platform

This project demonstrates a comprehensive API observability solution using modern tools and techniques. It provides monitoring, logging, and visualization capabilities for a FastAPI application.

## Components

- **FastAPI Application**: A demo API with various endpoints that simulate different scenarios
- **Prometheus**: For metrics collection and storage
- **Grafana**: For metrics visualization and dashboards
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

## Features

### Metrics Monitoring

The API is instrumented with Prometheus metrics that track:
- Request counts
- Response times
- Error rates
- Custom application metrics

### Log Management

Structured logging is implemented with:
- JSON formatting
- Request correlation IDs
- Automatic log forwarding to ELK
- Log visualization in Kibana

### Demo Endpoints

- `/health`: Simple health check endpoint
- `/demo/random`: Returns random numbers
- `/demo/metrics`: Returns simulated metrics data
- `/demo/echo`: Echoes back JSON payloads
- `/demo/simple-error`: Endpoint that can generate errors on demand

## Future Considerations

### Unified Dashboarding

Currently, metrics and logs are visualized in separate systems (Grafana for metrics, Kibana for logs). For a unified observability experience, consider:

- **Adding Elasticsearch as a Grafana Data Source**: This would allow visualizing logs alongside metrics in Grafana dashboards, providing a single pane of glass for all observability data.
- **Creating Combined Dashboards**: Build Grafana dashboards that show correlated metrics and logs for easier troubleshooting.
- **Implementing Alerts**: Set up alerts in Grafana based on both metrics and log patterns.

This integration would eliminate the need to switch between Grafana and Kibana when investigating issues, streamlining the monitoring and troubleshooting workflow.

## Testing

Run the included test script to verify the ELK stack setup:

```bash
./test_elk.sh
```

This will check the health of all services and generate some test logs. 