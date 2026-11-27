"""Integration tests for the FastAPI REST endpoints and error boundaries."""

import pytest
from fastapi.testclient import TestClient

from salary_analytics import api as api_module
from salary_analytics.config import PROJECT_ROOT, Settings
from salary_analytics.database import SalaryDataError


def _make_test_settings() -> Settings:
    """Create deterministic offline Settings pointing to the bundled dataset."""
    return Settings(
        app_env="test",
        log_level="INFO",
        data_path=PROJECT_ROOT / "ds_salaries.csv",
        db_path=":memory:",
        min_role_samples=3,
        top_roles_limit=5,
        api_host="127.0.0.1",
        api_port=8000,
        cors_origins=("http://localhost:3000",),
        request_timeout_seconds=5.0,
    )


def test_health_endpoint_returns_ok() -> None:
    """Verify /health probe returns 200 and reports bundled dataset availability."""
    client = TestClient(api_module.create_app(_make_test_settings()))

    response = client.get("/health")
    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "ok"
    assert body["service"] == "salary-analytics"
    assert body["dataset_available"] is True


def test_summary_endpoint_returns_full_analysis() -> None:
    """Verify /summary aggregates all 607 records and answers all four questions."""
    client = TestClient(api_module.create_app(_make_test_settings()))

    response = client.get("/summary")
    body = response.json()

    assert response.status_code == 200
    assert body["summary"]["total_records"] == 607
    assert len(body["yearly_trends"]) == 3
    assert len(body["experience_breakdown"]) == 4
    assert len(body["remote_breakdown"]) == 3
    assert len(body["top_roles"]) == 5


def test_roles_top_endpoint_validates_and_limits() -> None:
    """Verify /roles/top honors query bounds and rejects invalid parameters."""
    client = TestClient(api_module.create_app(_make_test_settings()))

    ok_resp = client.get("/roles/top", params={"min_samples": 3, "limit": 2})
    bad_resp = client.get("/roles/top", params={"min_samples": 0})

    assert ok_resp.status_code == 200
    assert len(ok_resp.json()["roles"]) == 2
    assert bad_resp.status_code == 422


def test_analyze_endpoint_rejects_path_traversal() -> None:
    """Block csv_path traversal attempts outside the project workspace."""
    client = TestClient(api_module.create_app(_make_test_settings()))

    ok_resp = client.post("/analyze", json={"min_samples": 3, "limit": 3})
    traversal_resp = client.post("/analyze", json={"csv_path": "../outside.csv", "min_samples": 3, "limit": 3})

    assert ok_resp.status_code == 200
    assert len(ok_resp.json()["top_roles"]) == 3
    assert traversal_resp.status_code == 400


def test_api_exception_handlers_mask_unexpected_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return safe HTTP 400 on SalaryDataError and generic 500 on unhandled errors."""
    app = api_module.create_app(_make_test_settings())
    client = TestClient(app, raise_server_exceptions=False)

    def _raise_data_error(*_args: object, **_kwargs: object) -> object:
        raise SalaryDataError("Malformed salary input")

    monkeypatch.setattr(api_module, "_execute_analysis", _raise_data_error)
    resp_400 = client.get("/summary")
    assert resp_400.status_code == 400
    assert resp_400.json() == {"detail": "Malformed salary input"}

    def _raise_runtime_error(*_args: object, **_kwargs: object) -> object:
        raise RuntimeError("sensitive internal stack context")

    monkeypatch.setattr(api_module, "_execute_analysis", _raise_runtime_error)
    resp_500 = client.get("/summary")
    assert resp_500.status_code == 500
    assert resp_500.json() == {"detail": "Internal server error."}
