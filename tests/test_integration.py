"""End-to-end CLI and environment configuration integration tests."""

import json
from pathlib import Path

import pytest

from main import run_cli
from salary_analytics.config import load_settings


def test_cli_health_returns_zero(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify CLI --health reports ok status and exits with code 0."""
    exit_code = run_cli(["--health"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["status"] == "ok"
    assert payload["dataset_available"] is True


def test_cli_demo_exports_json_and_charts(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Run CLI --demo end-to-end offline and verify JSON + PNG artifacts."""
    out_json = tmp_path / "demo_report.json"
    charts_dir = tmp_path / "charts"

    exit_code = run_cli(
        [
            "--demo",
            "--format",
            "json",
            "--min-samples",
            "3",
            "--limit",
            "5",
            "--output-json",
            str(out_json),
            "--charts-dir",
            str(charts_dir),
        ]
    )
    captured = capsys.readouterr()
    stdout_payload = json.loads(captured.out)

    assert exit_code == 0
    assert stdout_payload["summary"]["total_records"] == 607
    assert out_json.is_file()
    assert len(list(charts_dir.glob("*.png"))) == 4


def test_cli_missing_csv_returns_error_code(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Return non-zero exit code when --csv points to a missing dataset."""
    missing = tmp_path / "missing.csv"

    exit_code = run_cli(["--csv", str(missing)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Error:" in captured.err


def test_load_settings_parses_and_validates_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Parse custom environment overrides and reject malformed integer settings."""
    monkeypatch.setenv("SALARY_MIN_ROLE_SAMPLES", "4")
    monkeypatch.setenv("SALARY_CORS_ORIGINS", "https://example.org")

    settings = load_settings()
    assert settings.min_role_samples == 4
    assert settings.cors_origins == ("https://example.org",)

    monkeypatch.setenv("SALARY_MIN_ROLE_SAMPLES", "not-an-int")
    with pytest.raises(ValueError, match="SALARY_MIN_ROLE_SAMPLES"):
        load_settings()
