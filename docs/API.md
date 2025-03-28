# API Documentation

This document describes the endpoints exposed by our FastAPI backend service.

## Base URL

All API endpoints are accessible under the base URL: `http://localhost:8001`

## Authentication

Authentication is not currently implemented in this demo version. In a production environment, proper authentication mechanisms (JWT, OAuth, etc.) would be required.

## Endpoints

### Health Check

```
GET /health
```

Returns the current health status of the API service.

**Response:**
```json
{
  "status": "healthy"
}
```

**Status Codes:**
- 200 OK: Service is healthy

### Demo Endpoints

#### Get All Items

```
GET /demo/items
```

Returns a list of all items.

**Response:**
```json
[
  {
    "id": 1,
    "name": "Item 1",
    "description": "Description for Item 1"
  },
  {
    "id": 2,
    "name": "Item 2",
    "description": "Description for Item 2"
  }
]
```

**Status Codes:**
- 200 OK: Successful operation

#### Get Item by ID

```
GET /demo/items/{item_id}
```

Returns a specific item by ID.

**Path Parameters:**
- `item_id` (integer): The ID of the item to retrieve

**Response:**
```json
{
  "id": 1,
  "name": "Item 1",
  "description": "Description for Item 1"
}
```

**Status Codes:**
- 200 OK: Successful operation
- 404 Not Found: Item not found

#### Create New Item

```
POST /demo/items
```

Creates a new item.

**Request Body:**
```json
{
  "name": "New Item",
  "description": "Description for the new item"
}
```

**Response:**
```json
{
  "id": 3,
  "name": "New Item",
  "description": "Description for the new item"
}
```

**Status Codes:**
- 201 Created: Item created successfully
- 400 Bad Request: Invalid input

#### Delete Item

```
DELETE /demo/items/{item_id}
```

Deletes an item by ID.

**Path Parameters:**
- `item_id` (integer): The ID of the item to delete

**Response:**
```json
{
  "message": "Item deleted successfully"
}
```

**Status Codes:**
- 200 OK: Item deleted successfully
- 404 Not Found: Item not found

### Error Simulation Endpoints

These endpoints are used to simulate various error scenarios for testing observability features.

#### Simulate 500 Error

```
GET /demo/error
```

Simulates an internal server error.

**Status Codes:**
- 500 Internal Server Error: Simulated error

#### Simulate Slow Response

```
GET /demo/slow
```

Simulates a slow API response.

**Query Parameters:**
- `delay` (integer, optional): Delay in seconds (default: 5)

**Response:**
```json
{
  "message": "Response after delay",
  "delay_seconds": 5
}
```

**Status Codes:**
- 200 OK: Response after simulated delay

## Metrics Endpoint

```
GET /metrics
```

Provides Prometheus-compatible metrics for the API service.

**Response:**
Raw text format suitable for Prometheus scraping, containing metrics like:
- Request counts by endpoint
- Response time percentiles
- Error rates

## Usage Examples

### Using curl

Get all items:
```bash
curl -X GET http://localhost:8001/demo/items
```

Create a new item:
```bash
curl -X POST http://localhost:8001/demo/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Item", "description": "This is a test item"}'
```

### Using Python requests

```python
import requests

# Get an item by ID
response = requests.get("http://localhost:8001/demo/items/1")
item = response.json()
print(item)

# Simulate a slow response
response = requests.get("http://localhost:8001/demo/slow?delay=3")
print(response.json())
``` 