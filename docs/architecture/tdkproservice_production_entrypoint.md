# tdkproservice.pl Production Entrypoint

## Purpose

This is the first production entrypoint plan for TDK ProService / ACPC Energy Intelligence on:

```text
tdkproservice.pl
```

This is not a public EXIM runtime. The public product surface is a client-facing intake and report workflow. The private operator surface remains EXIM Node, Control Plane, DEMON, VMA, Operator Review, and human decisions.

## Strategic Boundary

```text
PUBLIC = client, form, upload, status, report, contact
PRIVATE = EXIM Node, Control Plane, DEMON, VMA, operator review, human decisions
```

Public users should see a simple service path. Operators should retain the full internal runtime and governance stack.

## Public Domain Scope

`tdkproservice.pl` may expose:

- public landing/service information,
- PV diagnostic intake form,
- file upload for client evidence,
- case creation,
- case status visible to the client,
- report availability after operator review,
- contact and follow-up request,
- limited public API endpoints needed by the public frontend.

## Private EXIM Node Scope

The following remain private and operator-only:

- EXIM Node,
- Control Plane,
- EXIM Operator Entrypoint,
- DEMON / Drift Energy Monitor,
- VMA continuity runtime,
- Live Case Loop internals,
- Operator Review Layer,
- raw runtime state,
- local recovery scripts,
- decision traces that include private operational context.

## Publicly Allowed Surface

Public endpoints may support:

- submit PV form,
- upload bounded files,
- create case,
- check sanitized case status,
- retrieve sanitized approved report,
- send contact/update request.

Public responses must be client-safe and must not expose internal runtime state.

## Publicly Forbidden Surface

Do not expose publicly:

- Control Plane,
- DEMON logs,
- VMA state,
- EXIM runtime state,
- local machine status,
- operator review internals,
- raw decision trace,
- raw uploaded evidence without access boundary,
- automation that executes EMS/PV/BESS actions,
- emergency stop or remediation commands,
- payment automation before operator approval,
- cloud orchestration without an operator decision.

## Client Flow

```text
client enters tdkproservice.pl
-> opens PV diagnostic form
-> enters site/system data
-> uploads data/photos
-> case is created
-> status = pending_review
-> operator manually reviews
-> report is approved or contact is requested
-> client receives report/status/contact
```

Initial public status should be:

```text
pending_review
```

The client must not receive final recommendations until operator approval is complete.

## Operator Flow

```text
EXIM Operator Entrypoint
-> ACPC API
-> Live Case Loop
-> Operator Review
-> Witness Report
-> approved client report / contact action
```

Operator remains the decision owner. The system may generate diagnostic findings and witness reports, but it does not approve or execute remediation autonomously.

## Minimal Production Architecture

Phase 1 production architecture:

- public frontend for `tdkproservice.pl`,
- limited API for public intake/status/report access,
- storage for uploads and reports,
- SQLite now for local/early production validation,
- Postgres later for durable multi-case production,
- manual payment confirmation,
- manual operator approval,
- private EXIM/Control Plane runtime.

Suggested boundary:

```text
Public frontend
-> restricted public API
-> case storage
-> private operator review
-> sanitized report export
```

## Security Requirements

Minimum safety requirements:

- no public Control Plane,
- no public DEMON log,
- no public runtime state,
- no automatic decisions,
- upload limits,
- input validation,
- file type allowlist,
- report access boundary,
- operator approval required,
- manual payment confirmation,
- private logs separated from client status,
- no EMS/PV/BESS control commands in public system.

## Deployment Sequence

Recommended production sequence:

1. Local production check.
2. Public frontend panel.
3. API hardening.
4. Domain staging.
5. Manual review flow.
6. First real client case.

## Decisions Requiring Confirmation

Before deployment, the operator must confirm:

- hosting,
- DNS,
- SSL,
- mail provider,
- upload storage,
- report storage,
- backup policy,
- log retention,
- public frontend candidate,
- production API runtime,
- data retention and client privacy policy.

## Operational Law

Public entrypoint collects and informs.

Private EXIM validates, traces, governs, and supports the operator.

The operator decides.
