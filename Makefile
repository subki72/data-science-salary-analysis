.PHONY: install lint format test health demo serve docker-build clean

PYTHON ?= python

install:
	$(PYTHON) -m pip install -r requirements-dev.txt

lint:
	$(PYTHON) -m ruff check src tests main.py
	$(PYTHON) -m ruff format --check src tests main.py
	$(PYTHON) -m flake8 --max-line-length=120 src tests main.py

format:
	$(PYTHON) -m ruff format src tests main.py

test:
	$(PYTHON) -m pytest tests/ -v --cov=src --cov-report=term-missing --cov-fail-under=75

health:
	$(PYTHON) main.py --health

demo:
	$(PYTHON) main.py --demo

serve:
	$(PYTHON) main.py --serve

docker-build:
	docker build -t ds-salary-analytics:latest .

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov dist build .coverage coverage.xml
	find . -type d -name "__pycache__" -exec rm -rf {} +
