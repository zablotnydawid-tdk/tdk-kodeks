# tdkproservice.pl Domain Deploy Runbook

## Purpose

This runbook defines the deployment preparation path for the public `tdkproservice.pl` entrypoint.

It is not an instruction to expose EXIM Node, Control Plane, DEMON, VMA, or raw runtime state.

## Preflight

Run the local production readiness check:

```powershell
.\scripts\production_readiness_check.ps1
```

The check is observe-only. It does not deploy, start services, install packages, or change DNS.

## Public Scope

Public domain may serve:

- service page,
- PV intake form,
- upload flow,
- case creation,
- client-safe status,
- approved report access,
- contact flow.

## Private Scope

Keep private:

- EXIM Operator Entrypoint,
- Control Plane,
- DEMON,
- VMA,
- Operator Review,
- raw ACPC diagnostics,
- raw uploads,
- runtime logs,
- local machine status.

## Minimal Deploy Order

1. Confirm hosting decision.
2. Confirm DNS ownership and target.
3. Confirm SSL path.
4. Confirm mail provider.
5. Confirm upload and report storage.
6. Confirm backup and log retention.
7. Run local production readiness check.
8. Stage public frontend.
9. Expose only restricted API endpoints.
10. Submit internal test case.
11. Complete manual operator review.
12. Publish first approved client report.

## Local Candidate Start

ACPC API foundation:

```bat
C:\KODEKS\run_api.bat
```

Health:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Possible frontend candidates:

```text
C:\TDK\TDK_front
C:\TDK\TDK_platform_next
C:\KODEKS\apps\web
```

Only one frontend should be selected for domain staging.

## Manual Payment Confirmation

Payment status may be recorded manually as:

```text
payment_confirmed
```

Do not add automatic payment execution or payment-triggered report release until the operator approves that scope.

## First Real Client Case

First real case criteria:

- upload limits enabled,
- input validation enabled,
- case starts as `pending_review`,
- operator review required,
- witness report generated,
- public report sanitized,
- contact path verified,
- raw EXIM/Control Plane state remains private.
