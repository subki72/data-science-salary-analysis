"""Unit tests for CSV validation, schema migrations, and SQLite ingestion."""

from pathlib import Path

import pandas as pd
import pytest

from salary_analytics.database import (
    REQUIRED_COLUMNS,
    SalaryDataError,
    ingest_salary_csv,
    load_and_clean_salary_frame,
    open_sqlite_connection,
)


def _build_sample_rows() -> list[dict[str, object]]:
    """Build valid sample salary records matching the ds_salaries schema."""
    return [
        {
            "Unnamed: 0": 0,
            "work_year": 2020,
            "experience_level": "MI",
            "employment_type": "FT",
            "job_title": "Data Scientist",
            "salary": 80000,
            "salary_currency": "USD",
            "salary_in_usd": 80000,
            "employee_residence": "US",
            "remote_ratio": 100,
            "company_location": "US",
            "company_size": "M",
        },
        {
            "Unnamed: 0": 1,
            "work_year": 2022,
            "experience_level": "SE",
            "employment_type": "FT",
            "job_title": "Data Engineer",
            "salary": 150000,
            "salary_currency": "USD",
            "salary_in_usd": 150000,
            "employee_residence": "US",
            "remote_ratio": 0,
            "company_location": "US",
            "company_size": "L",
        },
    ]


def test_load_and_clean_salary_frame_drops_unnamed_index(tmp_path: Path) -> None:
    """Drop synthetic Unnamed index columns and preserve required schema columns."""
    csv_path = tmp_path / "salaries.csv"
    pd.DataFrame(_build_sample_rows()).to_csv(csv_path, index=False)

    cleaned = load_and_clean_salary_frame(csv_path)

    assert list(cleaned.columns) == list(REQUIRED_COLUMNS)
    assert "Unnamed: 0" not in cleaned.columns
    assert len(cleaned) == 2


def test_load_and_clean_salary_frame_missing_file_raises(tmp_path: Path) -> None:
    """Raise SalaryDataError when source CSV path does not exist."""
    missing = tmp_path / "does_not_exist.csv"

    with pytest.raises(SalaryDataError, match="not found"):
        load_and_clean_salary_frame(missing)


def test_load_and_clean_salary_frame_empty_csv_raises(tmp_path: Path) -> None:
    """Raise SalaryDataError when CSV contains headers with zero rows."""
    csv_path = tmp_path / "empty.csv"
    pd.DataFrame(columns=list(REQUIRED_COLUMNS)).to_csv(csv_path, index=False)

    with pytest.raises(SalaryDataError, match="empty"):
        load_and_clean_salary_frame(csv_path)


def test_load_and_clean_salary_frame_missing_columns_raises(tmp_path: Path) -> None:
    """Raise SalaryDataError when mandatory columns are absent."""
    csv_path = tmp_path / "bad_cols.csv"
    pd.DataFrame([{"work_year": 2022, "job_title": "Data Scientist"}]).to_csv(csv_path, index=False)

    with pytest.raises(SalaryDataError, match="missing required columns"):
        load_and_clean_salary_frame(csv_path)


def test_load_and_clean_salary_frame_invalid_experience_raises(tmp_path: Path) -> None:
    """Reject unknown experience_level codes."""
    rows = _build_sample_rows()
    rows[0]["experience_level"] = "INTERN"
    csv_path = tmp_path / "bad_exp.csv"
    pd.DataFrame(rows).to_csv(csv_path, index=False)

    with pytest.raises(SalaryDataError, match="experience_level"):
        load_and_clean_salary_frame(csv_path)


def test_load_and_clean_salary_frame_invalid_remote_ratio_raises(tmp_path: Path) -> None:
    """Reject remote_ratio values outside {0, 50, 100}."""
    rows = _build_sample_rows()
    rows[0]["remote_ratio"] = 75
    csv_path = tmp_path / "bad_remote.csv"
    pd.DataFrame(rows).to_csv(csv_path, index=False)

    with pytest.raises(SalaryDataError, match="remote_ratio"):
        load_and_clean_salary_frame(csv_path)


def test_load_and_clean_salary_frame_negative_salary_raises(tmp_path: Path) -> None:
    """Reject negative salary values."""
    rows = _build_sample_rows()
    rows[0]["salary_in_usd"] = -100
    csv_path = tmp_path / "negative.csv"
    pd.DataFrame(rows).to_csv(csv_path, index=False)

    with pytest.raises(SalaryDataError, match="non-negative"):
        load_and_clean_salary_frame(csv_path)


def test_ingest_salary_csv_applies_schema_indexes_and_replaces_idempotently(tmp_path: Path) -> None:
    """Create indexed SQLite table and support idempotent re-ingestion."""
    csv_path = tmp_path / "salaries.csv"
    pd.DataFrame(_build_sample_rows()).to_csv(csv_path, index=False)

    with open_sqlite_connection(":memory:", timeout_seconds=5.0) as conn:
        first_count = ingest_salary_csv(csv_path, conn)
        second_count = ingest_salary_csv(csv_path, conn)
        total_rows = conn.execute("SELECT COUNT(*) FROM ds_salaries;").fetchone()[0]
        indexes = {row["name"] for row in conn.execute("PRAGMA index_list('ds_salaries');").fetchall()}
        fk_enabled = conn.execute("PRAGMA foreign_keys;").fetchone()[0]

    assert first_count == 2
    assert second_count == 2
    assert total_rows == 2
    assert fk_enabled == 1
    assert "idx_ds_salaries_work_year" in indexes
    assert "idx_ds_salaries_job_title" in indexes


def test_open_sqlite_connection_rejects_nonpositive_timeout() -> None:
    """Guard against non-positive SQLite lock timeout values."""
    with pytest.raises(SalaryDataError, match="timeout_seconds"):
        with open_sqlite_connection(":memory:", timeout_seconds=0):
            pass
