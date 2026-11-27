"""Salary Analytics package for global Data Science compensation insights."""

from typing import Final

from salary_analytics.config import Settings, configure_logging, load_settings
from salary_analytics.database import (
    REQUIRED_COLUMNS,
    SalaryDataError,
    apply_migrations,
    ingest_salary_csv,
    load_and_clean_salary_frame,
    open_sqlite_connection,
)
from salary_analytics.queries import (
    ExperienceSalaryMetric,
    RemoteSalaryMetric,
    SalaryAnalysisReport,
    SalaryOverviewSummary,
    TopPayingRole,
    YearlySalaryTrend,
    fetch_overall_summary,
    fetch_salary_by_experience,
    fetch_salary_by_remote_ratio,
    fetch_salary_trend_by_year,
    fetch_top_paying_roles,
    run_full_salary_analysis,
)
from salary_analytics.reporting import (
    export_report_json,
    format_report_markdown,
    generate_salary_charts,
    report_to_dict,
)

__version__: Final[str] = "1.0.0"

__all__: list[str] = [
    "ExperienceSalaryMetric",
    "REQUIRED_COLUMNS",
    "RemoteSalaryMetric",
    "SalaryAnalysisReport",
    "SalaryDataError",
    "SalaryOverviewSummary",
    "Settings",
    "TopPayingRole",
    "YearlySalaryTrend",
    "__version__",
    "apply_migrations",
    "configure_logging",
    "export_report_json",
    "fetch_overall_summary",
    "fetch_salary_by_experience",
    "fetch_salary_by_remote_ratio",
    "fetch_salary_trend_by_year",
    "fetch_top_paying_roles",
    "format_report_markdown",
    "generate_salary_charts",
    "ingest_salary_csv",
    "load_and_clean_salary_frame",
    "load_settings",
    "open_sqlite_connection",
    "report_to_dict",
    "run_full_salary_analysis",
]
