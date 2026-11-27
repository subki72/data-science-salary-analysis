"""FastAPI REST service exposing Data Science salary analytics endpoints."""

import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from salary_analytics import __version__
from salary_analytics.config import PROJECT_ROOT, Settings, configure_logging, load_settings
from salary_analytics.database import SalaryDataError, ingest_salary_csv, open_sqlite_connection
from salary_analytics.queries import SalaryAnalysisReport, fetch_top_paying_roles, run_full_salary_analysis
from salary_analytics.reporting import report_to_dict

logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    """Liveness and dataset readiness payload."""

    status: str
    service: str
    version: str
    dataset_available: bool


class YearlyTrendItem(BaseModel):
    """Yearly compensation trend data point."""

    work_year: int
    avg_salary_usd: float
    min_salary_usd: int
    max_salary_usd: int
    sample_count: int


class ExperienceMetricItem(BaseModel):
    """Compensation breakdown by seniority."""

    experience_level: str
    experience_label: str
    avg_salary_usd: float
    min_salary_usd: int
    max_salary_usd: int
    sample_count: int


class RemoteMetricItem(BaseModel):
    """Compensation breakdown by remote ratio."""

    remote_ratio: int
    work_mode: str
    avg_salary_usd: float
    sample_count: int


class TopRoleItem(BaseModel):
    """Top paying role ranking item."""

    job_title: str
    avg_salary_usd: float
    max_salary_usd: int
    employee_count: int


class SalarySummaryItem(BaseModel):
    """Dataset overview summary metrics."""

    total_records: int
    distinct_roles: int
    min_year: int
    max_year: int
    overall_avg_salary_usd: float
    min_salary_usd: int
    max_salary_usd: int


class AnalysisResponse(BaseModel):
    """Full salary analysis API response payload."""

    summary: SalarySummaryItem
    yearly_trends: list[YearlyTrendItem]
    experience_breakdown: list[ExperienceMetricItem]
    remote_breakdown: list[RemoteMetricItem]
    top_roles: list[TopRoleItem]


class AnalyzeRequest(BaseModel):
    """Request parameters for custom salary analysis."""

    csv_path: str | None = Field(
        default=None,
        description="Optional relative path inside the project workspace to a salary CSV dataset.",
    )
    min_samples: int = Field(default=3, ge=1, le=500)
    limit: int = Field(default=5, ge=1, le=50)


class TopRolesResponse(BaseModel):
    """Response payload for top paying roles query."""

    min_samples: int
    limit: int
    roles: list[TopRoleItem]


def _resolve_safe_csv_path(requested_path: str | None, default_path: Path) -> Path:
    """Resolve dataset path while blocking traversal outside project root."""
    if not requested_path:
        return default_path

    candidate = Path(requested_path)
    resolved = candidate.resolve() if candidate.is_absolute() else (PROJECT_ROOT / candidate).resolve()
    try:
        resolved.relative_to(PROJECT_ROOT.resolve())
    except ValueError as exc:
        logger.warning("Rejected csv_path outside workspace boundary: %s", requested_path)
        raise HTTPException(
            status_code=400,
            detail="Requested csv_path must reside inside the project workspace.",
        ) from exc

    if not resolved.is_file():
        raise HTTPException(status_code=404, detail="Requested salary CSV dataset was not found.")
    return resolved


def _execute_analysis(
    settings: Settings,
    csv_path: Path,
    min_samples: int,
    limit: int,
) -> SalaryAnalysisReport:
    """Ingest dataset into SQLite and compute full analytics report."""
    with open_sqlite_connection(
        db_path=settings.db_path,
        timeout_seconds=settings.request_timeout_seconds,
    ) as conn:
        ingest_salary_csv(csv_path, conn)
        return run_full_salary_analysis(conn, min_samples=min_samples, limit=limit)


def _register_exception_handlers(application: FastAPI) -> None:
    """Attach domain and global fallback exception handlers."""

    @application.exception_handler(SalaryDataError)
    async def handle_salary_data_error(_request: Request, exc: SalaryDataError) -> JSONResponse:
        logger.warning("Salary data validation error: %s", exc)
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @application.exception_handler(Exception)
    async def handle_unexpected_error(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception while processing request: %s", exc)
        return JSONResponse(status_code=500, content={"detail": "Internal server error."})


def _register_operational_routes(application: FastAPI) -> None:
    """Register service liveness and default summary routes."""

    @application.get("/health", response_model=HealthResponse, tags=["Operations"])
    def health_check() -> HealthResponse:
        """Report service health and dataset readiness."""
        active_settings: Settings = application.state.settings
        return HealthResponse(
            status="ok",
            service="salary-analytics",
            version=__version__,
            dataset_available=active_settings.data_path.is_file(),
        )

    @application.get("/summary", response_model=AnalysisResponse, tags=["Analytics"])
    def get_summary() -> dict[str, Any]:
        """Return full compensation summary across the default dataset."""
        active_settings: Settings = application.state.settings
        report = _execute_analysis(
            settings=active_settings,
            csv_path=active_settings.data_path,
            min_samples=active_settings.min_role_samples,
            limit=active_settings.top_roles_limit,
        )
        return report_to_dict(report)


def _register_query_routes(application: FastAPI) -> None:
    """Register parameterized role ranking and custom analysis routes."""

    @application.get("/roles/top", response_model=TopRolesResponse, tags=["Analytics"])
    def get_top_roles(
        min_samples: int = Query(default=3, ge=1, le=500),
        limit: int = Query(default=5, ge=1, le=50),
    ) -> TopRolesResponse:
        """Return top paying job titles filtered by minimum employee count."""
        active_settings: Settings = application.state.settings
        with open_sqlite_connection(
            db_path=active_settings.db_path,
            timeout_seconds=active_settings.request_timeout_seconds,
        ) as conn:
            ingest_salary_csv(active_settings.data_path, conn)
            roles = fetch_top_paying_roles(conn, min_samples=min_samples, limit=limit)

        return TopRolesResponse(
            min_samples=min_samples,
            limit=limit,
            roles=[TopRoleItem(**vars(role)) for role in roles],
        )

    @application.post("/analyze", response_model=AnalysisResponse, tags=["Analytics"])
    def analyze_salaries(payload: AnalyzeRequest) -> dict[str, Any]:
        """Run full salary analysis with caller-specified thresholds."""
        active_settings: Settings = application.state.settings
        target_csv = _resolve_safe_csv_path(payload.csv_path, active_settings.data_path)
        report = _execute_analysis(
            settings=active_settings,
            csv_path=target_csv,
            min_samples=payload.min_samples,
            limit=payload.limit,
        )
        return report_to_dict(report)


def create_app(settings_override: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application instance.

    Args:
        settings_override: Optional injected ``Settings`` instance for testing.

    Returns:
        Configured ``FastAPI`` application.
    """
    settings = settings_override or load_settings()
    configure_logging(settings.log_level)

    application = FastAPI(
        title="Data Science Salary Analytics API",
        version=__version__,
        description="SQLite-backed analytical REST service for global Data Science compensation trends.",
    )
    application.state.settings = settings
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Authorization"],
    )
    _register_exception_handlers(application)
    _register_operational_routes(application)
    _register_query_routes(application)
    return application


app = create_app()
