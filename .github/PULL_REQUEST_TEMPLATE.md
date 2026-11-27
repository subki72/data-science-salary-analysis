## Summary

Describe the change and reference any related issue or ADR.

## Type of Change

- [ ] Bug fix (`fix:`)
- [ ] New feature (`feat:`)
- [ ] Refactor / documentation (`docs:`, `refactor:`)
- [ ] CI / infrastructure (`ci:`, `chore:`)

## Checklist

- [ ] Code passes `python -m ruff check src tests main.py` and `ruff format --check`
- [ ] Code passes `python -m flake8 --max-line-length=120 src tests main.py`
- [ ] Offline unit and integration tests pass (`python -m pytest tests/ -v --cov=src --cov-fail-under=75`)
- [ ] Zero secrets or `.env` artifacts committed
- [ ] Documentation / `CHANGELOG.md` updated where applicable
