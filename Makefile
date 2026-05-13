.PHONY: install dev dev-backend dev-frontend test test-backend test-frontend lint lint-backend lint-frontend clean db-init help

PYTHON := python
PIP := pip
NPM := npm

BACKEND_DIR := chat-app/backend
FRONTEND_DIR := chat-app/frontend
AGENT_DIR := agent-framework

# Default target
help:
	@echo "ChatAgent - Available Commands"
	@echo "=============================="
	@echo "  make install       - Install all dependencies (parallel pip + npm)"
	@echo "  make dev           - Start full stack dev servers (backend + frontend)"
	@echo "  make dev-backend   - Start backend dev server only"
	@echo "  make dev-frontend  - Start frontend dev server only"
	@echo "  make test          - Run all tests (pytest + npm test)"
	@echo "  make test-backend  - Run backend tests only"
	@echo "  make test-frontend - Run frontend tests only"
	@echo "  make lint          - Run all linters (ruff + eslint)"
	@echo "  make lint-backend  - Run backend linter only"
	@echo "  make lint-frontend - Run frontend linter only"
	@echo "  make clean         - Clean build artifacts and caches"
	@echo "  make db-init       - Initialize PostgreSQL database"
	@echo "  make help          - Show this help message"

# Install dependencies
install: install-backend install-frontend install-agent

install-backend:
	cd $(BACKEND_DIR) && $(PIP) install -r requirements.txt

install-frontend:
	cd $(FRONTEND_DIR) && $(NPM) install

install-agent:
	cd $(AGENT_DIR) && $(PIP) install -e .

# Development servers
dev:
	@echo "Starting full stack development servers..."
	@echo "Backend will run on http://localhost:8000"
	@echo "Frontend will run on http://localhost:3000"
	@make -j2 dev-backend dev-frontend

dev-backend:
	cd $(BACKEND_DIR) && source venv/bin/activate 2>/dev/null || . venv/Scripts/activate 2>/dev/null; uvicorn main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd $(FRONTEND_DIR) && $(NPM) run dev

# Testing
test: test-backend test-frontend test-agent

test-backend:
	cd $(BACKEND_DIR) && source venv/bin/activate 2>/dev/null || . venv/Scripts/activate 2>/dev/null; pytest -v --tb=short

test-frontend:
	cd $(FRONTEND_DIR) && $(NPM) test

test-agent:
	cd $(AGENT_DIR) && source .venv/bin/activate 2>/dev/null || . .venv/Scripts/activate 2>/dev/null; pytest -v --tb=short

# Linting
lint: lint-backend lint-frontend

lint-backend:
	cd $(BACKEND_DIR) && ruff check . && ruff format --check .

lint-frontend:
	cd $(FRONTEND_DIR) && $(NPM) run lint

# Cleaning
clean:
	@echo "Cleaning build artifacts and caches..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf $(FRONTEND_DIR)/.next 2>/dev/null || true
	rm -rf $(FRONTEND_DIR)/dist 2>/dev/null || true
	rm -rf $(FRONTEND_DIR)/node_modules 2>/dev/null || true
	rm -rf $(BACKEND_DIR)/venv 2>/dev/null || true
	rm -rf $(AGENT_DIR)/.venv 2>/dev/null || true
	@echo "Clean complete."

# Database initialization
db-init:
	@echo "Initializing PostgreSQL database..."
	cd $(BACKEND_DIR) && source venv/bin/activate 2>/dev/null || . venv/Scripts/activate 2>/dev/null; alembic upgrade head
	@echo "Database initialized successfully."
