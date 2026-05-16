# Nautical Backup — Agent Guide

## Overview

Nautical Backup is a Docker-based container backup tool that automatically backs up Docker container data using rsync. It is configured via Docker labels on individual containers or via environment variables on the Nautical container itself.

- **GitHub**: https://github.com/Minituff/nautical-backup
- **Language**: Python (FastAPI backend, rsync for file transfer)
- **Distribution**: Docker image (`minituff/nautical-backup`)

## Active User Base — Backward Compatibility is Critical

~10,000 users run this app, many with **auto-updating Docker containers**. A push to the main branch can trigger automatic updates for a significant portion of the user base within hours.

- Every code change must be reviewed for backward compatibility before merging.
- If a change breaks existing behavior, it **must be called out explicitly** in the PR and the version bumped using **semantic versioning (semver)**:
  - `PATCH` (x.x.1) — bug fixes, no behavior change for existing users
  - `MINOR` (x.1.x) — new features, fully backward-compatible
  - `MAJOR` (1.x.x) — breaking changes (avoid unless absolutely necessary)

## Docs Folder = Source of Truth

The `docs/` folder contains the MkDocs user-facing documentation. **Read the relevant docs pages before implementing any feature or fix.** If the docs describe a behavior, that behavior is the contract with users. If your change affects documented behavior, update the docs too.

Key docs pages:
- `docs/labels.md` — all Docker label options (per-container config)
- `docs/arguments.md` — all environment variable options (global config)
- `docs/introduction.md` — high-level overview
- `app/defaults.env` — default environment variable values

## Tests — Do Not Change Without Explicit Justification

Tests in `pytest/` exist to enforce backward compatibility. Treat them as a contract.

- **Do not modify existing tests** unless there is a clear, meaningful reason (e.g., the test was wrong, or the code behavior intentionally changed).
- **If you must change an existing test, call it out explicitly** when proposing or describing the change.
- **Adding new tests is always fine** and encouraged.
- When mocking `subprocess.run`, always set `mock_subprocess_run.return_value.returncode = 0` in new tests so the mock behaves like a successful rsync call.

Run tests with: `nb pytest` (inside the dev environment) or `python -m pytest pytest/` locally (excluding `pytest/test_api.py` if the dev DB is not initialized).

## Codebase Layout

```
app/
  backup.py          # Core backup orchestration (NauticalBackup class)
  nautical_env.py    # Environment variable parsing (NauticalEnv class)
  api/               # FastAPI REST API
  db.py              # Simple JSON key-value database
  logger.py          # Logging utilities
pytest/              # Test suite
docs/                # MkDocs user documentation
```
