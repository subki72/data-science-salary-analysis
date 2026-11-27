"""Parameterized SQL analytics queries and typed domain models."""

import logging
import sqlite3
from dataclasses import dataclass

logger = logging.getLogger(__name__)

REMOTE_LABEL_MAP: dict[int, str] = {
    0: "WFO",
    50: "Hybrid",
    100: "Full Remote",
}

EXPERIENCE_LABEL_MAP: dict[str, str] = {
    "EN": "Entry-level",
    "MI": "Mid-level",
    "SE": "Senior-level",
    "EX": "Executive",
}

SQL_OVERALL_SUMMARY = """
SELECT
    COUNT(*) AS total_records,
    COUNT(DISTINCT job_title) AS distinct_roles,
    COALESCE(MIN(work_year), 0) AS min_year,
    COALESCE(MAX(work_year), 0) AS max_year,
    COALESCE(ROUND(AVG(salary_in_usd), 2), 0.0) AS overall_avg_salary_usd,
    COALESCE(MIN(salary_in_usd), 0) AS min_salary_usd,
    COALESCE(MAX(salary_in_usd), 0) AS max_salary_usd
FROM ds_salaries;
"""

SQL_SALARY_TREND_BY_YEAR = """
SELECT
    work_year,
    ROUND(AVG(salary_in_usd), 2) AS avg_salary_usd,
    MIN(salary_in_usd) AS min_salary_usd,
    MAX(salary_in_usd) AS max_salary_usd,
    COUNT(*) AS sample_count
FROM ds_salaries
GROUP BY work_year
ORDER BY work_year ASC;
"""

SQL_SALARY_BY_EXPERIENCE = """
SELECT
    experience_level,
    ROUND(AVG(salary_in_usd), 2) AS avg_salary_usd,
    MIN(salary_in_usd) AS min_salary_usd,
    MAX(salary_in_usd) AS max_salary_usd,
    COUNT(*) AS sample_count
FROM ds_salaries
GROUP BY experience_level
ORDER BY avg_salary_usd DESC;
"""

SQL_SALARY_BY_REMOTE_RATIO = """
SELECT
    remote_ratio,
    ROUND(AVG(salary_in_usd), 2) AS avg_salary_usd,
    COUNT(*) AS sample_count
FROM ds_salaries
GROUP BY remote_ratio
ORDER BY remote_ratio ASC;
"""

SQL_TOP_PAYING_ROLES = """
SELECT
    job_title,
    ROUND(AVG(salary_in_usd), 2) AS avg_salary_usd,
    MAX(salary_in_usd) AS max_salary_usd,
    COUNT(*) AS employee_count
FROM ds_salaries
GROUP BY job_title
HAVING COUNT(*) >= ?
ORDER BY avg_salary_usd DESC, employee_count DESC, job_title ASC
LIMIT ?;
"""


@dataclass(frozen=True)
class YearlySalaryTrend:
    """Average and range salary metrics aggregated by calendar year."""

    work_year: int
    avg_salary_usd: float
    min_salary_usd: int
    max_salary_usd: int
    sample_count: int


@dataclass(frozen=True)
class ExperienceSalaryMetric:
    """Salary metrics grouped by standardized experience level."""

    experience_level: str
    experience_label: str
    avg_salary_usd: float
    min_salary_usd: int
    max_salary_usd: int
    sample_count: int


@dataclass(frozen=True)
class RemoteSalaryMetric:
    """Salary metrics grouped by remote ratio (0=WFO, 50=Hybrid, 100=Full Remote)."""

    remote_ratio: int
    work_mode: str
    avg_salary_usd: float
    sample_count: int


@dataclass(frozen=True)
class TopPayingRole:
    """Highest compensated job title meeting the minimum sample size threshold."""

    job_title: str
    avg_salary_usd: float
    max_salary_usd: int
    employee_count: int


@dataclass(frozen=True)
class SalaryOverviewSummary:
    """High-level dataset summary statistics across all ingested records."""

    total_records: int
    distinct_roles: int
    min_year: int
    max_year: int
    overall_avg_salary_usd: float
    min_salary_usd: int
    max_salary_usd: int


@dataclass(frozen=True)
class SalaryAnalysisReport:
    """Complete analytical report answering all four core business questions."""

    summary: SalaryOverviewSummary
    yearly_trends: list[YearlySalaryTrend]
    experience_breakdown: list[ExperienceSalaryMetric]
    remote_breakdown: list[RemoteSalaryMetric]
    top_roles: list[TopPayingRole]


