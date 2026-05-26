# Production Safety Boundary

## Rule

Public production must not expose the operator runtime.

```text
PUBLIC:
client form, upload, status, approved report, contact

PRIVATE:
EXIM Node, Control Plane, DEMON, VMA, Operator Review, runtime state
```

## Never Public

Do not expose:

- Control Plane,
- `state/control_plane_status.json`,
- Control Plane history,
- DEMON logs,
- VMA continuity state,
- EXIM runtime state,
- Live Case internal memory,
- Operator Review raw trace,
- local scripts,
- machine start review output,
- raw uploads without access control,
- raw SQLite database,
- internal runtime reports.

## Required Public Safeguards

Before public traffic:

- validate all input,
- limit upload size,
- restrict upload file types,
- store uploads outside repo source,
- keep runtime data ignored by git,
- require operator approval before final report,
- keep `autonomous_action = false`,
- separate client-safe status from internal state,
- log enough for audit without leaking client/private runtime data.

## Decision Boundary

The system may generate:

- findings,
- risk level,
- witness report,
- recommended next actions.

The system may not autonomously:

- approve final recommendations,
- execute EMS/PV/BESS commands,
- remediate a site,
- expose private runtime state,
- trigger payment-driven release,
- perform emergency stop outside a confirmed and bounded future control design.

## Production Default

Default public case state:

```text
pending_review
```

Default runtime authority:

```text
operator_decides = true
autonomous_action = false
```

## First Deployment Principle

Ship the narrow public service path first.

Keep the operator runtime private and powerful behind it.
