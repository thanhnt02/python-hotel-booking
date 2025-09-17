# Makefile for Hotel Booking API
.PHONY: help install dev test lint format clean build start stop logs shell db-init db-reset db-migrate backup restore

# Default target
help:
	@echo "Hotel Booking API - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  install     - Install dependencies"
	@echo "  dev         - Start development server with auto-reload"
	@echo "  test        - Run tests"
	@echo "  test-cov    - Run tests with coverage"
	@echo "  lint        - Run code linting"
	@echo "  format      - Format code with black and isort"
	@echo "  clean       - Clean cache and temporary files"
	@echo ""
	@echo "Docker:"
	@echo "  build       - Build Docker images"
	@echo "  start       - Start all services with Docker Compose"
	@echo "  stop        - Stop all services"
	@echo "  restart     - Restart all services"
	@echo "  logs        - Show logs from all services"
	@echo "  shell       - Open shell in API container"
	@echo ""
	@echo "Database:"
	@echo "  db-init     - Initialize database with tables and data"
	@echo "  db-reset    - Reset database (WARNING: destroys all data)"
	@echo "  db-migrate  - Run database migrations"
	@echo "  db-shell    - Open database shell"
	@echo ""
	@echo "Backup & Restore:"
	@echo "  backup      - Create database backup"
	@echo "  restore     - Restore database from backup"

# Development commands
install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

dev:
	@echo "🚀 Starting development server..."
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

test:
	@echo "🧪 Running tests..."
	pytest

test-cov:
	@echo "🧪 Running tests with coverage..."
	pytest --cov=app --cov-report=html --cov-report=term

lint:
	@echo "🔍 Running linting..."
	flake8 app/
	mypy app/
	bandit -r app/

format:
	@echo "🎨 Formatting code..."
	black app/
	isort app/

clean:
	@echo "🧹 Cleaning cache and temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/

# Docker commands
build:
	@echo "🔨 Building Docker images..."
	docker-compose build

start:
	@echo "🚀 Starting all services..."
	docker-compose up -d
	@echo "✅ Services started. API available at http://localhost:8000"

stop:
	@echo "🛑 Stopping all services..."
	docker-compose down

restart: stop start

logs:
	@echo "📜 Showing logs from all services..."
	docker-compose logs -f

shell:
	@echo "🐚 Opening shell in API container..."
	docker-compose exec api bash

# Database commands
db-init:
	@echo "🗄️ Initializing database..."
	docker-compose exec api python -m app.db_init init

db-reset:
	@echo "⚠️  WARNING: This will destroy all data!"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ]
	@echo "🗄️ Resetting database..."
	docker-compose exec api python -m app.db_init reset

db-migrate:
	@echo "🗄️ Running database migrations..."
	docker-compose exec api python -m app.db_init migrate

db-shell:
	@echo "🗄️ Opening database shell..."
	docker-compose exec db psql -U postgres -d hotel_booking

# Backup and restore
backup:
	@echo "💾 Creating database backup..."
	@mkdir -p backups
	docker-compose exec db pg_dump -U postgres hotel_booking > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Backup created in backups/ directory"

restore:
	@echo "📥 Available backups:"
	@ls -la backups/*.sql 2>/dev/null || echo "No backups found"
	@read -p "Enter backup filename: " backup_file; \
	if [ -f "backups/$$backup_file" ]; then \
		echo "🔄 Restoring database from $$backup_file..."; \
		docker-compose exec -T db psql -U postgres -d hotel_booking < "backups/$$backup_file"; \
		echo "✅ Database restored successfully"; \
	else \
		echo "❌ Backup file not found"; \
	fi

# Production deployment
deploy-prod:
	@echo "🚀 Deploying to production..."
	./deploy.sh production true

# Security scan
security-scan:
	@echo "🔒 Running security scan..."
	safety check
	bandit -r app/

# Performance test
perf-test:
	@echo "⚡ Running performance tests..."
	locust -f tests/performance/locustfile.py --host=http://localhost:8000

# Documentation
docs:
	@echo "📚 Generating documentation..."
	@echo "API documentation available at http://localhost:8000/docs"
	@echo "ReDoc documentation available at http://localhost:8000/redoc"

# Environment setup
setup-env:
	@echo "⚙️ Setting up environment..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "📝 .env file created from template"; \
		echo "Please edit .env file with your configuration"; \
	else \
		echo "✅ .env file already exists"; \
	fi

# Quality checks
quality: lint test security-scan
	@echo "✅ All quality checks passed!"

# Complete setup for new developers
setup: setup-env install build start db-init
	@echo "🎉 Complete setup finished!"
	@echo "API is running at http://localhost:8000"
	@echo "Documentation at http://localhost:8000/docs"
