.DEFAULT_GOAL := help
.PHONY: help install lint format format-check typecheck test check build clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-13s\033[0m %s\n", $$1, $$2}'

install: ## Install the package with dev dependencies
	pip install -e ".[dev]"

lint: ## Lint with ruff
	ruff check .

format: ## Format with ruff (apply changes)
	ruff format .

format-check: ## Check formatting without changing files
	ruff format --check .

typecheck: ## Type-check with mypy
	mypy src

test: ## Run the test suite with coverage
	pytest --cov=senderkit --cov-report=term-missing

check: format-check lint typecheck test ## Run everything CI runs

build: ## Build sdist and wheel
	python -m build

clean: ## Remove build and cache artifacts
	rm -rf dist build *.egg-info src/*.egg-info .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +
