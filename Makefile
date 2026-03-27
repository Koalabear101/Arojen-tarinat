.PHONY: install dev test lint run run-prod clean help

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install production dependencies
	pip install -r requirements.txt

dev:  ## Install development dependencies
	pip install -r requirements-dev.txt

test:  ## Run all tests
	python -m pytest backend/tests/ -v

test-legacy:  ## Run legacy PythonGame tests
	cd PythonGame && python -m unittest discover .

lint:  ## Lint backend code
	python -m pylint backend/ --disable=C0114,C0115,C0116,C0103,R0903 --fail-under=7

lint-js:  ## Lint JSGame code
	cd JSGame && npm run lint

test-js:  ## Run JSGame tests
	cd JSGame && npm test

run:  ## Run development server
	python run.py

run-prod:  ## Run production server with Gunicorn
	gunicorn --bind 0.0.0.0:8000 --workers 4 wsgi:app

docker-build:  ## Build Docker image
	docker build -t arojen-tarinat .

docker-run:  ## Run Docker container
	docker run -p 8000:8000 arojen-tarinat

clean:  ## Remove caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true

check: lint test lint-js test-js  ## Run all lints and tests
