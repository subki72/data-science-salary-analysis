# Contributing Guidelines

Thank you for your interest in contributing to **Data Science Salary Analysis**!

## Development Setup

1. Clone the repository and create a virtual environment:
   ```bash
   git clone https://github.com/subki72/data-science-salary-analysis.git
   cd data-science-salary-analysis
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install pre-commit hooks (recommended):
   ```bash
   pre-commit install
   ```

## Code Quality & Testing Standards

All pull requests must pass linting, formatting, and the offline automated test suite before merging:

```bash
python -m ruff check src tests main.py
python -m ruff format --check src tests main.py
python -m flake8 --max-line-length=120 src tests main.py
python -m pytest tests/ -v --cov=src --cov-fail-under=75
```

Or simply run:

```bash
make lint test
```

## Coding Conventions

- Follow Python 3.11+ type annotations and Google-style docstrings.
- Use `logging.getLogger(__name__)` rather than bare `print()` inside `src/salary_analytics/`.
- Keep all SQL queries in `src/salary_analytics/queries.py` or `migrations/` using parameterized bindings (`?`).
- Ensure every test is 100% offline with deterministic inputs.
- Use Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `ci:`, `chore:`).
