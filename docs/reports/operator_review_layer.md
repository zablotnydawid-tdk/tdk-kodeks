# Operator Review Layer

## Status

`OPERATOR_REVIEW_LAYER` closes the first local operator workflow:

```text
LIVE INGEST
-> DIAGNOSTICS
-> GOVERNANCE
-> OPERATOR REVIEW
-> FINAL DECISION
-> FINAL REPORT
-> CASE CLOSED
```

It is terminal-first, local-first, and operator-controlled. It does not add web UI, auth, cloud runtime, SaaS runtime, or autonomous remediation.

## Runtime Boundary

The layer reads a Live Case Loop result or an embedded live case payload, then records the human operator decision. It can export a final JSON report and Markdown report only when an output path is explicitly provided.

The default governance posture is:

- operator always decides,
- `autonomous_action = false`,
- Control Plane observes,
- missing data becomes `UNKNOWN`,
- missing required context triggers `SAFE_MODE_MISSING_DATA`,
- decision trace is preserved for recovery and continuity.

## Supported Operator Outcomes

- `approve_recommendation`
- `reject_recommendation`
- `request_field_visit`
- `request_thermal_inspection`
- `escalation_required`
- `safe_to_monitor`

The final decision resolves to one of:

- `APPROVED`
- `REJECTED`
- `FIELD_VISIT_REQUIRED`
- `THERMAL_INSPECTION_REQUIRED`
- `ESCALATED`
- `SAFE_TO_MONITOR`
- `UNKNOWN`

`APPROVED`, `REJECTED`, and `SAFE_TO_MONITOR` close the case. Escalation and inspection decisions close the review step but keep the operational case open for follow-up.

## Outputs

The operator review result contains:

- final operator report JSON,
- Markdown final report,
- decision trace,
- final governance summary,
- operator acceptance state,
- case closed/open state.

Runtime exports are written by the demo to:

```text
data/live_ops/operator_review_result.json
data/live_ops/operator_review_report.md
```

Those files are local runtime outputs and are ignored by git.

## Integration Points

- Live Case Loop provides case context and operator-gated recommendation.
- ACPC diagnostics may provide evidence and diagnostic findings through Live Case Loop assets.
- Control Plane remains read-only and can display the latest operator review state.
- EXIM Operator Entrypoint displays last review, final decision, and case closed/open state.

## Operational Law

Models generate. Diagnostics inform. Governance constrains. Operator decides.
