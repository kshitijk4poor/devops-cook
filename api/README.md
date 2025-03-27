# API Observability Platform

A FastAPI-based platform for API observability, monitoring, and debugging.

## Features

- RESTful API with FastAPI
- Health check endpoint
- Containerized with Docker
- Configuration management
- Testing with pytest

## Getting Started

### Prerequisites

- Python 3.9+
- pip
- Docker (optional)

### Installation

1. Clone the repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the API

#### Development mode:

```bash
uvicorn app.main:app --reload
```

#### Production mode:

```bash
uvicorn app.main:app
```

### Docker

Build and run with Docker:

```bash
docker build -t api-observability .
docker run -p 8000:8000 api-observability
```

## API Documentation

Once the application is running, you can access:

- API documentation: http://localhost:8000/docs
- ReDoc documentation: http://localhost:8000/redoc

## Testing

Run tests with pytest:

```bash
pytest
```

## Project Structure

```
api/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py
│   └── routes/
│       ├── __init__.py
│       └── health.py
├── tests/
│   ├── __init__.py
│   └── test_health.py
├── Dockerfile
├── requirements.txt
└── README.md
```
