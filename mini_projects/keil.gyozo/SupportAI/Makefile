.PHONY: help install test lint format run docker-up docker-down clean

# Variables
PYTHON := python
POETRY := poetry
DOCKER_COMPOSE := docker compose

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies with Poetry
	$(POETRY) install

install-prod: ## Install production dependencies only
	$(POETRY) install --no-dev

update: ## Update dependencies
	$(POETRY) update

# Testing
test: ## Run all tests
	$(POETRY) run pytest

test-unit: ## Run only unit tests
	$(POETRY) run pytest -m unit -v

test-integration: ## Run integration tests
	$(POETRY) run pytest -m integration -v

test-e2e: ## Run end-to-end tests
	$(POETRY) run pytest -m e2e -v

test-coverage: ## Run tests with coverage report
	$(POETRY) run pytest --cov=src --cov-report=html --cov-report=term-missing

test-parallel: ## Run tests in parallel
	$(POETRY) run pytest -n auto

# Code quality
lint: ## Run linting checks
	$(POETRY) run ruff check src/ tests/

lint-fix: ## Fix linting issues automatically
	$(POETRY) run ruff check --fix src/ tests/

format: ## Format code with ruff
	$(POETRY) run ruff format src/ tests/

typecheck: ## Run type checking with mypy
	$(POETRY) run mypy src/

# Running
run: ## Run the application locally
	$(POETRY) run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

run-prod: ## Run the application in production mode
	$(POETRY) run uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4

# Docker
docker-build: ## Build Docker images
	$(DOCKER_COMPOSE) -f docker/docker-compose.yml build

docker-up: ## Start Docker containers
	$(DOCKER_COMPOSE) -f docker/docker-compose.yml up -d

docker-down: ## Stop Docker containers
	$(DOCKER_COMPOSE) -f docker/docker-compose.yml down

docker-logs: ## View Docker logs
	$(DOCKER_COMPOSE) -f docker/docker-compose.yml logs -f

docker-ps: ## List running containers
	$(DOCKER_COMPOSE) -f docker/docker-compose.yml ps

docker-clean: ## Remove Docker containers and volumes
	$(DOCKER_COMPOSE) -f docker/docker-compose.yml down -v

# Database
seed-qdrant: ## Seed Qdrant with sample data
	$(POETRY) run python scripts/seed_qdrant.py

# Utilities
clean: ## Clean up generated files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf coverage_html/ htmlcov/ .coverage

env-example: ## Create .env from .env.example
	cp .env.example .env
	@echo "Created .env file. Please update with your actual values."

# Development
dev-setup: install env-example ## Setup development environment
	@echo "Development environment setup complete!"
	@echo "Next steps:"
	@echo "  1. Update .env with your API keys"
	@echo "  2. Run 'make docker-up' to start services"
	@echo "  3. Run 'make run' to start the application"
