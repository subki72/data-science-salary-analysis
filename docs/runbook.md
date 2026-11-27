# Operational Runbook: Data Science Salary Analytics

## 1. Service Overview

- **Package**: `salary_analytics` (`src/salary_analytics/`)
- **CLI Entrypoint**: `main.py`
- **REST API**: FastAPI (`salary_analytics.api:app`) on port `8000`
- **Database**: SQLite with schema managed via `migrations/001_init_salaries.sql`

## 2. Health & Readiness Verification

### Local CLI Probe
```bash
python main.py --health
```
Expected exit code `0` and JSON payload `"status": "ok"` with `"dataset_available": true`.

### HTTP Liveness Probe
```bash
curl -fsS http://127.0.0.1:8000/health
```
Expected HTTP `200` with `{"status":"ok","service":"salary-analytics","version":"1.0.0","dataset_available":true}`.

## 3. Common Incident Playbooks

### A. `SalaryDataError: Salary CSV file not found`
- **Cause**: `SALARY_DATA_PATH` points to a missing CSV or container build excluded `ds_salaries.csv`.
- **Resolution**:
  1. Check `.env` or container environment variable `SALARY_DATA_PATH`.
  2. Verify `ds_salaries.csv` exists in `/app/ds_salaries.csv` (container) or repository root.

### B. `SalaryDataError: Invalid values in column ...` or `missing required columns`
- **Cause**: Input CSV schema drifted or contains `NaN` / malformed numeric rows.
- **Resolution**:
  1. Verify required 11 columns match `migrations/001_init_salaries.sql`.
  2. Ensure synthetic CSV index columns start with `Unnamed` or are removed before ingestion.

### C. HTTP `500 Internal server error`
- **Cause**: Unhandled runtime failure inside API route.
- **Resolution**:
  1. Inspect structured application logs (`%(asctime)s | %(levelname)s | %(name)s | %(message)s`).
  2. Verify SQLite file permissions if `SALARY_DB_PATH` is set to a disk path instead of `:memory:`.

## 4. Rollback Procedure

1. Roll back Docker container to the previous semantic tag (`v1.0.0` or prior release tag).
2. Re-run `python main.py --health` and `curl http://127.0.0.1:8000/health` to confirm recovery.
