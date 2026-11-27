"""Unit tests for Markdown, JSON, and headless Matplotlib chart reporting."""

import json
import warnings
from pathlib import Path

from salary_analytics.config import PROJECT_ROOT
from salary_analytics.database import ingest_salary_csv, open_sqlite_connection
from salary_analytics.queries import SalaryAnalysisReport, run_full_salary_analysis
from salary_analytics.reporting import (
    export_report_json,
    format_report_markdown,
    generate_salary_charts,
)


def _load_bundled_report() -> SalaryAnalysisReport:
    """Load and analyze bundled ds_salaries.csv into a structured report."""
    with open_sqlite_connection(":memory:") as conn:
        ingest_salary_csv(PROJECT_ROOT / "ds_salaries.csv", conn)
        return run_full_salary_analysis(conn, min_samples=3, limit=5)


def test_format_report_markdown_contains_all_sections() -> None:
    """Render Markdown containing overview and all four analytical sections."""
    report = _load_bundled_report()

    markdown = format_report_markdown(report)

    assert "# Data Science Salary Analysis Report" in markdown
    assert "607" in markdown
    assert "## 1. Salary Trend by Year" in markdown
    assert "## 2. Salary by Experience Level" in markdown
    assert "## 3. Remote Ratio Comparison" in markdown
    assert "## 4. Top Paying Roles" in markdown


def test_export_report_json_writes_valid_payload(tmp_path: Path) -> None:
    """Serialize report to JSON file and verify round-trip integrity."""
    report = _load_bundled_report()
    out_file = tmp_path / "nested" / "salary_report.json"

    written = export_report_json(report, out_file)
    parsed = json.loads(written.read_text(encoding="utf-8"))

    assert written.is_file()
    assert parsed["summary"]["total_records"] == 607
    assert len(parsed["yearly_trends"]) == 3
    assert len(parsed["top_roles"]) == 5


def test_generate_salary_charts_emits_no_seaborn_future_warnings(tmp_path: Path) -> None:
    """Render four PNG charts headlessly without Seaborn FutureWarning deprecations."""
    report = _load_bundled_report()
    charts_dir = tmp_path / "charts"

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", FutureWarning)
        paths = generate_salary_charts(report, charts_dir)

    future_warnings = [w for w in caught if issubclass(w.category, FutureWarning)]
    assert future_warnings == []
    assert len(paths) == 4
    for chart_path in paths:
        assert chart_path.is_file()
        assert chart_path.stat().st_size > 0
