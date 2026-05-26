# ACPC Live Flow Runbook

## Purpose

This runbook documents the first local ACPC runtime flow:

```text
ACPC live ingest
-> PV diagnostics
-> Live Case Loop
-> Control Plane
```

The flow is local-first and recovery-safe. It proves that ACPC runtime, ingest, diagnostics, Live Case Loop, and Control Plane can behave as one operator-visible system without starting cloud runtime, SaaS services, or automatic background ingestion.

## First Local Flow

The first live pass used a local ACPC event payload and moved it through the operator path:

1. ACPC ingest accepted a local event and normalized it into a runtime payload.
2. PV diagnostics consumed the derived diagnostic sample and produced a diagnostic report.
3. Live Case Loop received the case payload and created the current operator-facing live case state.
4. Control Plane snapshot reflected ACPC component presence and the latest available runtime/test status.

The operator-facing result is a single continuity path:

```text
source event
-> diagnostic evidence
-> live case status
-> control plane organism snapshot
```

## Runtime Artifacts

Raw ACPC runtime artifacts are created under:

```text
data/acpc/
```

The first flow created its local working set under:

```text
data/acpc/live_ingest_first/
```

Typical files in that directory may include:

```text
acpc_event.json
pv_sample_for_diagnostics.json
pv_diagnostic_report.json
pv_diagnostic_report.md
live_case_payload.json
flow_summary.json
```

These files are runtime outputs. They may contain local case data, diagnostic input, intermediate evidence, generated reports, or operator flow summaries. They are intentionally not repository source.

## Repository Boundary

`data/acpc/` is ignored by git and must remain local runtime output.

The repository should contain:

- source code,
- tests,
- schemas,
- runbooks,
- architecture notes,
- cleaned reports that were intentionally reviewed and moved into a tracked documentation/report path.

The repository must not contain:

- raw ACPC runtime artifacts,
- local live ingest payloads,
- generated cache files,
- unreviewed diagnostic output,
- client-sensitive evidence dumps.

## Recovery Hints

If the Control Plane shows ACPC components as missing, verify these paths:

```text
src/acpc/runtime
src/acpc/ingest
src/acpc/energy/pv_diagnostics
tests/runtime
tests/ingest
tests/energy
```

If live flow artifacts are missing, treat the state as `UNKNOWN` rather than reconstructing facts from memory. Re-run the local flow from source inputs and preserve the new output under `data/acpc/`.

If diagnostics or Live Case Loop cannot read the latest payload, verify that the previous stage produced a valid local JSON artifact and that no manual copy step introduced schema drift.

## Continuity Note

ACPC runtime artifacts are useful for operator continuity, but they are not source of truth for repository history. Commit code, tests, schemas, and cleaned documentation. Keep noisy runtime evidence local unless it has been reviewed, sanitized, and deliberately promoted into a tracked report.
