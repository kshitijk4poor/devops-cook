#!/usr/bin/env python3

import random
import time
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="Mock API", description="Mock API for load testing")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_random_latency(request: Request, call_next):
    """Add some random latency to simulate real-world conditions"""
    # 10% of requests get high latency (100-300ms)
    if random.random() < 0.1:
        time.sleep(random.uniform(0.1, 0.3))
    # 20% of requests get medium latency (50-100ms)
    elif random.random() < 0.2:
        time.sleep(random.uniform(0.05, 0.1))
    # Rest get low latency (10-50ms)
    else:
        time.sleep(random.uniform(0.01, 0.05))
    
    response = await call_next(request)
    return response

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}

@app.get("/api/v1/items")
async def get_items():
    """Return a list of items"""
    items = [
        {"id": i, "name": f"Item {i}", "description": f"This is item {i}"} 
        for i in range(1, random.randint(5, 20))
    ]
    return {"items": items}

@app.get("/api/v1/items/{item_id}")
async def get_item(item_id: int):
    """Return a specific item"""
    # Simulate a 404 for certain IDs
    if item_id % 10 == 0:
        return Response(status_code=404, content="Item not found")
    
    return {
        "id": item_id,
        "name": f"Item {item_id}",
        "description": f"This is item {item_id}",
        "details": {
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-02T00:00:00Z",
            "tags": ["tag1", "tag2", "tag3"][:random.randint(1, 3)]
        }
    }

@app.post("/api/v1/items")
async def create_item(request: Request):
    """Create a new item"""
    try:
        # Simulate item creation
        body = await request.json()
        new_id = random.randint(1000, 9999)
        
        # Simulate errors for invalid input
        if not body.get("name"):
            return Response(status_code=400, content="Missing required field: name")
        
        return {
            "id": new_id,
            "name": body.get("name"),
            "description": body.get("description", ""),
            "created": True
        }
    except Exception as e:
        return Response(status_code=400, content=f"Invalid input: {str(e)}")

@app.put("/api/v1/items/{item_id}")
async def update_item(item_id: int, request: Request):
    """Update an existing item"""
    try:
        # Simulate a 404 for certain IDs
        if item_id % 10 == 0:
            return Response(status_code=404, content="Item not found")
        
        body = await request.json()
        
        return {
            "id": item_id,
            "name": body.get("name", f"Item {item_id}"),
            "description": body.get("description", f"This is item {item_id}"),
            "updated": True
        }
    except Exception as e:
        return Response(status_code=400, content=f"Invalid input: {str(e)}")

@app.delete("/api/v1/items/{item_id}")
async def delete_item(item_id: int):
    """Delete an item"""
    # Simulate a 404 for certain IDs
    if item_id % 10 == 0:
        return Response(status_code=404, content="Item not found")
    
    # 5% of delete operations fail with a 500 error
    if random.random() < 0.05:
        return Response(status_code=500, content="Internal server error during deletion")
    
    return {"id": item_id, "deleted": True}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080) 