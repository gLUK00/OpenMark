#!/bin/bash
# =============================================================================
# OpenMark Test Runner Script
# =============================================================================
# Usage: ./scripts/run_tests.sh [test_type] [options]
#
# Test types:
#   unit         - Run unit tests only (fast, no external dependencies)
#   integration  - Run integration tests (requires databases)
#   e2e          - Run end-to-end tests
#   docker       - Run all tests with Docker
#   all          - Run all tests (default)
#
# Options:
#   --coverage   - Generate coverage report
#   --verbose    - Verbose output
#   --fast       - Skip slow tests
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TEST_TYPE="${1:-all}"
COVERAGE=""
VERBOSE="-v"
MARKERS=""

# Parse arguments
shift || true
while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage)
            COVERAGE="--cov=app --cov-report=html --cov-report=term-missing"
            shift
            ;;
        --verbose)
            VERBOSE="-vv"
            shift
            ;;
        --fast)
            MARKERS="-m 'not slow'"
            shift
            ;;
        *)
            shift
            ;;
    esac
done

echo -e "${BLUE}🧪 OpenMark Test Runner${NC}"
echo "========================="
echo ""

# Change to project root
cd "$(dirname "$0")/.."

case $TEST_TYPE in
    unit)
        echo -e "${YELLOW}▶ Running unit tests...${NC}"
        pytest tests/unit $VERBOSE --tb=short $COVERAGE $MARKERS
        ;;
    integration)
        echo -e "${YELLOW}▶ Running integration tests...${NC}"
        pytest tests/integration $VERBOSE --tb=short $COVERAGE $MARKERS
        ;;
    e2e)
        echo -e "${YELLOW}▶ Running end-to-end tests...${NC}"
        pytest tests/e2e $VERBOSE --tb=short $COVERAGE $MARKERS
        ;;
    scripts)
        echo -e "${YELLOW}▶ Running script tests...${NC}"
        pytest tests/scripts $VERBOSE --tb=short $COVERAGE $MARKERS
        ;;
    docker)
        echo -e "${YELLOW}▶ Running all tests with Docker...${NC}"
        docker-compose -f tests/docker/docker-compose.test.yml up --build --abort-on-container-exit
        EXIT_CODE=$?
        docker-compose -f tests/docker/docker-compose.test.yml down -v
        exit $EXIT_CODE
        ;;
    all|*)
        echo -e "${YELLOW}▶ Running all tests...${NC}"
        pytest tests/ $VERBOSE --tb=short $COVERAGE $MARKERS
        ;;
esac

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Tests completed successfully!${NC}"
else
    echo ""
    echo -e "${RED}❌ Tests failed with exit code $EXIT_CODE${NC}"
fi

if [[ -n "$COVERAGE" && -d "htmlcov" ]]; then
    echo ""
    echo -e "${BLUE}📊 Coverage report: htmlcov/index.html${NC}"
fi

exit $EXIT_CODE
