# Operator Review Demo

## Command

```powershell
.\scripts\operator_review_demo.ps1
```

Optional paths:

```powershell
.\scripts\operator_review_demo.ps1 `
  -InputPath C:\KODEKS\sample_data\operator_review_input.json `
  -OutputPath C:\KODEKS\data\live_ops\operator_review_result.json `
  -MarkdownPath C:\KODEKS\data\live_ops\operator_review_report.md
```

## Flow

```text
diagnostic case
-> human review
-> final decision
-> final report
-> closed case
```

The demo reads a local operator review input and exports final review artifacts only when the operator runs the command. It does not start a web dashboard, auth layer, cloud runtime, SaaS service, or background ingest.

## Runtime Outputs

The default output paths are:

```text
data\live_ops\operator_review_result.json
data\live_ops\operator_review_report.md
```

These are local runtime outputs. The repo tracks code, tests, schemas, sample inputs, sample result shapes, runbooks, and cleaned reports. It does not track raw live case artifacts or local operator review exports.

## SAFE Mode

If the input is missing a live case, an operator decision, or operator notes, the review enters:

```text
SAFE_MODE_MISSING_DATA
```

In SAFE mode:

- `final_decision` remains `UNKNOWN`,
- `case_closed` remains `false`,
- `autonomous_action` remains `false`,
- recovery hints explain which data must be restored.

## Control Plane

After a review export exists, the EXIM operator entrypoint displays:

- last operator review,
- final decision state,
- case closed/open,
- operator acceptance state.

Run:

```powershell
.\scripts\exim_operator_entrypoint.ps1
```
