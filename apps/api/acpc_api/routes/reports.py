from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response

from acpc_api.models.schemas import ReportDetailResponse, ReportListResponse
from acpc_api.services.storage_service import StorageService


router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("", response_model=ReportListResponse)
def list_reports() -> dict[str, object]:
    return {"reports": StorageService().list_reports()}


@router.get("/{report_id}", response_model=ReportDetailResponse)
def get_report(report_id: str) -> dict[str, object]:
    report = StorageService().get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="report not found")
    return {"report": report}


@router.get("/{report_id}/markdown")
def get_report_markdown(report_id: str) -> Response:
    markdown = StorageService().get_markdown(report_id)
    if markdown is None:
        raise HTTPException(status_code=404, detail="report not found")
    return Response(content=markdown, media_type="text/markdown")
