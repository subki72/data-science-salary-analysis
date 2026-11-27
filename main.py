"""CLI and ASGI server entrypoint for Data Science Salary Analytics."""

import argparse
import json
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from salary_analytics.config import Settings, configure_logging, load_settings  # noqa: E402
from salary_analytics.database import SalaryDataError, ingest_salary_csv, open_sqlite_connection  # noqa: E402
from salary_analytics.queries import run_full_salary_analysis  # noqa: E402
from salary_analytics.reporting import (  # noqa: E402
    export_report_json,
    format_report_markdown,
    generate_salary_charts,
    report_to_dict,
)

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser for health checks, offline demos, and API serving."""
    parser = argparse.ArgumentParser(
        prog="salary-analytics",
        description="SQLite & FastAPI analytics toolkit for global Data Science salaries.",
    )
    parser.add_argument("--health", action="store_true", help="Verify runtime environment and dataset availability.")
    parser.add_argument("--demo", action="store_true", help="Run offline analytics against the bundled dataset.")
    parser.add_argument("--csv", type=str, default=None, help="Path to a custom salary CSV dataset.")
    parser.add_argument("--min-samples", type=int, default=None, help="Minimum records per role for top-role ranking.")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of top roles to display.")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown", help="CLI report output format.")
    parser.add_argument("--output-json", type=str, default=None, help="Optional file path to save JSON report.")
    parser.add_argument("--charts-dir", type=str, default=None, help="Optional directory to render PNG charts.")
    parser.add_argument("--serve", action="store_true", help="Start the FastAPI Uvicorn server.")
    return parser


def _handle_health_command(settings: Settings) -> int:
    """Emit structured runtime health status JSON and return process exit code."""
    payload = {
        "status": "ok" if settings.data_path.is_file() else "degraded",
        "dataset_path": str(settings.data_path),
        "dataset_available": settings.data_path.is_file(),
        "db_path": settings.db_path,
    }
    logger.info("Health check result: %s", json.dumps(payload))
    sys.stdout.write(json.dumps(payload, indent=2) + "\n")
    return 0 if settings.data_path.is_file() else 1


def _handle_analysis_command(args: argparse.Namespace, settings: Settings) -> int:
    """Execute offline CSV ingestion, SQL analytics, and requested report exports."""
    csv_target = Path(args.csv).resolve() if args.csv else settings.data_path
    min_samples = args.min_samples if args.min_samples is not None else settings.min_role_samples
    limit = args.limit if args.limit is not None else settings.top_roles_limit

    try:
        with open_sqlite_connection(
            db_path=settings.db_path,
            timeout_seconds=settings.request_timeout_seconds,
        ) as conn:
            ingest_salary_csv(csv_target, conn)
            report = run_full_salary_analysis(conn, min_samples=min_samples, limit=limit)
    except (SalaryDataError, ValueError) as exc:
        logger.error("Analysis failed: %s", exc)
        sys.stderr.write(f"Error: {exc}\n")
        return 1

    if args.output_json:
        export_report_json(report, args.output_json)
    if args.charts_dir:
        generate_salary_charts(report, args.charts_dir)

    rendered = json.dumps(report_to_dict(report), indent=2) if args.format == "json" else format_report_markdown(report)
    sys.stdout.write(rendered + ("" if rendered.endswith("\n") else "\n"))
    return 0


def run_cli(argv: Sequence[str] | None = None) -> int:
    """Execute CLI commands and return an explicit process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    settings = load_settings()
    configure_logging(settings.log_level)

    if args.health:
        return _handle_health_command(settings)

    if args.serve:
        import uvicorn

        logger.info("Starting FastAPI server on %s:%d", settings.api_host, settings.api_port)
        uvicorn.run(
            "salary_analytics.api:app",
            host=settings.api_host,
            port=settings.api_port,
            log_level=settings.log_level.lower(),
        )
        return 0

    return _handle_analysis_command(args, settings)


def main() -> None:
    """Invoke CLI entrypoint and exit with status code."""
    raise SystemExit(run_cli())


if __name__ == "__main__":
    main()
