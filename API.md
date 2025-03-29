# API Documentation

This document provides detailed information about the API endpoints available in the API Observability Platform.

## Table of Contents
1. [Authentication](#authentication)
2. [API Endpoints](#api-endpoints)
3. [Request/Response Formats](#request-response-formats)
4. [Error Handling](#error-handling)
5. [Rate Limiting](#rate-limiting)
6. [Example Usage](#example-usage)

## Authentication

The API uses OAuth2 for authentication with JWT tokens.

### Obtaining a Token

```bash
curl -X POST http://localhost:8001/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&username=user@example.com&password=yourpassword"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Using the Token

Include the token in the Authorization header for all API requests:

```bash
curl -X GET http://localhost:8001/api/v1/items \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## API Endpoints

| Endpoint | Method | Description | Authentication |
|----------|--------|-------------|----------------|
| `/api/v1/health` | GET | Health check endpoint | No |
| `/api/v1/items` | GET | List all items | Yes |
| `/api/v1/items/{id}` | GET | Get item by ID | Yes |
| `/api/v1/items` | POST | Create a new item | Yes |
| `/api/v1/items/{id}` | PUT | Update an item | Yes |
| `/api/v1/items/{id}` | DELETE | Delete an item | Yes |
| `/api/v1/users` | GET | List all users | Yes (Admin) |
| `/api/v1/metrics` | GET | Get application metrics | Yes (Admin) |

### Detailed Endpoint Documentation

#### Health Check

```
GET /api/v1/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": "2d 3h 45m"
}
```

#### List Items

```
GET /api/v1/items
```

Query Parameters:
- `page` (int): Page number for pagination (default: 1)
- `limit` (int): Number of items per page (default: 10)
- `sort` (string): Field to sort by (default: "created_at")
- `order` (string): Sort order, "asc" or "desc" (default: "desc")

Response:
```json
{
  "items": [
    {
      "id": "1",
      "name": "Example Item",
      "description": "This is an example item",
      "created_at": "2023-01-01T12:00:00Z",
      "updated_at": "2023-01-02T14:30:00Z"
    },
    ...
  ],
  "total": 100,
  "page": 1,
  "limit": 10,
  "pages": 10
}
```

#### Get Item by ID

```
GET /api/v1/items/{id}
```

Path Parameters:
- `id` (string): The unique identifier of the item

Response:
```json
{
  "id": "1",
  "name": "Example Item",
  "description": "This is an example item",
  "created_at": "2023-01-01T12:00:00Z",
  "updated_at": "2023-01-02T14:30:00Z",
  "metadata": {
    "owner": "user123",
    "tags": ["example", "demo"]
  }
}
```

#### Create Item

```
POST /api/v1/items
```

Request Body:
```json
{
  "name": "New Item",
  "description": "This is a new item",
  "metadata": {
    "tags": ["new", "example"]
  }
}
```

Response:
```json
{
  "id": "2",
  "name": "New Item",
  "description": "This is a new item",
  "created_at": "2023-01-03T09:15:00Z",
  "updated_at": "2023-01-03T09:15:00Z",
  "metadata": {
    "owner": "current-user",
    "tags": ["new", "example"]
  }
}
```

## Request/Response Formats

All API endpoints accept and return JSON data. The content type for requests should be set to `application/json`, and responses will have the same content type.

### Common Response Structure

All responses follow this general structure:

```json
{
  "data": {
    // Response data specific to the endpoint
  },
  "meta": {
    "timestamp": "2023-01-03T12:34:56Z",
    "request_id": "req-123456"
  },
  "links": {
    "self": "http://localhost:8001/api/v1/items/1",
    "next": "http://localhost:8001/api/v1/items?page=2"
  }
}
```

## Error Handling

When an error occurs, the API returns an appropriate HTTP status code along with a JSON response containing error details.

### Error Response Format

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested resource could not be found",
    "details": "Item with ID '999' does not exist"
  },
  "meta": {
    "timestamp": "2023-01-03T12:34:56Z",
    "request_id": "req-123456"
  }
}
```

### Common Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | INVALID_REQUEST | Invalid request format or parameters |
| 401 | UNAUTHORIZED | Authentication required or invalid credentials |
| 403 | FORBIDDEN | Insufficient permissions |
| 404 | RESOURCE_NOT_FOUND | Requested resource not found |
| 409 | CONFLICT | Resource conflict (e.g., duplicate entry) |
| 422 | VALIDATION_ERROR | Validation error in request data |
| 429 | RATE_LIMIT_EXCEEDED | Too many requests |
| 500 | SERVER_ERROR | Internal server error |

## Rate Limiting

The API implements rate limiting to protect against abuse. Rate limits are applied per client IP address and API key.

### Rate Limit Headers

The following headers are included in API responses:

- `X-RateLimit-Limit`: Maximum requests allowed in the current time window
- `X-RateLimit-Remaining`: Remaining requests in the current time window
- `X-RateLimit-Reset`: Time (in UTC seconds) when the current rate limit window resets

### Rate Limit Tiers

| Tier | Rate Limit |
|------|------------|
| Anonymous | 60 requests per hour |
| Basic | 1000 requests per hour |
| Premium | 10000 requests per hour |

## Example Usage

### Python Example

```python
import requests
import json

# Authenticate and get token
auth_response = requests.post(
    "http://localhost:8001/auth/token",
    data={
        "grant_type": "password",
        "username": "user@example.com",
        "password": "yourpassword"
    }
)
token = auth_response.json()["access_token"]

# Get list of items
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
response = requests.get("http://localhost:8001/api/v1/items", headers=headers)
items = response.json()["data"]["items"]

# Create a new item
new_item = {
    "name": "API Created Item",
    "description": "This item was created via the API",
    "metadata": {
        "tags": ["api", "example"]
    }
}
create_response = requests.post(
    "http://localhost:8001/api/v1/items",
    headers=headers,
    data=json.dumps(new_item)
)
created_item = create_response.json()["data"]
print(f"Created item with ID: {created_item['id']}")
```

### JavaScript Example

```javascript
async function apiExample() {
  // Authenticate and get token
  const authResponse = await fetch("http://localhost:8001/auth/token", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded"
    },
    body: "grant_type=password&username=user@example.com&password=yourpassword"
  });
  const authData = await authResponse.json();
  const token = authData.access_token;
  
  // Get list of items
  const headers = {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json"
  };
  
  const itemsResponse = await fetch("http://localhost:8001/api/v1/items", {
    headers
  });
  const itemsData = await itemsResponse.json();
  const items = itemsData.data.items;
  
  // Create a new item
  const newItem = {
    name: "API Created Item",
    description: "This item was created via the API",
    metadata: {
      tags: ["api", "example"]
    }
  };
  
  const createResponse = await fetch("http://localhost:8001/api/v1/items", {
    method: "POST",
    headers,
    body: JSON.stringify(newItem)
  });
  
  const createdItem = await createResponse.json();
  console.log(`Created item with ID: ${createdItem.data.id}`);
}

apiExample().catch(console.error);
``` 