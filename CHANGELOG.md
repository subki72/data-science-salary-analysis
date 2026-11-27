# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-11-27

### Added
- Modular Python analytics package `src/salary_analytics/` (`config.py`, `database.py`, `queries.py`, `reporting.py`, `api.py`).
- Normalized SQLite DDL and indexes in `migrations/001_init_salaries.sql`.
- FastAPI service exposing `/health`, `/summary`, `/analyze`, and `/roles/top` with Pydantic v2 validation, CORS middleware, and global exception handling.
- Dual-mode CLI entrypoint `main.py` supporting `--health`, `--demo`, `--csv`, `--min-samples`, and `--serve`.
- Automated offline unit and integration test suite under `tests/` (`test_database.py`, `test_queries.py`, `test_reporting.py`, `test_api.py`).
- Multi-stage non-root `Dockerfile`, `docker-compose.yml`, `Makefile`, `pyproject.toml`, `.env.example`, and `.pre-commit-config.yaml`.
- GitHub Actions CI (`ci.yml`) and release (`release.yml`) workflows with Ruff, Flake8, Pytest coverage gate, Semgrep SAST, Docker build, and Trivy scanning.
- Operational documentation (`docs/runbook.md`, `docs/adr/001-sqlite-analytics-architecture.md`, `SECURITY.md`, `CONTRIBUTING.md`).

### Fixed
- Added `.gitignore` excluding `.env`, virtual environments, caches, and runtime database outputs while tracking `ds_salaries.csv`.
- Patched `dsSalary.ipynb` Cell 2 to strip `Unnamed: 0` CSV index columns prior to SQLite ingestion and added explicit `conn.close()` cleanup.
- Fixed Seaborn v0.14 `FutureWarning` calls in `dsSalary.ipynb` Cells 8, 10, and 12 by specifying `hue` and `legend=False`.
- Corrected `README.md` repository clone URL and notebook filename (`dsSalary.ipynb`).
