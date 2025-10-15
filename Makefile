.PHONY: help install install-dev clean test lint format security check all run docker-build docker-run

# Default target
help:
	@echo "Trading Bot Swarm - Development Commands"
	@echo "=========================================="
	@echo ""
	@echo "Setup:"
	@echo "  make install        Install production dependencies"
	@echo "  make install-dev    Install development dependencies"
	@echo ""
	@echo "Code Quality:"
	@echo "  make format         Format code with black and isort"
	@echo "  make lint           Run linting (flake8, mypy)"
	@echo "  make security       Run security checks (bandit, safety)"
	@echo "  make check          Run all quality checks"
	@echo ""
	@echo "Testing:"
	@echo "  make test           Run tests with pytest"
	@echo "  make test-cov       Run tests with coverage report"
	@echo ""
	@echo "Application:"
	@echo "  make run            Run the trading bot"
	@echo "  make run-dev        Run in development mode"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build   Build Docker image"
	@echo "  make docker-run     Run Docker container"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean          Clean build artifacts and cache"
	@echo "  make deps-check     Check for outdated dependencies"

# Installation
install:
	pip install -r requirements.txt

install-dev: install
	pip install black flake8 mypy pytest pytest-asyncio pytest-cov
	pip install bandit safety pip-audit pre-commit
	pip install isort
	pre-commit install

# Code formatting
format:
	@echo "Formatting code with black..."
	black src/ main.py tests/ --line-length=100
	@echo "Sorting imports with isort..."
	isort src/ main.py tests/ --profile black

# Linting
lint:
	@echo "Running flake8..."
	flake8 src/ main.py --max-line-length=127 --extend-ignore=E203,W503
	@echo "Running mypy..."
	mypy src/ main.py --ignore-missing-imports

# Security checks
security:
	@echo "Running bandit security checks..."
	bandit -r src/ main.py
	@echo "Checking for vulnerable dependencies..."
	safety check || true
	pip-audit || true

# Run all checks
check: lint security test

# Testing
test:
	@echo "Running tests..."
	pytest tests/ -v

test-cov:
	@echo "Running tests with coverage..."
	pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

# Run application
run:
	python main.py

run-dev:
	python main.py --env development

run-prod:
	python main.py --env production

# Docker
docker-build:
	docker build -t trading-bot-swarm:latest .

docker-run:
	docker run -it --rm trading-bot-swarm:latest

# Cleanup
clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	rm -rf build/ dist/ htmlcov/ .coverage coverage.xml
	@echo "Clean complete!"

# Dependency management
deps-check:
	@echo "Checking for outdated dependencies..."
	pip list --outdated

deps-update:
	@echo "This will update all dependencies. Continue? [y/N]"
	@read -r response && [ "$$response" = "y" ] && pip install --upgrade -r requirements.txt || echo "Cancelled"

# Pre-commit
pre-commit-install:
	pre-commit install

pre-commit-run:
	pre-commit run --all-files

# Documentation
docs:
	@echo "Opening documentation..."
	@open docs/CI_CD.md || xdg-open docs/CI_CD.md || echo "Please manually open docs/CI_CD.md"

# All quality checks (used by CI)
all: format lint security test
	@echo "All checks passed! ✅"
