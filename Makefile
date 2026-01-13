# OpenMark Makefile
# ===================
# Commands for development, testing, and deployment

.PHONY: help install dev test test-unit test-integration test-e2e test-docker coverage clean lint format run docker-build docker-run

# Default target
help:
	@echo "OpenMark Development Commands"
	@echo "=============================="
	@echo ""
	@echo "Development:"
	@echo "  make install        Install production dependencies"
	@echo "  make dev            Install development dependencies"
	@echo "  make run            Run the application locally"
	@echo "  make lint           Run linting checks"
	@echo "  make format         Format code with black"
	@echo ""
	@echo "Testing:"
	@echo "  make test           Run all tests"
	@echo "  make test-unit      Run unit tests only"
	@echo "  make test-integration  Run integration tests"
	@echo "  make test-e2e       Run end-to-end tests"
	@echo "  make test-docker    Run all tests with Docker"
	@echo "  make coverage       Generate coverage report"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build   Build Docker image"
	@echo "  make docker-run     Run with Docker Compose"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          Remove generated files"

# ============================================
# Installation
# ============================================

install:
	pip install -r requirements.txt

dev: install
	pip install -r tests/requirements-test.txt

# ============================================
# Running
# ============================================

run:
	python run.py

# ============================================
# Testing
# ============================================

test:
	pytest tests/ -v --tb=short

test-unit:
	pytest tests/unit -v --tb=short -m unit

test-integration:
	pytest tests/integration -v --tb=short -m integration

test-e2e:
	pytest tests/e2e -v --tb=short -m e2e

test-docker:
	docker-compose -f tests/docker/docker-compose.test.yml up --build --abort-on-container-exit
	docker-compose -f tests/docker/docker-compose.test.yml down -v

coverage:
	pytest tests/ --cov=app --cov-report=html --cov-report=term-missing
	@echo ""
	@echo "Coverage report generated: htmlcov/index.html"

# ============================================
# Code Quality
# ============================================

lint:
	@echo "Running flake8..."
	-flake8 app/ scripts/ --max-line-length=120 --ignore=E501,W503
	@echo "Running pylint..."
	-pylint app/ scripts/ --disable=C0114,C0115,C0116

format:
	black app/ scripts/ tests/

# ============================================
# Docker
# ============================================

docker-build:
	docker build -t openmark:latest .

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

# ============================================
# Cleanup
# ============================================

clean:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf test-results
	rm -rf __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
