from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI


ROOT = Path(__file__).resolve().parents[2]
API_ROOT = Path(__file__).resolve().parent
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from acpc_api.routes import diagnostics, health, reports  # noqa: E402


app = FastAPI(
    title="ACPC Web MVP API",
    version="0.1.0",
    description="Local-first ACPC diagnostic API foundation.",
)

app.include_router(health.router)
app.include_router(diagnostics.router)
app.include_router(reports.router)
