# TDK Energy Intelligence Platform Freemium Access

## Purpose

This runbook closes the public freemium flow for TDK Energy Intelligence Platform / AnchorGrid.

The public product is:

```text
10 free AnchorGrid analyses
-> paid lock
-> email payment request
-> operator confirms payment
-> operator issues API key
-> client continues analysis
```

## Public Boundary

Public:

- TDK Energy Intelligence Platform frontend
- AnchorGrid input form
- 10 free analyses
- payment/contact instructions
- API key field
- sanitized advisory output

Private:

- EXIM Node
- Control Plane
- DEMON logs
- runtime state
- operator decisions
- internal case review

Never expose private runtime state publicly.

## Domain Setup

Recommended public frontend target:

```text
tdkproservice.pl
```

Optional subdomain if the main domain remains a marketing page:

```text
platform.tdkproservice.pl
energy.tdkproservice.pl
```

Frontend environment:

```text
NEXT_PUBLIC_API_URL=https://api.tdkproservice.pl
NEXT_PUBLIC_ANCHORGRID_ACCESS_PRICE="cena ustalana indywidualnie"
```

Backend environment:

```text
ANCHORGRID_FREE_LIMIT=10
ANCHORGRID_API_KEYS=
PUBLIC_ORIGIN=https://tdkproservice.pl
```

If a subdomain is used, set `PUBLIC_ORIGIN` to that subdomain.

## Client Flow

1. Client opens the public TDK Energy Intelligence Platform.
2. Client runs up to 10 free AnchorGrid analyses.
3. After the limit, the frontend locks new analysis without an API key.
4. Client clicks `Wykup dostęp`.
5. Mail opens to `kontakt@tdkproservice.pl` with a payment/access request.
6. Operator confirms the commercial offer and payment manually.
7. Operator sends the API key to the client.
8. Client enters the key in `Klucz dostępu API`.
9. Client continues using AnchorGrid.

## Anti-Reset Boundary

The frontend localStorage counter is only a user-facing display helper.

The authoritative free usage limit is enforced by the backend and persisted in SQLite through the `anchorgrid_usage` table.

This means:

- browser refresh does not reset the limit,
- clearing localStorage does not grant a new backend allowance,
- backend restart does not reset the limit,
- valid API keys bypass the free limit after operator/payment confirmation.

Known production boundary:

- the current durable identity is based on backend client identity, primarily IP/proxy identity;
- a determined user with a different network/device can still appear as a new client;
- stronger commercial protection requires account login, verified email, or payment-bound access keys.

## Operator Flow

Generate a client key manually, for example:

```powershell
[guid]::NewGuid().ToString("N")
```

Add it to backend env:

```text
ANCHORGRID_API_KEYS=client-key-one,client-key-two
```

Restart/redeploy backend after changing keys.

Price is not hardcoded. Set it only after the operator confirms the offer:

```text
NEXT_PUBLIC_ANCHORGRID_ACCESS_PRICE="example price or offer text"
```

Send the client a short message:

```text
Dzień dobry,

płatny dostęp do TDK Energy Intelligence Platform został aktywowany.

Klucz API:
<CLIENT_KEY>

Proszę wkleić go w polu "Klucz dostępu API" w platformie i uruchomić kolejne analizy.

TDK&ProService
kontakt@tdkproservice.pl
```

## Test Plan

Local:

```powershell
cd C:\TDK\TDK_backend
set ANCHORGRID_FREE_LIMIT=10
set ANCHORGRID_API_KEYS=test-paid-key

cd C:\TDK\TDK_platform_next
set NEXT_PUBLIC_API_URL=http://127.0.0.1:8010
npm run build
npm run dev -- --hostname 127.0.0.1 -p 3002
```

Manual browser checks:

- counter shows `10/10` on a clean browser profile,
- each free analysis decreases local free counter,
- after 10 analyses the UI shows payment/access lock,
- `Wykup dostęp` opens an email to `kontakt@tdkproservice.pl`,
- entering a valid API key unlocks analysis,
- backend with valid API key reports `api_key_valid=true`.

## Safety Notes

- No automatic remediation.
- No automatic payment confirmation.
- No public Control Plane.
- No public DEMON.
- No public EXIM runtime state.
- Operator remains responsible for paid access and client communication.
