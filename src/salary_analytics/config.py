"""Externalized environment configuration and structured logging utilities."""

import logging
import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TIMEOUT_SECONDS: float = 10.0


@dataclass(frozen=True)
class Settings:
    """Immutable application runtime configuration loaded from environment variables."""

    app_env: str
    log_level: str
    data_path: Path
    db_path: str
    min_role_samples: int
    top_roles_limit: int
    api_host: str
    api_port: int
    cors_origins: tuple[str, ...]
    request_timeout_seconds: float


def _parse_int_env(name: str, default: int, minimum: int = 1) -> int:
    """Parse and validate an integer environment variable."""
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer, got {raw!r}.") from exc
    if value < minimum:
        raise ValueError(f"Environment variable {name} must be >= {minimum}, got {value}.")
    return value


def _parse_float_env(name: str, default: float, minimum: float = 0.1) -> float:
    """Parse and validate a positive floating-point environment variable."""
    raw = os.getenv(name, str(default)).strip()
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be a number, got {raw!r}.") from exc
    if value < minimum:
        raise ValueError(f"Environment variable {name} must be >= {minimum}, got {value}.")
    return value


def _resolve_data_path(raw_path: str) -> Path:
    """Resolve dataset path relative to project root when a relative path is given."""
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate
    return (PROJECT_ROOT / candidate).resolve()


def load_settings() -> Settings:
    """Load and validate application settings from environment variables.

    Returns:
        Validated ``Settings`` instance.
    """
    raw_origins = os.getenv("SALARY_CORS_ORIGINS", "http://localhost:3000,http://localhost:8000")
    origins = tuple(origin.strip() for origin in raw_origins.split(",") if origin.strip())
    if not origins:
        origins = ("http://localhost:8000",)

    raw_data = os.getenv("SALARY_DATA_PATH", "ds_salaries.csv").strip() or "ds_salaries.csv"
    db_path = os.getenv("SALARY_DB_PATH", ":memory:").strip() or ":memory:"

    return Settings(
        app_env=os.getenv("SALARY_APP_ENV", "development").strip() or "development",
        log_level=(os.getenv("SALARY_LOG_LEVEL", "INFO").strip() or "INFO").upper(),
        data_path=_resolve_data_path(raw_data),
        db_path=db_path,
        min_role_samples=_parse_int_env("SALARY_MIN_ROLE_SAMPLES", 3, minimum=1),
        top_roles_limit=_parse_int_env("SALARY_TOP_ROLES_LIMIT", 5, minimum=1),
        api_host=os.getenv("SALARY_API_HOST", "0.0.0.0").strip() or "0.0.0.0",
        api_port=_parse_int_env("SALARY_API_PORT", 8000, minimum=1),
        cors_origins=origins,
        request_timeout_seconds=_parse_float_env("SALARY_REQUEST_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS),
    )


def configure_logging(level: str = "INFO") -> logging.Logger:
    """Configure application-wide structured logging once and return package logger.

    Args:
        level: Standard Python logging level name (e.g., ``INFO``, ``DEBUG``).

    Returns:
        Configured logger for ``salary_analytics``.
    """
    resolved_level = getattr(logging, level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=resolved_level,
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        )
    else:
        root_logger.setLevel(resolved_level)

    pkg_logger = logging.getLogger("salary_analytics")
    pkg_logger.setLevel(resolved_level)
    pkg_logger.info("Logging initialized at level=%s", logging.getLevelName(resolved_level))
    return pkg_logger