def fetch_overall_summary(conn: sqlite3.Connection) -> SalaryOverviewSummary:
    """Compute overall dataset summary statistics from SQLite.

    Args:
        conn: Open SQLite connection containing ``ds_salaries``.

    Returns:
        Populated ``SalaryOverviewSummary``.
    """
    row = conn.execute(SQL_OVERALL_SUMMARY).fetchone()
    if row is None or int(row["total_records"]) == 0:
        raise ValueError("Cannot compute summary on an empty ds_salaries table.")

    return SalaryOverviewSummary(
        total_records=int(row["total_records"]),
        distinct_roles=int(row["distinct_roles"]),
        min_year=int(row["min_year"]),
        max_year=int(row["max_year"]),
        overall_avg_salary_usd=float(row["overall_avg_salary_usd"]),
        min_salary_usd=int(row["min_salary_usd"]),
        max_salary_usd=int(row["max_salary_usd"]),
    )


def fetch_salary_trend_by_year(conn: sqlite3.Connection) -> list[YearlySalaryTrend]:
    """Retrieve average USD salary progression grouped by ``work_year``."""
    rows = conn.execute(SQL_SALARY_TREND_BY_YEAR).fetchall()
    return [
        YearlySalaryTrend(
            work_year=int(r["work_year"]),
            avg_salary_usd=float(r["avg_salary_usd"]),
            min_salary_usd=int(r["min_salary_usd"]),
            max_salary_usd=int(r["max_salary_usd"]),
            sample_count=int(r["sample_count"]),
        )
        for r in rows
    ]


def fetch_salary_by_experience(conn: sqlite3.Connection) -> list[ExperienceSalaryMetric]:
    """Retrieve average USD salary grouped by ``experience_level``."""
    rows = conn.execute(SQL_SALARY_BY_EXPERIENCE).fetchall()
    return [
        ExperienceSalaryMetric(
            experience_level=str(r["experience_level"]),
            experience_label=EXPERIENCE_LABEL_MAP.get(str(r["experience_level"]), str(r["experience_level"])),
            avg_salary_usd=float(r["avg_salary_usd"]),
            min_salary_usd=int(r["min_salary_usd"]),
            max_salary_usd=int(r["max_salary_usd"]),
            sample_count=int(r["sample_count"]),
        )
        for r in rows
    ]


def fetch_salary_by_remote_ratio(conn: sqlite3.Connection) -> list[RemoteSalaryMetric]:
    """Retrieve average USD salary grouped by ``remote_ratio``."""
    rows = conn.execute(SQL_SALARY_BY_REMOTE_RATIO).fetchall()
    return [
        RemoteSalaryMetric(
            remote_ratio=int(r["remote_ratio"]),
            work_mode=REMOTE_LABEL_MAP.get(int(r["remote_ratio"]), "Other"),
            avg_salary_usd=float(r["avg_salary_usd"]),
            sample_count=int(r["sample_count"]),
        )
        for r in rows
    ]


def fetch_top_paying_roles(
    conn: sqlite3.Connection,
    min_samples: int = 3,
    limit: int = 5,
) -> list[TopPayingRole]:
    """Retrieve top paying job titles filtered by minimum employee sample count.

    Args:
        conn: Open SQLite connection.
        min_samples: Minimum row count per job title to prevent small-sample bias.
        limit: Maximum number of roles to return.

    Returns:
        List of ``TopPayingRole`` sorted by descending average salary.

    Raises:
        ValueError: If ``min_samples < 1`` or ``limit`` is outside ``[1, 100]``.
    """
    if min_samples < 1:
        raise ValueError(f"min_samples must be >= 1, got {min_samples}.")
    if limit < 1 or limit > 100:
        raise ValueError(f"limit must be between 1 and 100, got {limit}.")

    rows = conn.execute(SQL_TOP_PAYING_ROLES, (min_samples, limit)).fetchall()
    return [
        TopPayingRole(
            job_title=str(r["job_title"]),
            avg_salary_usd=float(r["avg_salary_usd"]),
            max_salary_usd=int(r["max_salary_usd"]),
            employee_count=int(r["employee_count"]),
        )
        for r in rows
    ]


def run_full_salary_analysis(
    conn: sqlite3.Connection,
    min_samples: int = 3,
    limit: int = 5,
) -> SalaryAnalysisReport:
    """Execute all analytical SQL queries and return a structured report.

    Args:
        conn: Open SQLite connection containing ingested salary rows.
        min_samples: Minimum employee records required for top-role ranking.
        limit: Number of top roles to include.

    Returns:
        Complete ``SalaryAnalysisReport`` dataclass.
    """
    summary = fetch_overall_summary(conn)
    trends = fetch_salary_trend_by_year(conn)
    experience = fetch_salary_by_experience(conn)
    remote = fetch_salary_by_remote_ratio(conn)
    top_roles = fetch_top_paying_roles(conn, min_samples=min_samples, limit=limit)

    logger.info(
        "Completed salary analysis: records=%d years=%d-%d top_roles=%d",
        summary.total_records,
        summary.min_year,
        summary.max_year,
        len(top_roles),
    )
    return SalaryAnalysisReport(
        summary=summary,
        yearly_trends=trends,
        experience_breakdown=experience,
        remote_breakdown=remote,
        top_roles=top_roles,
    )
