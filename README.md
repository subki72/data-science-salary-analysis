# Data Science Salary Analysis (2020-2022)

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688)
![SQLite](https://img.shields.io/badge/SQLite-Parameterized%20SQL-003B57)
![CI](https://img.shields.io/badge/CI-Ruff%20%7C%20Pytest%20%7C%20Docker%20%7C%20Trivy-brightgreen)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Project Overview

This project analyzes global Data Science compensation trends from 2020 to 2022 using `ds_salaries.csv` (607 compensation records). It provides a **dual-mode analytical architecture**:

1. **Interactive Notebook (`dsSalary.ipynb`)**: Exploratory SQL + Python workflow in Jupyter Notebook, patched to strip synthetic `Unnamed: 0` CSV index columns, close SQLite connections cleanly, and use Seaborn v0.14-compatible `hue`/`legend=False` barplots.
2. **Production Analytics Package & FastAPI Service (`src/salary_analytics/` + `main.py`)**: Modular SQLite schema migrations (`migrations/001_init_salaries.sql`), strict CSV schema validation (`SalaryDataError`), parameterized SQL queries, headless PNG/Markdown/JSON reporting, CLI execution, and REST endpoints (`/health`, `/summary`, `/roles/top`, `/analyze`).

## Business Questions

1. **Salary Trend:** How did average USD salaries for data roles evolve from 2020 to 2022?
2. **Experience Impact:** How does compensation scale across Entry (`EN`), Mid (`MI`), Senior (`SE`), and Executive (`EX`) levels?
3. **Remote Work Analysis:** How do WFO (`0`), Hybrid (`50`), and Full Remote (`100`) compensation averages compare?
4. **Top Paying Roles:** Which job titles command the highest average salaries (filtered by `COUNT(*) >= 3` to avoid single-sample bias)?

## Architecture

```text
data-science-salary-analysis/
├── dsSalary.ipynb                     # Patched exploratory SQL + Seaborn notebook
├── ds_salaries.csv                    # Source dataset (607 rows)
├── main.py                            # CLI & Uvicorn entrypoint (--health, --demo, --serve)
├── migrations/
│   └── 001_init_salaries.sql          # Normalized SQLite DDL, constraints & indexes
├── src/salary_analytics/
│   ├── config.py                      # Environment settings & structured logging
│   ├── database.py                    # Context-managed SQLite ingestion & validation
│   ├── queries.py                     # Parameterized SQL queries & typed dataclasses
│   ├── reporting.py                   # Markdown, JSON & headless Agg Matplotlib charts
│   └── api.py                         # FastAPI service (/health, /summary, /roles/top, /analyze)
├── tests/                             # Offline unit & API integration tests
├── docs/
│   ├── runbook.md                     # Operational health & incident playbooks
│   └── adr/001-sqlite-analytics-architecture.md
├── Dockerfile                         # Multi-stage non-root Python 3.11 container
├── docker-compose.yml                 # Local container runner
└── Makefile                           # One-command lint, test, demo, and serve targets
```

## Quickstart

### 1. Clone and Install
```bash
git clone https://github.com/subki72/data-science-salary-analysis.git
cd data-science-salary-analysis
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

### 2. Run CLI Health Check & Offline Demo
```bash
python main.py --health
python main.py --demo
python main.py --demo --format json --output-json report.json --charts-dir reports/charts
```

### 3. Run FastAPI Service
```bash
python main.py --serve
# Or via Makefile:
make serve
```
Verify live endpoints:
- `GET http://127.0.0.1:8000/health`
- `GET http://127.0.0.1:8000/summary`
- `GET http://127.0.0.1:8000/roles/top?min_samples=3&limit=5`
- `POST http://127.0.0.1:8000/analyze`

### 4. Run Automated Quality & Test Gates
```bash
make lint
make test
```

### 5. Run Exploratory Notebook
```bash
jupyter notebook dsSalary.ipynb
```

### 6. Run with Docker
```bash
docker compose up --build
```

## Database Schema & Key Findings

Key columns in `ds_salaries` (`migrations/001_init_salaries.sql`):
- `work_year`: Payment year (`2020`, `2021`, `2022`), indexed via `idx_ds_salaries_work_year`.
- `experience_level`: `EN`, `MI`, `SE`, `EX`, indexed via `idx_ds_salaries_experience_level`.
- `remote_ratio`: `0` (WFO), `50` (Hybrid), `100` (Full Remote), indexed via `idx_ds_salaries_remote_ratio`.
- `job_title`: Role title, indexed via `idx_ds_salaries_job_title`.
- `salary_in_usd`: Standardized compensation in USD (`$2,859` to `$600,000`, overall average `$112,297.87`).

Key insights across the 607 records:
- **Positive Market Trend:** Average salaries climbed strongly in **2022** compared to 2020 and 2021.
- **Seniority Scaling:** Transitioning from Mid-level (`MI`) to Senior-level (`SE`) and Executive (`EX`) yields the largest compensation step-up.
- **Remote Compensation:** Full Remote (`100`) roles exhibit a higher average USD salary than Hybrid (`50`) and on-site (`0`) roles in this dataset.
- **Top Specialized Roles:** Specialized roles meeting the `>= 3` sample filter (such as *Principal Data Engineer* and *Data Architect*) lead average USD compensation.

## Stage 1 Remediation Notes

- Added `.gitignore` excluding `.env`, virtual environments, caches, and runtime `.sqlite`/report artifacts while keeping `ds_salaries.csv` tracked.
- Fixed `dsSalary.ipynb` Cell 2 (`Unnamed: 0` CSV index column dropped before `to_sql`, plus explicit `conn.close()` cleanup) and Cells 8, 10, 12 (explicit `hue` and `legend=False` for Seaborn v0.14 compatibility).
- Fixed repository clone URL (`yourusername` -> `subki72`) and notebook reference (`dsSalary.ipynb`) in `README.md`.

## Author & License

**Muhammad Syafii Assubki** — Licensed under the [MIT License](LICENSE).
