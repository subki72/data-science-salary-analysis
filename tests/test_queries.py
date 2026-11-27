"""Unit tests for parameterized SQL analytics queries."""

from pathlib import Path

import pandas as pd
import pytest

from salary_analytics.config import PROJECT_ROOT
from salary_analytics.database import ingest_salary_csv, open_sqlite_connection
from salary_analytics.queries import (
    fetch_salary_by_experience,
    fetch_salary_by_remote_ratio,
    fetch_salary_trend_by_year,
    fetch_top_paying_roles,
    run_full_salary_analysis,
)


def _write_synthetic_dataset(csv_path: Path) -> None:
    """Create a deterministic synthetic salary dataset covering all query branches."""
    records = [
        ("2020", "EN", "FT", "Data Analyst", 50000, 0),
        ("2021", "MI", "FT", "Data Analyst", 70000, 50),
        ("2022", "SE", "FT", "Data Analyst", 90000, 100),
        ("2022", "SE", "FT", "ML Engineer", 160000, 100),
        ("2022", "SE", "FT", "ML Engineer", 140000, 100),
        ("2022", "EX", "FT", "ML Engineer", 200000, 100),
        ("2022", "EX", "FT", "Chief AI Officer", 450000, 100),  # Only 1 sample -> filtered out when min_samples=3
    ]
    rows = [
        {
            "work_year": int(yr),
            "experience_level": exp,
            "employment_type": emp,
            "job_title": title,
            "salary": usd,
            "salary_currency": "USD",
            "salary_in_usd": usd,
            "employee_residence": "US",
            "remote_ratio": remote,
            "company_location": "US",
            "company_size": "M",
        }
        for yr, exp, emp, title, usd, remote in records
    ]
    pd.DataFrame(rows).to_csv(csv_path, index=False)


def test_salary_trend_by_year_chronological(tmp_path: Path) -> None:
    """Aggregate average salary per year ordered ascending."""
    csv_path = tmp_path / "synthetic.csv"
    _write_synthetic_dataset(csv_path)

    with open_sqlite_connection(":memory:") as conn:
        ingest_salary_csv(csv_path, conn)
        trends = fetch_salary_trend_by_year(conn)

    assert [t.work_year for t in trends] == [2020, 2021, 2022]
    assert trends[0].avg_salary_usd == 50000.0
    assert trends[1].avg_salary_usd == 70000.0
    assert trends[2].sample_count == 5


def test_salary_by_experience_orders_descending(tmp_path: Path) -> None:
    """Group compensation by experience level with descriptive labels."""
    csv_path = tmp_path / "synthetic.csv"
    _write_synthetic_dataset(csv_path)

    with open_sqlite_connection(":memory:") as conn:
        ingest_salary_csv(csv_path, conn)
        exp_metrics = fetch_salary_by_experience(conn)

    assert [e.experience_level for e in exp_metrics] == ["EX", "SE", "MI", "EN"]
    assert exp_metrics[0].experience_label == "Executive"
    assert exp_metrics[0].avg_salary_usd == 325000.0


def test_salary_by_remote_ratio_maps_modes(tmp_path: Path) -> None:
    """Map numeric remote_ratio codes to WFO, Hybrid, and Full Remote."""
    csv_path = tmp_path / "synthetic.csv"
    _write_synthetic_dataset(csv_path)

    with open_sqlite_connection(":memory:") as conn:
        ingest_salary_csv(csv_path, conn)
        remote_metrics = fetch_salary_by_remote_ratio(conn)

    assert [(r.remote_ratio, r.work_mode) for r in remote_metrics] == [
        (0, "WFO"),
        (50, "Hybrid"),
        (100, "Full Remote"),
    ]


def test_top_paying_roles_filters_by_min_samples_and_limit(tmp_path: Path) -> None:
    """Exclude single-sample outlier titles when min_samples >= 3."""
    csv_path = tmp_path / "synthetic.csv"
    _write_synthetic_dataset(csv_path)

    with open_sqlite_connection(":memory:") as conn:
        ingest_salary_csv(csv_path, conn)
        roles = fetch_top_paying_roles(conn, min_samples=3, limit=5)

    assert [r.job_title for r in roles] == ["ML Engineer", "Data Analyst"]
    assert roles[0].employee_count == 3
    assert roles[0].avg_salary_usd == pytest.approx(166666.67, rel=1e-4)


def test_fetch_top_paying_roles_rejects_invalid_bounds(tmp_path: Path) -> None:
    """Enforce valid bounds on min_samples and limit arguments."""
    csv_path = tmp_path / "synthetic.csv"
    _write_synthetic_dataset(csv_path)

    with open_sqlite_connection(":memory:") as conn:
        ingest_salary_csv(csv_path, conn)
        with pytest.raises(ValueError, match="min_samples"):
            fetch_top_paying_roles(conn, min_samples=0, limit=5)
        with pytest.raises(ValueError, match="limit"):
            fetch_top_paying_roles(conn, min_samples=1, limit=101)


def test_run_full_salary_analysis_on_bundled_dataset() -> None:
    """Verify baseline metrics against bundled 607-row ds_salaries.csv."""
    bundled_csv = PROJECT_ROOT / "ds_salaries.csv"
    with open_sqlite_connection(":memory:") as conn:
        ingest_salary_csv(bundled_csv, conn)
        report = run_full_salary_analysis(conn, min_samples=3, limit=5)

    assert report.summary.total_records == 607
    assert report.summary.min_year == 2020
    assert report.summary.max_year == 2022
    assert report.summary.overall_avg_salary_usd == pytest.approx(112297.87, abs=0.05)
    assert len(report.top_roles) == 5
