.PHONY: install install-dev run dev test lint format typecheck docker-build docker-run clean

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt
	pip install -e .

run:
	python main.py

dev:
	uvicorn main:app --host 0.0.0.0 --port 8000 --reload

test:
	pytest -v

lint:
	ruff check .

format:
	black .
	ruff check --fix .

typecheck:
	mypy .

docker-build:
	docker build -t databricks-connector:latest .

docker-run:
	docker compose up --build

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage dist build *.egg-info
