#!/bin/bash

# Run load tests with Locust
# This script runs different load test scenarios

# Define colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Define test parameters
HOST="http://localhost:8000"
DURATION=60  # seconds
CSV_PREFIX="load_tests/results/$(date +"%Y%m%d_%H%M%S")"
USERS=10
SPAWN_RATE=2
HEADLESS_MODE=false
TEST_TYPE="all"  # Options: basic, error, mixed, all

# Parse command line arguments
while [ $# -gt 0 ]; do
  case "$1" in
    --host=*)
      HOST="${1#*=}"
      ;;
    --users=*)
      USERS="${1#*=}"
      ;;
    --spawn-rate=*)
      SPAWN_RATE="${1#*=}"
      ;;
    --duration=*)
      DURATION="${1#*=}"
      ;;
    --headless)
      HEADLESS_MODE=true
      ;;
    --type=*)
      TEST_TYPE="${1#*=}"
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --host=URL             Target host URL (default: $HOST)"
      echo "  --users=N              Number of users (default: $USERS)"
      echo "  --spawn-rate=N         User spawn rate (default: $SPAWN_RATE)"
      echo "  --duration=N           Test duration in seconds (default: $DURATION)"
      echo "  --headless             Run in headless mode"
      echo "  --type=TYPE            Test type (basic, error, mixed, all)"
      echo "  --help                 Show this help"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
  shift
done

# Create results directory if it doesn't exist
mkdir -p load_tests/results

# Check if API is running
echo -e "${YELLOW}Checking if API is running at $HOST...${NC}"
if curl -s "$HOST/api/v1/health" > /dev/null; then
    echo -e "${GREEN}API is running.${NC}"
else
    echo -e "${RED}API is not running at $HOST${NC}"
    echo -e "${YELLOW}Please start the API before running load tests.${NC}"
    exit 1
fi

# Install dependencies if needed
if ! pip list | grep -q "locust"; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install -r load_tests/requirements.txt
    echo -e "${GREEN}Dependencies installed.${NC}"
fi

# Function to run a specific test scenario
run_test() {
    local scenario=$1
    local user_class=$2
    
    echo -e "${YELLOW}Running $scenario load test...${NC}"
    
    # Set up command
    local cmd="locust"
    cmd+=" --host=$HOST"
    
    if [ "$HEADLESS_MODE" = true ]; then
        # Headless mode command
        cmd+=" --headless"
        cmd+=" --users=$USERS"
        cmd+=" --spawn-rate=$SPAWN_RATE"
        cmd+=" --run-time=${DURATION}s"
        cmd+=" --csv=${CSV_PREFIX}_${scenario}"
    fi
    
    # Add user class filter
    cmd+=" --class-picker"
    cmd+=" --user-classes=$user_class"
    
    # Run the test
    echo -e "${YELLOW}Command: $cmd${NC}"
    $cmd
    
    echo -e "${GREEN}$scenario test completed.${NC}"
    echo
}

# Main testing logic
case "$TEST_TYPE" in
    basic)
        run_test "basic" "BasicFlowUser"
        ;;
    error)
        run_test "error" "ErrorScenarioUser"
        ;;
    mixed)
        run_test "mixed" "MixedScenarioUser"
        ;;
    all)
        echo -e "${YELLOW}Running all test scenarios sequentially...${NC}"
        run_test "basic" "BasicFlowUser"
        run_test "error" "ErrorScenarioUser"
        run_test "mixed" "MixedScenarioUser"
        ;;
    *)
        echo -e "${RED}Invalid test type: $TEST_TYPE${NC}"
        echo "Valid options: basic, error, mixed, all"
        exit 1
        ;;
esac

echo -e "${GREEN}All load tests completed.${NC}"
exit 0 