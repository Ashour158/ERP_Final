.PHONY: help install install-dev clean lint format test test-cov security pre-commit-install run docker-build docker-run

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements.txt
	pip install -r dev-requirements.txt

clean: ## Clean up cache and temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf build/
	rm -rf dist/

lint: ## Run linting (flake8, bandit)
	flake8 .
	bandit -r . --severity-level medium

format: ## Format code with black and isort
	black .
	isort .

format-check: ## Check code formatting
	black --check --diff .
	isort --check-only --diff .

test: ## Run tests
	pytest

test-cov: ## Run tests with coverage
	pytest --cov=. --cov-report=html --cov-report=term-missing

security: ## Run security scans
	bandit -r . -f json -o bandit-report.json
	bandit -r . --severity-level medium

pre-commit-install: ## Install pre-commit hooks
	pre-commit install

run: ## Run the Flask application in development mode
	export FLASK_ENV=development && python wsgi.py

docker-build: ## Build Docker image
	docker build -t erp-system .

docker-run: ## Run Docker container
	docker run -p 8080:8080 --env-file .env erp-system

deploy-check: ## Run deployment readiness checks
	python deployment_check.py

validate: ## Run application validation
	python validate.py

init-db: ## Initialize database
	python init_db.py