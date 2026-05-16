# Order Storage Migration Plan

## Current flow

KODEKS currently uses a manual approval flow that must remain unchanged:

`form -> order JSON -> payment instruction -> admin confirmation -> PDF generation -> client link`

The active storage is still filesystem JSON through `FileSystemOrderStore`.
Orders are saved under `data/orders/`, reports are generated under
`data/reports/`, and the admin panel decides whether to show `GENERUJ` or
`Pobierz PDF` based on `pdf_url`.

## Current order model

The current order dict is created by `/form-analyze` and later updated by
`/admin/generate/{order_id}`.

Current fields:

| JSON field | Current meaning |
| --- | --- |
| `order_id` | Public order id, format `KODEKS-YYYYMMDD-XXXXXX`. |
| `status` | Business state, currently `waiting_for_payment` or `paid_generated`. |
| `created_at` | Local ISO timestamp with seconds precision. |
| `email` | Client email from form. |
| `consumption_kwh` | Client electricity consumption input. |
| `price_per_kwh` | Client energy price input. |
| `pv_power_kw` | Client PV installation power input. |
| `pv_monthly_production_kwh` | Client monthly PV production input. |
| `amount` | Display amount from payment configuration, for example `39,99 zl`. |
| `pdf_url` | Public report link, null before generation. |
| `pdf_path` | Local generated report path, null before generation. |
| `base_url` | Request base URL captured when the form was submitted. |
| `generated_at` | Added after manual PDF generation. |

No persistent production order JSON files were present in `data/orders/` during
this preparation pass, so the model above is based on the live code path and the
local test order created during FileSystemOrderStore verification.

## Render Free risk

Render Free local filesystem can be temporary. That makes `data/orders/` and
`data/reports/` risky for production because a restart or redeploy can remove:

- pending orders,
- generated PDF files,
- history needed by the admin panel,
- report links already sent to customers.

The first migration goal is durability, not new business behavior.

## Proposed SQL schema

Minimal PostgreSQL/Supabase table:

```sql
create table if not exists orders (
  id text primary key,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  status text not null,
  email text not null,
  input_data jsonb not null default '{}'::jsonb,
  analysis_text text,
  report_path text,
  report_url text,
  generated_at timestamptz,
  payment_status text not null default 'waiting_for_payment',
  payment_method text,
  notes text
);

create index if not exists orders_created_at_idx on orders (created_at desc);
create index if not exists orders_status_idx on orders (status);
create index if not exists orders_payment_status_idx on orders (payment_status);
```

Optional trigger for `updated_at` should be added only when the database
migration is actually implemented.

## JSON to SQL mapping

| Current JSON | SQL target | Notes |
| --- | --- | --- |
| `order_id` | `id` | Keep exact public ID. Do not introduce a new visible ID. |
| `created_at` | `created_at` | Parse ISO string; fallback to import timestamp if missing. |
| generated update time | `updated_at` | Set on every update. |
| `status` | `status` | Preserve values exactly. |
| `email` | `email` | Preserve as submitted. |
| `consumption_kwh` | `input_data.consumption_kwh` | Store technical inputs in JSONB first. |
| `price_per_kwh` | `input_data.price_per_kwh` | Store technical inputs in JSONB first. |
| `pv_power_kw` | `input_data.pv_power_kw` | Store technical inputs in JSONB first. |
| `pv_monthly_production_kwh` | `input_data.pv_monthly_production_kwh` | Store technical inputs in JSONB first. |
| `amount` | `input_data.amount` | Keep current payment display value. |
| `base_url` | `input_data.base_url` | Useful for audit/debug; not core business state. |
| derived by `build_analysis_text_from_order` | `analysis_text` | Can be filled during import or generation. |
| `pdf_path` | `report_path` | Keep local path while filesystem reports are active. |
| `pdf_url` | `report_url` | Public client/admin URL. |
| `generated_at` | `generated_at` | Null until admin generation. |
| `status == waiting_for_payment` | `payment_status` | Start as `waiting_for_payment`. |
| `status == paid_generated` | `payment_status` | For imported generated orders, use `paid_confirmed`. |
| not present | `payment_method` | Future field: `blik`, `transfer`, `p24`, etc. |
| not present | `notes` | Future admin/CRM notes. |

For compatibility, a future `SupabaseOrderStore` should convert SQL rows back
to the existing dict shape expected by `server.py`:

```json
{
  "order_id": "KODEKS-...",
  "status": "...",
  "created_at": "...",
  "email": "...",
  "consumption_kwh": 0,
  "price_per_kwh": 0,
  "pv_power_kw": 0,
  "pv_monthly_production_kwh": 0,
  "amount": "...",
  "pdf_url": null,
  "pdf_path": null,
  "base_url": "..."
}
```

## Migration order

1. Keep `FileSystemOrderStore` active.
2. Add database table in Supabase/PostgreSQL.
3. Export existing `data/orders/*.json` into a migration script or one-off job.
4. Import JSON orders into SQL with `id = order_id`.
5. Verify row counts and sample orders against JSON.
6. Add read-only `SupabaseOrderStore` tests without wiring it into `server.py`.
7. Run dual-read verification in a local branch: compare filesystem result vs SQL result.
8. During a short maintenance window, switch `server.py` store construction from filesystem to SQL.
9. Keep JSON files as backup until production behavior is verified.
10. Move report files to durable object storage in a separate phase.

## No-downtime approach

The lowest-risk path is not a big-bang rewrite:

1. Keep filesystem active while SQL table is prepared.
2. Backfill SQL from current JSON files.
3. Freeze writes briefly only during the final delta import, if needed.
4. Switch storage adapter once SQL has all current orders.
5. Keep JSON backup and old code path available for rollback.

Because current order volume is expected to be low during MVP/manual flow, the
final delta window can be short and operationally simple.

## Existing JSON files

Existing JSON files should not be deleted during migration. Treat them as the
source of truth until SQL import is verified. After cutover, keep a dated backup
archive of `data/orders/` and do not remove it until several successful
production orders have passed through the new store.

If an imported JSON lacks newer fields, use safe defaults:

- `report_url = pdf_url`,
- `report_path = pdf_path`,
- `payment_status = waiting_for_payment` unless the order is already generated,
- `input_data = all original form and payment display fields`.

## Rollback plan

Rollback should be adapter-level:

1. Stop using the SQL adapter.
2. Restore `FileSystemOrderStore` as the active store.
3. If SQL accepted new orders during the failed window, export those rows back to
   JSON using the old order dict shape.
4. Confirm `/admin/orders` shows all expected orders.
5. Confirm generated orders still have `pdf_url` and do not regenerate PDFs.

Do not rollback by changing engine, PDF, SMTP, DNS, or payment logic.

## Future SupabaseOrderStore contract

Future implementation should keep the same methods:

- `create_order(data)`
- `list_orders()`
- `get_order(order_id)`
- `update_order(order_id, data)`
- `mark_generated(order_id, pdf_url, pdf_path=None)`

It must return dicts compatible with the current `server.py`, so endpoint HTML
and manual admin flow do not need to change during the storage migration.
