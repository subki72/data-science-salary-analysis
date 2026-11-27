"""SQLite schema management, CSV validation, and safe data ingestion."""

import logging
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

from salary_analytics.config import DEFAULT_TIMEOUT_SECONDS, PROJECT_ROOT

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS: tuple[str, ...] = (
    "work_year",
    "experience_level",
    "employment_type",
    "job_title",
    "salary",
    "salary_currency",
    "salary_in_usd",
    "employee_residence",
    "remote_ratio",
    "company_location",
    "company_size",
)

VALID_EXPERIENCE_LEVELS: frozenset[str] = frozenset({"EN", "MI", "SE", "EX"})
VALID_EMPLOYMENT_TYPES: frozenset[str] = frozenset({"PT", "FT", "CT", "FL"})
VALID_COMPANY_SIZES: frozenset[str] = frozenset({"S", "M", "L"})
VALID_REMOTE_RATIOS: frozenset[int] = frozenset({0, 50, 100})
DEFAULT_MIGRATION_PATH: Path = PROJECT_ROOT / "migrations" / "001_init_salaries.sql"


class SalaryDataError(ValueError):
    """Domain error raised for invalid salary CSV datasets, paths, or SQLite failures."""


@contextmanager
def open_sqlite_connection(
    db_path: str | Path = ":memory:",
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> Iterator[sqlite3.Connection]:
    """Open a context-managed SQLite connection with foreign keys enabled.

    Args:
        db_path: Target SQLite database file path or ``:memory:``.
        timeout_seconds: Connection lock wait timeout in seconds.

    Yields:
        Configured ``sqlite3.Connection`` guaranteed to close on exit.
    """
    if timeout_seconds <= 0:
        raise SalaryDataError("SQLite timeout_seconds must be positive.")

    conn = sqlite3.connect(str(db_path), timeout=timeout_seconds)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        yield conn
    finally:
        conn.close()


def apply_migrations(conn: sqlite3.Connection, migration_path: Path | None = None) -> None:
    """Apply the SQLite DDL schema migration script.

    Args:
        conn: Active SQLite database connection.
        migration_path: Optional override path to the SQL migration file.

    Raises:
        SalaryDataError: If the migration script is missing or SQL execution fails.
    """
    target = migration_path or DEFAULT_MIGRATION_PATH
    if not target.is_file():
        logger.error("SQLite migration script missing at path=%s", target)
        raise SalaryDataError(f"Migration file not found: {target}")

    sql_script = target.read_text(encoding="utf-8")
    try:
        conn.executescript(sql_script)
        conn.commit()
    except sqlite3.Error as exc:
        logger.error("Failed applying SQLite migration %s: %s", target, exc)
        raise SalaryDataError(f"Failed to apply migration {target.name}: {exc}") from exc


def _validate_categorical_column(df: pd.DataFrame, column: str, allowed: frozenset[str]) -> None:
    """Ensure categorical string columns only contain expected domain codes."""
    values = set(df[column].astype(str).str.strip().unique())
    invalid = sorted(values - allowed)
    if invalid:
        raise SalaryDataError(f"Invalid values in column '{column}': {invalid}")


def _coerce_and_validate_numeric_columns(df: pd.DataFrame) -> None:
    """Validate and cast integer salary, year, and remote ratio columns in-place."""
    for numeric_col in ("work_year", "salary", "salary_in_usd", "remote_ratio"):
        converted = pd.to_numeric(df[numeric_col], errors="coerce")
        if converted.isna().any():
            raise SalaryDataError(f"Column '{numeric_col}' contains non-numeric values.")
        df[numeric_col] = converted.astype(int)

    if (df["work_year"] < 2000).any() or (df["work_year"] > 2100).any():
        raise SalaryDataError("Column 'work_year' must fall between 2000 and 2100.")
    if (df["salary"] < 0).any() or (df["salary_in_usd"] < 0).any():
        raise SalaryDataError("Salary values must be non-negative.")

    invalid_remote = sorted(set(df["remote_ratio"].unique()) - VALID_REMOTE_RATIOS)
    if invalid_remote:
        raise SalaryDataError(f"Invalid 'remote_ratio' values: {invalid_remote}. Expected 0, 50, or 100.")


def _validate_string_and_categorical_columns(df: pd.DataFrame) -> None:
    """Normalize string columns and validate categorical domain constraints in-place."""
    string_columns = (
        "experience_level",
        "employment_type",
        "job_title",
        "salary_currency",
        "employee_residence",
        "company_location",
        "company_size",
    )
    for str_col in string_columns:
        df[str_col] = df[str_col].astype(str).str.strip()
        if (df[str_col] == "").any():
            raise SalaryDataError(f"Column '{str_col}' contains blank string values.")

    _validate_categorical_column(df, "experience_level", VALID_EXPERIENCE_LEVELS)
    _validate_categorical_column(df, "employment_type", VALID_EMPLOYMENT_TYPES)
    _validate_categorical_column(df, "company_size", VALID_COMPANY_SIZES)


def load_and_clean_salary_frame(csv_path: str | Path) -> pd.DataFrame:
    """Load a salary CSV file, drop synthetic index columns, and validate domain rules.

    Args:
        csv_path: Path to the salary CSV file.

    Returns:
        Cleaned and validated ``pandas.DataFrame`` ordered by ``REQUIRED_COLUMNS``.

    Raises:
        SalaryDataError: If the file does not exist, is empty, or fails schema checks.
    """
    path = Path(csv_path)
    if not path.is_file():
        logger.error("Salary CSV file does not exist: %s", path)
        raise SalaryDataError(f"Salary CSV file not found: {path}")

    try:
        raw_df = pd.read_csv(path)
    except (OSError, pd.errors.EmptyDataError, pd.errors.ParserError) as exc:
        logger.error("Unable to parse CSV %s: %s", path, exc)
        raise SalaryDataError(f"Failed to read salary CSV {path.name}: {exc}") from exc

    # Drop CSV export index columns such as 'Unnamed: 0' before database ingestion.
    cleaned_df = raw_df.loc[:, ~raw_df.columns.astype(str).str.startswith("Unnamed")].copy()
    if cleaned_df.empty:
        raise SalaryDataError("Salary dataset is empty.")

    missing_columns = [col for col in REQUIRED_COLUMNS if col not in cleaned_df.columns]
    if missing_columns:
        raise SalaryDataError(f"Salary CSV missing required columns: {missing_columns}")

    cleaned_df = cleaned_df.loc[:, list(REQUIRED_COLUMNS)].copy()
    if cleaned_df.isna().any().any():
        null_cols = cleaned_df.columns[cleaned_df.isna().any()].tolist()
        raise SalaryDataError(f"Salary CSV contains null values in required columns: {null_cols}")

    _coerce_and_validate_numeric_columns(cleaned_df)
    _validate_string_and_categorical_columns(cleaned_df)

    logger.info("Validated salary CSV %s (%d rows, %d columns)", path.name, len(cleaned_df), len(cleaned_df.columns))
    return cleaned_df


def ingest_salary_csv(
    csv_path: str | Path,
    conn: sqlite3.Connection,
    replace_existing: bool = True,
    migration_path: Path | None = None,
) -> int:
    """Apply migrations and ingest validated salary records into SQLite.

    Args:
        csv_path: Source CSV dataset file path.
        conn: Open SQLite connection.
        replace_existing: When True, clears existing rows before appending cleanly.
        migration_path: Optional override path to SQL schema DDL.

    Returns:
        Number of inserted rows.

    Raises:
        SalaryDataError: If validation, migration, or SQLite insertion fails.
    """
    apply_migrations(conn, migration_path=migration_path)
    df = load_and_clean_salary_frame(csv_path)

    try:
        if replace_existing:
            conn.execute("DELETE FROM ds_salaries;")
        df.to_sql("ds_salaries", conn, if_exists="append", index=False)
        conn.commit()
    except sqlite3.Error as exc:
        conn.rollback()
        logger.error("SQLite ingestion failed for %s: %s", csv_path, exc)
        raise SalaryDataError(f"SQLite ingestion failed: {exc}") from exc

    row_count = int(len(df))
    logger.info("Ingested %d salary records into SQLite table ds_salaries.", row_count)
    return row_count
