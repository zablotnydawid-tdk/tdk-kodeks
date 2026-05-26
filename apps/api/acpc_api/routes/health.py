from __future__ import annotations

from fastapi import APIRouter

from acpc_api.models.schemas import HealthResponse


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "service": "acpc-web-mvp-api",
        "storage": "sqlite",
        "local_first": True,
        "cloud_runtime": False,
        "autonomous_action": False,
    }
