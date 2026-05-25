# EXIM Knowledge Operating System Runbook

## Local Command

```powershell
cd C:\KODEKS
python .\scripts\run_knowledge_ingestion.py .\path\to\document.md --output .\data\knowledge\ingestion_result.json
```

To also write the operator report:

```powershell
python .\scripts\run_knowledge_ingestion.py .\path\to\document.md --output .\data\knowledge\ingestion_result.json --report .\data\knowledge\operator_report.md
```

Supported local inputs:

- `.txt`
- `.md`
- `.json`
- `.csv`
- `.pdf` when local `pypdf` is installed

No cloud OCR, SaaS runtime, or model router is used.

## SAFE Behavior

If PDF text extraction is unavailable or a page has no embedded text, the result is marked with parser warnings and `requires_human_review`.

The system must show `UNKNOWN` or review-required state instead of guessing document content.

## Output

The JSON output contains:

- chunks,
- trace object per chunk,
- source graph,
- dependency map,
- risk map,
- evidence map,
- decision map,
- validation status,
- blocked recommendation claims,
- human review queue,
- operator report markdown,
- `ready_for_client_recommendation`.

## Operator Rule

If `ready_for_client_recommendation` is `false`, the material may inform operator review but must not be used as final client recommendation.
