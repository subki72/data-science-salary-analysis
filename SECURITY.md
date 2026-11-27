# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in this repository:

1. **Do NOT open a public GitHub issue** for undisclosed vulnerabilities.
2. Submit a private report via GitHub Security Advisories (`Security -> Advisories -> Report a vulnerability`).
3. Include affected file paths, reproduction steps, and estimated severity.
4. Initial acknowledgement will be provided within **48 hours**.

## Security Controls

- **Secret Hygiene**: `.env` and key artifacts are excluded via `.gitignore`; zero active credentials are stored in source control.
- **SQL Injection Prevention**: All analytical SQL queries use parameterized bindings via Python's `sqlite3` DB-API 2.0.
- **Input Validation & Bounds**: FastAPI routes validate payloads via Pydantic v2 schemas with strict numeric constraints.
- **Automated Vulnerability Management**: Weekly Dependabot alerts (`semver-major` ignored for stability), Semgrep SAST, and Trivy container image scanning in CI.
- **Container Hardening**: Multi-stage non-root Docker runtime (`appuser`).
