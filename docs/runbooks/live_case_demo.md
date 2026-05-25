# LIVE CASE LOOP Demo

## Purpose

Run the smallest isolated LIVE CASE LOOP proof from a local sample case.

This command is operator-driven and local. It does not start a dashboard, call cloud services, connect to SaaS, or integrate with `C:\TDK` frontend/backend.

## Run

```powershell
cd C:\KODEKS
.\scripts\live_case_demo.ps1
```

Optional paths:

```powershell
.\scripts\live_case_demo.ps1 `
  -InputPath C:\KODEKS\sample_data\live_case_input.json `
  -OutputPath C:\KODEKS\data\live_ops\live_case_result.json `
  -MarkdownPath C:\KODEKS\data\live_ops\live_case_report.md
```

## Expected Flow

1. Read local case input JSON.
2. Run intake.
3. Classify case.
4. Detect priority.
5. Generate diagnostic summary.
6. Generate operator-gated recommendation.
7. Update local proof memory.
8. Emit executive summary.

## Outputs

- JSON result: `data\live_ops\live_case_result.json`
- Markdown report: `data\live_ops\live_case_report.md`

## What It Does Not Do

- no UI
- no SaaS
- no cloud
- no autonomous action
- no live EMS/PV/BESS command
- no TDK frontend/backend integration
- no DEMON scoring yet
- no VMA continuity binding yet

## Operator Rule

Models generate, Control Plane observes, operator decides.

