# API Observability Platform

This platform demonstrates a comprehensive observability implementation for modern APIs, incorporating monitoring, logging, tracing, and alerting.

## Architecture Overview

The API Observability Platform consists of several interconnected services:

![Architecture Diagram](images/architecture.mmd)

- **FastAPI Backend**: The main application exposing REST endpoints
- **Prometheus**: Time-series database for metrics collection and storage
- **Grafana**: Visualization and dashboarding tool for metrics
- **Jaeger**: Distributed tracing system for request flow analysis
- **ELK Stack**: 
  - Elasticsearch: Document store for logs and events
  - Logstash: Log processing pipeline
  - Kibana: Log visualization and search interface

## Installation

### Prerequisites

- Docker and Docker Compose
- Git
- 4GB+ of available RAM

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/api-observability-platform.git
   cd api-observability-platform
   ```

2. Start all services:
   ```
   docker-compose up -d
   ```

3. Wait for all services to initialize (approximately 1-2 minutes)

4. Access the services:
   - API: http://localhost:8001
   - Grafana: http://localhost:3000 (default credentials: admin/admin)
   - Prometheus: http://localhost:9091
   - Kibana: http://localhost:5601
   - Jaeger UI: http://localhost:16686

## Configuration

Configuration files are available for each service:

- API: Dockerfile and requirements.txt
- Prometheus: prometheus.yml
- Grafana: grafana/provisioning/
- ELK Stack:
  - Elasticsearch: elasticsearch/elasticsearch.yml
  - Logstash: logstash/pipeline/
  - Kibana: kibana/dashboards/

## Testing

To run load tests:

```
python -m locust -f locustfile.py
```

## Troubleshooting

Common issues and solutions:

1. **Services not starting**: Check docker-compose logs with `docker-compose logs <service_name>`
2. **Memory issues**: Ensure you have sufficient memory allocated to Docker
3. **Port conflicts**: Verify no other services are using the required ports

## Extension Points

The platform can be extended in several ways:

1. Add custom metrics collectors
2. Implement additional alerting rules
3. Create custom Kibana dashboards
4. Develop service-specific tracers

## Documentation

For more detailed information, refer to the specific documentation:
- [API Documentation](API.md)
- [Observability Stack](OBSERVABILITY.md)
- [Dashboard Guide](DASHBOARD.md)

### Sample Visualizations

> Note: All diagrams are available in both Mermaid (.mmd) format for interactive viewing and PNG format for static viewing. To generate PNG images from Mermaid files, run `./scripts/generate_images.sh`.

#### Metrics Dashboard
![Metrics Dashboard](images/metrics_dashboard.mmd)

#### Trace View
![Jaeger Trace View](images/trace_view.mmd)

#### Log Explorer
![Kibana Log Explorer](images/log_explorer.mmd) 