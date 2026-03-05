# Nanobot Makefile
.PHONY: help install run agent gateway cron-list cron-clean cron-status test clean lint format onboard cognition cognition-log mindprint quickstart dev status

# Default target
help:
	@echo "🐈 Nanobot Commands:"
	@echo ""
	@echo "Setup & Install:"
	@echo "  install     - Install dependencies and setup"
	@echo "  onboard     - Initialize configuration"
	@echo ""
	@echo "Running:"
	@echo "  run         - Start interactive agent (CLI)"
	@echo "  agent       - Start interactive agent (alias for run)"
	@echo "  gateway     - Start gateway server (includes cron)"
	@echo ""
	@echo "Cron Management:"
	@echo "  cron-list   - List scheduled jobs"
	@echo "  cron-clean  - Remove all cron jobs"
	@echo "  cron-status - Show cron job status"
	@echo ""
	@echo "Development:"
	@echo "  test        - Run tests"
	@echo "  lint        - Run linting"
	@echo "  format      - Format code"
	@echo "  clean       - Clean cache and build files"
	@echo ""
	@echo "MindPrint:"
	@echo "  mindprint   - Manual cognition distillation"
	@echo "  cognition   - View latest cognition profile"
	@echo "  cognition-log - View distillation log"

# Setup & Install
install:
	@echo "📦 Installing dependencies..."
	python -m venv venv
	source venv/bin/activate && pip install -e .
	@echo "✅ Installation complete!"

onboard:
	@echo "🔧 Initializing nanobot configuration..."
	source venv/bin/activate && python -m nanobot onboard
	@echo "✅ Configuration complete!"

# Running
run:
	@echo "🐈 Starting nanobot agent..."
	source venv/bin/activate && python -m nanobot agent

agent: run

gateway:
	@echo "🌐 Starting nanobot gateway..."
	source venv/bin/activate && python -m nanobot gateway

# Cron Management
cron-list:
	@echo "⏰ Scheduled cron jobs:"
	source venv/bin/activate && python -m nanobot cron list

cron-clean:
	@echo "🧹 Removing all cron jobs..."
	@echo "⚠️  This will remove ALL scheduled jobs including auto-distillation"
	@read -p "Continue? (y/N) " confirm && [ "$$confirm" = "y" ] || exit 1
	source venv/bin/activate && python -m nanobot cron list | grep "enabled" | awk '{print $$2}' | xargs -I {} sh -c 'python -m nanobot cron remove {} 2>/dev/null || true'
	@echo "✅ All cron jobs removed"

cron-status:
	@echo "📊 Cron job status:"
	source venv/bin/activate && python -m nanobot cron list --all

# MindPrint Commands
mindprint:
	@echo "🧠 Running manual cognition distillation..."
	source venv/bin/activate && python -m nanobot agent -m "mindprint distill"

cognition:
	@echo "📖 Latest cognition profile:"
	@if [ -f "/Users/santosh/.nanobot/workspace/memory/.mindprint/cognition.md" ]; then \
		cat /Users/santosh/.nanobot/workspace/memory/.mindprint/cognition.md; \
	else \
		echo "❌ No cognition profile found. Run 'make mindprint' first."; \
	fi

cognition-log:
	@echo "📋 Distillation log:"
	@if [ -f "/Users/santosh/.nanobot/workspace/memory/.mindprint/distillation.log" ]; then \
		cat /Users/santosh/.nanobot/workspace/memory/.mindprint/distillation.log; \
	else \
		echo "❌ No distillation log found."; \
	fi

# Development
test:
	@echo "🧪 Running tests..."
	source venv/bin/activate && python -m pytest

lint:
	@echo "🔍 Running linting..."
	source venv/bin/activate && python -m flake8 nanobot/
	source venv/bin/activate && python -m mypy nanobot/

format:
	@echo "✨ Formatting code..."
	source venv/bin/activate && python -m black nanobot/
	source venv/bin/activate && python -m isort nanobot/

clean:
	@echo "🧹 Cleaning cache and build files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ 2>/dev/null || true
	@echo "✅ Clean complete!"

# Quick start
quickstart: install onboard
	@echo "🚀 Quick start complete!"
	@echo "Next steps:"
	@echo "  1. Add your API key to ~/.nanobot/config.json"
	@echo "  2. Run: make run"
	@echo "  3. Or run: make gateway (for background services)"

# Development workflow
dev: format lint test
	@echo "✅ Development checks complete!"

# Show current cognition status
status: cognition cognition-log cron-status
	@echo "✅ Status complete!"
