# Test Verification Runbook

## Purpose

This runbook documents the local verification path for KODEKS when `pytest` or the `python` launcher is unavailable in the operator shell.

It does not change Knowledge OS logic, Drift Energy thresholds, SAFE behavior, or runtime modules.

## Interpreter Availability

Observed in this environment:

```text
WSL/bash:
- py -3: unavailable
- python: unavailable
- python3: Python 3.12.3

Windows PowerShell:
- py: unavailable
- python: unavailable
- python3: unavailable
```

## Preferred Verification

If `pytest` is installed:

```bash
python3 -m compileall knowledge tests
python3 -m pytest tests/test_knowledge_ingestion.py
```

## Fallback Verification

If `pytest` is not installed, use the standard-library runner:

```bash
python3 -m compileall knowledge tests
python3 scripts/run_tests.py tests/test_knowledge_ingestion.py
```

The fallback runner discovers `test_*` functions and supports the local `tmp_path` fixture by creating temporary directories. Tests requiring unsupported pytest fixtures are skipped with an explicit message.

## Commit Rule

Commit only after:

- compileall passes,
- pytest passes or fallback runner passes when pytest is unavailable,
- `git status --short` is reviewed.
