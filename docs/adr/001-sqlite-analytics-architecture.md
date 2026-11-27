# ADR 001: Modular SQLite Analytics & Dual-Mode FastAPI Architecture

- **Status**: Accepted
- **Date**: 2026-11-27
- **Deciders**: Muhammad Syafii Assubki

## Context

The initial repository contained a standalone Jupyter notebook (`dsSalary.ipynb`) coupled with `ds_salaries.csv`. While effective for exploratory visualization, the codebase lacked:
1. Automated schema validation and removal of the CSV synthetic `Unnamed: 0` column before SQLite ingestion.
2. Separation between database DDL, parameterized SQL queries, visualization reporting, and programmatic interfaces.
3. Headless execution (`CLI` and `HTTP API`), automated offline tests, and reproducible container packaging.

## Decision

We adopt a **dual-mode non-breaking architecture**:
1. Preserve and patch `dsSalary.ipynb` directly (cleaning `Unnamed: 0`, enforcing `conn.close()`, and fixing Seaborn v0.14 `hue`/`legend=False` deprecations) so exploratory notebook users retain full parity.
2. Extract core analytics into `src/salary_analytics/`:
   - `config.py`: Environment-driven `Settings` and structured logging.
   - `database.py`: Context-managed SQLite lifecycle (`PRAGMA foreign_keys = ON`), explicit timeouts, schema validation (`SalaryDataError`), and DDL migrations from `migrations/001_init_salaries.sql`.
   - `queries.py`: Typed dataclasses and parameterized SQL (`?` placeholders) answering all 4 analytical questions.
   - `reporting.py`: Headless Matplotlib (`Agg`), Markdown, and JSON exporters.
   - `api.py`: FastAPI service (`/health`, `/summary`, `/roles/top`, `/analyze`) with Pydantic v2 validation, CORS policy, workspace boundary path checks, and centralized exception handlers, keeping zero raw SQL inside API routes.
3. Expose unified CLI entrypoint `main.py` (`--health`, `--demo`, `--csv`, `--min-samples`, `--serve`).

## Consequences

- **Positive**: 100% offline deterministic testability, strict separation of concerns, zero SQL injection risk, and container portability on Python 3.11+.
- **Trade-off**: In-memory SQLite (`:memory:`) is used by default for stateless queries; high-volume persistent workloads can configure `SALARY_DB_PATH` to a persistent volume.
