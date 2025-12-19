.PHONY: help run stop restart logs connect connect_db test coverage lint format typecheck security quality clean

# Variables
DOCKER_CMD = docker compose
SERVICE_NAME = api
DB_SERVICE_NAME = db
DB_USER = user
DB_NAME = user_registration

# ==============================================================================
# HELP
# ==============================================================================

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ==============================================================================
# DEVELOPMENT
# ==============================================================================

run: ## Start the development server
	@echo "🚀 Starting development server..."
	@$(DOCKER_CMD) up -d --build
	@echo "✅ Server started!"
	@echo "   API:     http://localhost:8000/docs"

stop: ## Stop the development server
	@echo "🛑 Stopping development server..."
	@$(DOCKER_CMD) down
	@echo "✅ Server stopped!"

restart: stop run ## Restart the development server

logs: ## Tail logs from the API container
	@echo "📋 Tailing logs..."
	@$(DOCKER_CMD) logs -f $(SERVICE_NAME)

connect: ## Connect to the API container shell
	@echo "🔌 Connecting to API container..."
	@$(DOCKER_CMD) exec -it $(SERVICE_NAME) /bin/bash

connect_db: ## Connect to the database via psql
	@echo "🔌 Connecting to database..."
	@$(DOCKER_CMD) exec -it $(DB_SERVICE_NAME) psql -U $(DB_USER) -d $(DB_NAME)

# ==============================================================================
# QUALITY & TESTING
# ==============================================================================

test: ## Run tests inside the container
	@echo "🧪 Running tests..."
	@$(DOCKER_CMD) exec $(SERVICE_NAME) pytest -v

coverage: ## Run tests with coverage report
	@echo "📊 Running tests with coverage..."
	@$(DOCKER_CMD) exec $(SERVICE_NAME) pytest --cov=src --cov-report=term-missing

lint: ## Run linters (Black, Isort) check only
	@echo "🔍 Running linters..."
	@$(DOCKER_CMD) exec $(SERVICE_NAME) black --check .
	@$(DOCKER_CMD) exec $(SERVICE_NAME) isort --check-only .

format: ## Format code with Black and Isort
	@echo "🎨 Formatting code..."
	@$(DOCKER_CMD) exec $(SERVICE_NAME) black .
	@$(DOCKER_CMD) exec $(SERVICE_NAME) isort .

typecheck: ## Run static type checking with MyPy
	@echo "types Checking types..."
	@$(DOCKER_CMD) exec $(SERVICE_NAME) mypy .

security: ## Run security checks with Bandit
	@echo "🔒 Running security checks..."
	@$(DOCKER_CMD) exec $(SERVICE_NAME) bandit -r src

quality: format lint typecheck security test ## Run full quality check (format, lint, types, security, test)

# ==============================================================================
# CLEANUP
# ==============================================================================

clean: ## Clean up temporary files and docker volumes
	@echo "🧹 Cleaning up..."
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@rm -rf .pytest_cache
	@rm -rf .mypy_cache
	@rm -rf .coverage
	@rm -rf htmlcov
	@echo "✅ Cleanup complete!"
