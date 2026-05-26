# tdkproservice.pl Domain Readiness Alignment

## Purpose

This note aligns the existing local ACPC / EXIM / TDK assets with the real public entrypoint:

```text
tdkproservice.pl
```

No deploy is performed here. No DNS, SSL, hosting, mail, or production service is changed. This is readiness alignment only.

## Existing Assets

### Domain

```text
tdkproservice.pl
```

Status: real public domain exists, but deployment target and DNS routing still require operator confirmation.

### Mail

```text
kontakt@tdkproservice.pl
```

Status: real contact address exists. Mail provider, inbound routing, outbound transactional flow, and retention policy still require confirmation before production workflow.

### API

Current API foundation:

```text
C:\KODEKS\apps\api
C:\KODEKS\run_api.bat
```

Status: real local ACPC API foundation exists. It supports PV diagnostic intake, witness report generation, SQLite persistence, report history, and Markdown export.

### Frontend Candidates

```text
C:\TDK\TDK_front
C:\TDK\TDK_platform_next
```

`TDK_front`:

- Vite + React,
- lightweight gateway,
- login/subscription/module/GPT bridge direction,
- static hosting friendly,
- better suited to internal/operator gateway unless heavily simplified for public clients.

`TDK_platform_next`:

- Next.js + React + Tailwind,
- named as TDK Energy Intelligence Platform,
- already oriented toward production frontend and AnchorGrid-style analysis,
- better candidate for first public `tdkproservice.pl` frontend.

### Local Runtime

Private local runtime assets:

- EXIM Node,
- Control Plane,
- EXIM Operator Entrypoint,
- Live Case Loop,
- Operator Review Layer,
- ACPC diagnostics,
- DEMON / Drift Energy Monitor,
- VMA continuity state.

Status: real local operator stack exists. It must remain private.

### Report Pipeline

Existing report path:

```text
PV intake
-> ACPC diagnostics
-> witness report
-> pending_review
-> operator review
-> approved/sanitized report
```

Status: local report generation is real. Public report access still needs a sanitized report boundary and access model.

### Operator Workflow

Operator flow exists through:

```text
C:\KODEKS\scripts\exim_operator_entrypoint.ps1
C:\KODEKS\scripts\live_case_demo.ps1
C:\KODEKS\scripts\operator_review_demo.ps1
C:\KODEKS\scripts\production_readiness_check.ps1
```

Status: operator workflow is real and terminal-first.

## Recommended Public Structure

### PUBLIC

The public `tdkproservice.pl` surface should contain:

- homepage,
- PV intake form,
- bounded upload,
- report status,
- contact,
- manual review flow presented as a service promise.

Public copy should be simple:

```text
submit data
-> expert review
-> witness-backed report
-> contact / next step
```

### PRIVATE

The private operator environment remains:

- EXIM Node,
- Control Plane,
- DEMON,
- runtime telemetry,
- continuity state,
- operator decisions,
- raw uploads and diagnostic evidence,
- raw decision traces.

## Frontend Recommendation

### Recommended First Public Frontend

Use:

```text
C:\TDK\TDK_platform_next
```

Reason:

- it is already named and framed as the TDK Energy Intelligence Platform,
- Next.js is better for a public domain entrypoint, routing, SEO, landing content, and future server-side boundaries,
- the existing project structure has public-platform components rather than only gateway/admin concepts,
- it can present a clean client path without exposing EXIM internals.

### Recommended Internal / Operator Frontend

Keep:

```text
C:\TDK\TDK_front
```

as internal/operator-oriented or later admin/gateway surface.

Reason:

- current README describes login, subscription, modules, and GPT bridge,
- it reads more like an authenticated gateway than a first public client intake,
- exposing it first risks mixing public client experience with internal module/operator flows.

## Production Boundaries

Required boundaries:

- no public runtime state,
- no public Control Plane,
- no public DEMON,
- no public VMA continuity state,
- no public EXIM Operator Entrypoint,
- no raw decision trace in public responses,
- no autonomous remediation,
- operator approval required,
- public report must be sanitized and intentionally released.

The public system may accept data and show `pending_review`. It must not decide or remediate.

## Missing Production Decisions

The following decisions are still required:

- hosting,
- SSL,
- DNS routing,
- backup,
- mail flow,
- upload limits,
- storage retention.

Additional decisions likely needed before first client:

- public API base URL,
- maximum upload size,
- allowed upload file types,
- report access method,
- client privacy notice,
- incident/contact escalation path.

## Suggested First Public Flow

```text
Klient:
tdkproservice.pl
-> formularz
-> upload
-> pending_review
-> operator review
-> report
-> kontakt
```

Client status should initially expose only:

- case received,
- pending review,
- awaiting operator contact,
- report ready after approval.

## Readiness Assessment

### Already Real

- domain exists,
- contact mail exists,
- ACPC API foundation exists,
- local witness report generation exists,
- SQLite persistence exists,
- Operator Review Layer exists,
- EXIM/Control Plane operator stack exists,
- production safety boundary docs exist,
- production readiness check exists.

### Still Prototype / Needs Hardening

- public frontend is not yet selected and staged,
- public upload limits are not enforced at production boundary,
- sanitized public report access is not implemented,
- mail flow is not wired into the case lifecycle,
- backup and retention are not decided,
- SSL/DNS/hosting are not confirmed,
- Postgres migration is future work.

### Can Serve a First Client After Minimal Staging

The stack can support a first manually handled client case after:

1. selecting `TDK_platform_next` as the public frontend candidate,
2. connecting a restricted public PV form to ACPC API,
3. keeping status as `pending_review`,
4. routing review through the private operator workflow,
5. releasing only sanitized report/contact output.

## Recommended Frontend Candidate

```text
C:\TDK\TDK_platform_next
```

Use it as the first public `tdkproservice.pl` candidate.

Keep `C:\TDK\TDK_front` internal/operator-oriented until the public service boundary is stable.

## Recommended Next Deployment Step

Do a local staging alignment:

```text
TDK_platform_next
-> restricted ACPC API endpoint
-> pending_review case
-> private Operator Review
-> sanitized report/contact output
```

Then choose hosting, DNS, SSL, mail, storage, backup, and retention before exposing public traffic.
