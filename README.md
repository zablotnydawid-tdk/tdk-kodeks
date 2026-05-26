# KODEKS

## Local Windows Demo Run

ACPC Web MVP Phase 1 runs a local FastAPI backend for PV diagnostic intake, witness report generation, SQLite persistence, report history, and Markdown export.

```bat
run_api.bat
```

Manual run:

```powershell
cd apps\api
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Health:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Runbook:

```text
docs/runbooks/acpc_api_local_run.md
```
