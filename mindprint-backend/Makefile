.PHONY: install dev run-docker stop-docker logs clean test health

# Variables
PYTHON = python3
PIP = $(PYTHON) -m pip
UVICORN = $(PYTHON) -m uvicorn

# --- Development ---

install:
	$(PIP) install -r requirements.txt

dev:
	$(UVICORN) app.main:app --host 0.0.0.0 --port 5000 --reload

# --- Docker ---

run-docker:
	docker-compose up -d --build

stop-docker:
	docker-compose down

logs:
	docker-compose logs -f

# --- Utilities ---

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

health:
	curl http://localhost:5000/api/health

test:
	$(PYTHON) -m pytest

reset-db:
	psql -d memorydb -U nanobot -c "TRUNCATE TABLE memory_data, sellers, buyers, rentals CASCADE;"
