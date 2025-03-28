# Load Testing Suite

This directory contains a comprehensive load testing suite for testing the API service using Locust. The suite includes scripts for both running the tests and visualizing the results.

## Directory Structure

```
load_tests/
├── locustfile.py            # Main Locust configuration
├── mock_api.py              # Mock API server for testing
├── requirements.txt         # Python dependencies
├── README.md                # This file
├── run_tests.sh             # Test execution script 
├── visualize_results.py     # Results visualization script
├── results/                # Test result data (CSV)
├── reports/                # Generated test reports
└── scenarios/              # Test scenarios
    ├── basic_flow.py       # Normal endpoint usage
    ├── error_scenario.py   # Error-prone endpoint testing
    └── mixed_scenario.py   # Realistic mixed traffic pattern
```

## Prerequisites

- Python 3.10+
- pip (Python package manager)
- Virtual environment (recommended)

## Installation

1. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Using the Mock API Server

The `mock_api.py` script provides a simple mock API server that can be used for load testing if the actual API service is not available or if you want to test in isolation.

To start the mock API server:

```bash
./mock_api.py
```

This will start a FastAPI server on http://localhost:8000 with the following endpoints:
- `GET /health` - Health check endpoint
- `GET /api/v1/items` - Get a list of items
- `GET /api/v1/items/{item_id}` - Get a specific item
- `POST /api/v1/items` - Create a new item
- `PUT /api/v1/items/{item_id}` - Update an existing item
- `DELETE /api/v1/items/{item_id}` - Delete an item

The mock server includes realistic behavior like random latency and occasional errors to simulate real-world conditions.

## Running Load Tests

There are two ways to run the load tests:

### 1. Using the UI

Start Locust with the UI:

```bash
locust -f locustfile.py --host=http://localhost:8000
```

Then open your browser at http://localhost:8089 to access the Locust web interface.

### 2. Headless Mode

Run tests without the UI for automated testing:

```bash
locust -f locustfile.py --host=http://localhost:8000 --headless -u 100 -r 10 -t 5m
```

Parameters:
- `-u 100`: Simulate 100 users
- `-r 10`: Spawn 10 users per second
- `-t 5m`: Run for 5 minutes

## Test Scenarios

The load test includes different user classes that simulate various load patterns:

1. **LightLoadUser**: Simulates light load with longer wait times (weight: 3)
2. **MediumLoadUser**: Simulates medium load with standard wait times (weight: 2)
3. **HeavyLoadUser**: Simulates heavy load with shorter wait times (weight: 1)

Each user type performs the following tasks with different frequencies:
- Check API health (highest frequency)
- Get list of items (high frequency)
- Get single item (medium frequency)
- Create item (low frequency)
- Update item (low frequency)
- Delete item (low frequency)

## Visualizing Results

After running the tests, you can visualize the results using the provided script:

```bash
./visualize_results.py <path_to_csv_results>
```

This will generate charts showing:
- Response times over time
- Request rates
- Error rates
- Distribution of response times

## Grafana Integration

The load testing metrics can be viewed in Grafana using the Prometheus data source configured in the main project. The metrics include:
- Request rates
- Response times (min, max, median, 95th percentile)
- Error rates
- User count

## Customizing Tests

To customize the tests:

1. **Change User Behavior**: Edit the task methods in `locustfile.py` to modify how users interact with the API.
2. **Adjust Load Parameters**: Modify the weights and wait times of the different user classes.
3. **Add New Scenarios**: Create new user classes that inherit from `HttpUser` to simulate different user behaviors.

## Best Practices

- Start with a small number of users and gradually increase the load
- Monitor system resources during testing to identify bottlenecks
- Run tests regularly as part of your CI/CD pipeline
- Compare results between test runs to track performance changes
- Use distributed mode for high-load testing across multiple machines