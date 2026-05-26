# ACPC ZIP Inventory Compare

## Scope

Inventory and architecture comparison for four local ACPC ZIP packages:

- `C:\Users\zablo\Desktop\1acpc_mvp_runtime.zip`
- `C:\Users\zablo\Desktop\acpc_mvp_runtime.zip`
- `C:\Users\zablo\Desktop\acpc_energy_diagnostic_mvp.zip`
- `C:\Users\zablo\Downloads\acpc_live_ingest_gateway.zip`

Rules for this pass:

- no extraction into the current repository,
- no merge,
- no code modification,
- no commit,
- compare only by ZIP metadata and file manifests.

`unzip` is not available in this environment, so inspection was performed with Python standard-library `zipfile` without extracting package contents.

## Inventory Summary

| Package | Entries | Uncompressed bytes | Primary role | Merge posture |
| --- | ---: | ---: | --- | --- |
| `1acpc_mvp_runtime.zip` | 12 | 23,356 | ACPC core runtime proof | Duplicate of `acpc_mvp_runtime.zip`; keep one source only |
| `acpc_mvp_runtime.zip` | 12 | 23,356 | ACPC core runtime proof | Candidate source for runtime review |
| `acpc_energy_diagnostic_mvp.zip` | 23 | 57,415 | Energy diagnostic MVP | Candidate source after cache removal |
| `acpc_live_ingest_gateway.zip` | 24 | 36,923 | Live ingest gateway MVP | Candidate source after cache removal |

## Duplicate Detection

`acpc_mvp_runtime.zip` and `1acpc_mvp_runtime.zip` are duplicates by manifest:

- same entry count: `12`,
- same total uncompressed bytes: `23,356`,
- identical file paths,
- identical per-entry file sizes,
- identical per-entry CRC values.

Hash calculation was not used because the approval request for SHA256 was rejected. Manifest/CRC comparison is sufficient for content-level duplicate confirmation inside the ZIP entries.

Runtime duplicate manifest:

```text
acpc_mvp_runtime/acpc/
acpc_mvp_runtime/tests/
acpc_mvp_runtime/README.md
acpc_mvp_runtime/docs_architecture.md
acpc_mvp_runtime/pyproject.toml
acpc_mvp_runtime/acpc/__init__.py
acpc_mvp_runtime/acpc/model.py
acpc_mvp_runtime/acpc/state.py
acpc_mvp_runtime/acpc/wal.py
acpc_mvp_runtime/acpc/snapshot.py
acpc_mvp_runtime/acpc/runtime.py
acpc_mvp_runtime/tests/test_acpc_runtime.py
```

## File Trees

### `1acpc_mvp_runtime.zip`

```text
acpc_mvp_runtime/
├── README.md
├── docs_architecture.md
├── pyproject.toml
├── acpc/
│   ├── __init__.py
│   ├── model.py
│   ├── state.py
│   ├── wal.py
│   ├── snapshot.py
│   └── runtime.py
└── tests/
    └── test_acpc_runtime.py
```

### `acpc_mvp_runtime.zip`

```text
acpc_mvp_runtime/
├── README.md
├── docs_architecture.md
├── pyproject.toml
├── acpc/
│   ├── __init__.py
│   ├── model.py
│   ├── state.py
│   ├── wal.py
│   ├── snapshot.py
│   └── runtime.py
└── tests/
    └── test_acpc_runtime.py
```

### `acpc_energy_diagnostic_mvp.zip`

```text
acpc_energy_diagnostic_mvp/
├── README.md
├── ARCHITECTURE.md
├── acpc_energy/
│   ├── __init__.py
│   ├── models.py
│   ├── normalization.py
│   ├── rules.py
│   ├── reducer.py
│   ├── reports.py
│   ├── diagnostic_engine.py
│   └── __pycache__/
│       ├── __init__.cpython-313.pyc
│       ├── diagnostic_engine.cpython-313.pyc
│       ├── models.cpython-313.pyc
│       ├── reducer.cpython-313.pyc
│       ├── rules.cpython-313.pyc
│       ├── normalization.cpython-313.pyc
│       └── reports.cpython-313.pyc
├── tests/
│   ├── test_pv_diagnostic.py
│   └── __pycache__/
│       └── test_pv_diagnostic.cpython-313-pytest-9.0.2.pyc
├── examples/
│   └── run_pv_diagnosis.py
└── .pytest_cache/
    ├── README.md
    ├── .gitignore
    ├── CACHEDIR.TAG
    └── v/cache/nodeids
```

### `acpc_live_ingest_gateway.zip`

```text
acpc_live_ingest_gateway/
├── README.md
├── acpc_live_ingest_gateway/
│   ├── __init__.py
│   ├── events.py
│   ├── clock.py
│   ├── wal.py
│   ├── cache.py
│   ├── normalizers.py
│   ├── gateway.py
│   ├── replay.py
│   └── __pycache__/
│       ├── __init__.cpython-313.pyc
│       ├── events.cpython-313.pyc
│       ├── gateway.cpython-313.pyc
│       ├── cache.cpython-313.pyc
│       ├── clock.cpython-313.pyc
│       ├── normalizers.cpython-313.pyc
│       ├── wal.cpython-313.pyc
│       └── replay.cpython-313.pyc
├── tests/
│   ├── test_gateway.py
│   └── __pycache__/
│       └── test_gateway.cpython-313-pytest-9.0.2.pyc
├── examples/
│   └── run_gateway_smoke_test.py
└── .pytest_cache/
    ├── README.md
    ├── .gitignore
    ├── CACHEDIR.TAG
    └── v/cache/nodeids
```

## Classification

### A. Core Runtime Modules

From runtime package:

- `acpc_mvp_runtime/acpc/model.py`
- `acpc_mvp_runtime/acpc/state.py`
- `acpc_mvp_runtime/acpc/wal.py`
- `acpc_mvp_runtime/acpc/snapshot.py`
- `acpc_mvp_runtime/acpc/runtime.py`

Likely responsibilities by filename:

- model definitions,
- state representation,
- write-ahead log,
- snapshot persistence,
- runtime orchestration.

### B. Ingest Gateway Modules

From live ingest package:

- `acpc_live_ingest_gateway/acpc_live_ingest_gateway/events.py`
- `acpc_live_ingest_gateway/acpc_live_ingest_gateway/clock.py`
- `acpc_live_ingest_gateway/acpc_live_ingest_gateway/wal.py`
- `acpc_live_ingest_gateway/acpc_live_ingest_gateway/cache.py`
- `acpc_live_ingest_gateway/acpc_live_ingest_gateway/normalizers.py`
- `acpc_live_ingest_gateway/acpc_live_ingest_gateway/gateway.py`
- `acpc_live_ingest_gateway/acpc_live_ingest_gateway/replay.py`

Likely responsibilities by filename:

- event schema,
- deterministic/local clock,
- ingestion write-ahead log,
- local cache,
- input normalization,
- gateway entrypoint,
- replay/recovery support.

### C. Energy Diagnostic Modules

From diagnostic package:

- `acpc_energy_diagnostic_mvp/acpc_energy/models.py`
- `acpc_energy_diagnostic_mvp/acpc_energy/normalization.py`
- `acpc_energy_diagnostic_mvp/acpc_energy/rules.py`
- `acpc_energy_diagnostic_mvp/acpc_energy/reducer.py`
- `acpc_energy_diagnostic_mvp/acpc_energy/reports.py`
- `acpc_energy_diagnostic_mvp/acpc_energy/diagnostic_engine.py`

Likely responsibilities by filename:

- energy case models,
- input normalization,
- diagnostic rules,
- reducer/state aggregation,
- reports,
- diagnostic orchestration.

### D. Tests

- `acpc_mvp_runtime/tests/test_acpc_runtime.py`
- `acpc_energy_diagnostic_mvp/tests/test_pv_diagnostic.py`
- `acpc_live_ingest_gateway/tests/test_gateway.py`

These should be reviewed and ported into KODEKS tests only after source modules are reviewed. They may need fallback runner compatibility because the current environment lacks `pytest`.

### E. Examples

- `acpc_energy_diagnostic_mvp/examples/run_pv_diagnosis.py`
- `acpc_live_ingest_gateway/examples/run_gateway_smoke_test.py`

Examples should be preserved as smoke-test references or converted into `scripts/` commands after module integration.

### F. Ignore / Do Not Merge

Do not merge generated caches:

```text
__pycache__/
.pytest_cache/
*.pyc
```

Specific ignored entries:

```text
acpc_energy_diagnostic_mvp/.pytest_cache/**
acpc_energy_diagnostic_mvp/tests/__pycache__/**
acpc_energy_diagnostic_mvp/acpc_energy/__pycache__/**
acpc_live_ingest_gateway/.pytest_cache/**
acpc_live_ingest_gateway/tests/__pycache__/**
acpc_live_ingest_gateway/acpc_live_ingest_gateway/__pycache__/**
```

## Architecture Compare Against Current KODEKS

Current KODEKS already has these relevant layers:

```text
app/final_axis              runtime proof, state/reducer/logging/projection
app/live_ops                live case loop
app/monitoring              drift energy monitor
app/drift_energy_monitor    DEMON_CORE package
app/anchorgrid              energy/grid advisory runtime
knowledge                   EXIM Knowledge OS
scripts/run_tests.py        standard-library fallback test runner
scripts/exim_operator_entrypoint.ps1
```

Comparison:

| ACPC package | Closest KODEKS layer | Fit | Notes |
| --- | --- | --- | --- |
| `acpc_mvp_runtime` | `app/final_axis`, `data/final_axis`, `knowledge/risk_mapper.py` | Medium-high | Runtime/WAL/snapshot concepts overlap with Final Axis state/logging. Needs boundary review before adding a new runtime package. |
| `acpc_live_ingest_gateway` | `app/live_ops`, `knowledge/document_ingestor.py`, `scripts/exim_operator_entrypoint.ps1` | High | Gateway/replay/WAL concepts fit local-first ingest and live case pipeline. Strong candidate after duplicate runtime is resolved. |
| `acpc_energy_diagnostic_mvp` | `app/anchorgrid`, `app/monitoring/drift_energy_monitor.py`, `app/engine`, `app/output` | High | Energy diagnostics align with PV/EMS/BESS/client report flow. Must be reconciled with existing AnchorGrid and report builder. |

Potential overlap risks:

- ACPC runtime WAL vs KODEKS Final Axis logging.
- ACPC gateway WAL/cache vs KODEKS local storage/session/data conventions.
- ACPC energy reports vs existing `app/output/report_builder.py` and `knowledge/report_generator.py`.
- ACPC diagnostic rules vs `app/anchorgrid/engine.py` and DEMON rules.
- Tests may assume `pytest`; KODEKS currently has fallback runner because `pytest` is not installed.

## Integration Priority

1. **Energy Diagnostic MVP**
   - Highest immediate business value for PV/EMS/BESS/253V/client reports.
   - Candidate for isolated review under a new namespace before touching existing report flow.

2. **Live Ingest Gateway**
   - Strong fit for local-first ingestion and replay.
   - Should be integrated after diagnostic model boundaries are clear.

3. **ACPC Core Runtime**
   - Important architectural layer, but overlaps with Final Axis runtime.
   - Review as design/reference first; avoid parallel runtime duplication until the boundary is explicit.

4. **Duplicate runtime ZIP**
   - Keep only one source package for future extraction.
   - Prefer `acpc_mvp_runtime.zip`; ignore `1acpc_mvp_runtime.zip` unless its filename is needed as an external provenance marker.

## Risk List

- **Duplicate runtime package**: two ZIPs contain identical runtime manifests; merging both would duplicate files.
- **Generated caches inside ZIPs**: energy and gateway packages include `.pytest_cache`, `__pycache__`, and `.pyc` files.
- **Runtime overlap**: ACPC runtime may duplicate existing Final Axis runtime responsibilities.
- **Report overlap**: ACPC energy reports may conflict with existing KODEKS report and Knowledge OS report generators.
- **Test environment mismatch**: ZIP tests appear to come from Python 3.13 / pytest 9 cache artifacts, while current KODEKS environment uses `python3 3.12.3` and no installed `pytest`.
- **Unknown dependencies**: package internals were not extracted or reviewed in this pass, so imports/dependencies remain unknown.
- **No hash confirmation**: SHA256 was not executed because approval was rejected; duplicate confirmation is manifest/CRC based.

## Proposed Target Paths

Merge plan only. Do not apply until a dedicated extraction/review pass.

### Core Runtime

Preferred target if accepted as separate runtime:

```text
app/acpc_runtime/
tests/test_acpc_runtime.py
docs/architecture/acpc_runtime.md
```

Alternative if folded into Final Axis:

```text
app/final_axis/acpc_runtime_adapter.py
app/final_axis/acpc_wal.py
app/final_axis/acpc_snapshot.py
```

Recommendation: start as `app/acpc_runtime/` in a sandbox branch, then decide whether to fold into Final Axis.

### Live Ingest Gateway

Preferred target:

```text
app/live_ingest/
app/live_ingest/events.py
app/live_ingest/clock.py
app/live_ingest/wal.py
app/live_ingest/cache.py
app/live_ingest/normalizers.py
app/live_ingest/gateway.py
app/live_ingest/replay.py
tests/test_live_ingest_gateway.py
scripts/run_live_ingest_smoke.py
```

Integration points:

```text
app/live_ops/live_case_loop.py
knowledge/document_ingestor.py
scripts/exim_operator_entrypoint.ps1
```

### Energy Diagnostic

Preferred target:

```text
app/energy_diagnostic/
app/energy_diagnostic/models.py
app/energy_diagnostic/normalization.py
app/energy_diagnostic/rules.py
app/energy_diagnostic/reducer.py
app/energy_diagnostic/reports.py
app/energy_diagnostic/diagnostic_engine.py
tests/test_energy_diagnostic.py
scripts/run_energy_diagnostic_smoke.py
```

Integration points:

```text
app/anchorgrid/
app/monitoring/drift_energy_monitor.py
knowledge/report_context_builder.py
knowledge/report_generator.py
app/output/report_builder.py
```

### Examples

Convert examples into scripts only after module imports are verified:

```text
scripts/run_pv_diagnosis.py
scripts/run_live_ingest_gateway_smoke.py
```

### Ignore Rules

Do not extract or stage:

```text
**/__pycache__/**
**/.pytest_cache/**
**/*.pyc
```

## Test Plan

Before any future merge:

1. Extract each package to a temporary folder outside the repo.
2. Inspect imports and dependencies.
3. Run package tests in isolation.
4. Remove generated caches before staging any source.
5. Port tests into KODEKS naming and fallback runner style.
6. Run:

```bash
python3 -m compileall app knowledge scripts tests
python3 scripts/run_tests.py tests
```

7. If `pytest` becomes available:

```bash
python3 -m pytest tests
```

8. After integration with KODEKS layers, run focused tests:

```bash
python3 scripts/run_tests.py tests/test_knowledge_ingestion.py
python3 scripts/run_tests.py tests/test_live_case_loop.py
python3 scripts/run_tests.py tests/test_drift_energy_monitor.py
python3 scripts/run_tests.py tests/test_anchorgrid_engine.py
```

9. Run operator smoke:

```powershell
.\scripts\exim_operator_entrypoint.ps1
```

## Stop Point

This document stops before extraction or merge.

No package files were extracted into the repository during this pass.

---

## Selective Merge Execution

Status: completed after inventory review.

Rules applied:

- ZIP blobs were not committed or copied into the repository.
- `1acpc_mvp_runtime.zip` was not merged because it is a duplicate of `acpc_mvp_runtime.zip`.
- `.pytest_cache`, `__pycache__`, and `*.pyc` were excluded from the ZIP merge.
- Python-generated `__pycache__` from verification was removed before commit.

## Merged Files

### ACPC Core Runtime

Source package:

```text
C:\Users\zablo\Desktop\acpc_mvp_runtime.zip
```

Target:

```text
src/acpc/runtime/
tests/runtime/
```

Merged:

```text
src/acpc/runtime/__init__.py
src/acpc/runtime/model.py
src/acpc/runtime/state.py
src/acpc/runtime/wal.py
src/acpc/runtime/snapshot.py
src/acpc/runtime/runtime.py
tests/runtime/test_acpc_runtime.py
```

### ACPC Live Ingest Gateway

Source package:

```text
C:\Users\zablo\Downloads\acpc_live_ingest_gateway.zip
```

Target:

```text
src/acpc/ingest/
tests/ingest/
```

Merged:

```text
src/acpc/ingest/__init__.py
src/acpc/ingest/events.py
src/acpc/ingest/clock.py
src/acpc/ingest/wal.py
src/acpc/ingest/cache.py
src/acpc/ingest/normalizers.py
src/acpc/ingest/gateway.py
src/acpc/ingest/replay.py
tests/ingest/test_gateway.py
```

### ACPC Energy PV Diagnostics

Source package:

```text
C:\Users\zablo\Desktop\acpc_energy_diagnostic_mvp.zip
```

Target:

```text
src/acpc/energy/pv_diagnostics/
tests/energy/
```

Merged:

```text
src/acpc/energy/pv_diagnostics/__init__.py
src/acpc/energy/pv_diagnostics/models.py
src/acpc/energy/pv_diagnostics/normalization.py
src/acpc/energy/pv_diagnostics/rules.py
src/acpc/energy/pv_diagnostics/reducer.py
src/acpc/energy/pv_diagnostics/reports.py
src/acpc/energy/pv_diagnostics/diagnostic_engine.py
tests/energy/test_pv_diagnostic.py
```

### Package Markers

Added:

```text
src/__init__.py
src/acpc/__init__.py
src/acpc/energy/__init__.py
```

## Omitted Files

Omitted duplicate:

```text
C:\Users\zablo\Desktop\1acpc_mvp_runtime.zip
```

Omitted generated caches:

```text
**/.pytest_cache/**
**/__pycache__/**
**/*.pyc
```

Omitted examples for this pass:

```text
acpc_energy_diagnostic_mvp/examples/run_pv_diagnosis.py
acpc_live_ingest_gateway/examples/run_gateway_smoke_test.py
```

Reason: examples should become explicit smoke scripts only after import paths and operator command names are approved.

Omitted upstream package metadata/docs for this pass:

```text
pyproject.toml
README.md
ARCHITECTURE.md
docs_architecture.md
```

Reason: KODEKS keeps integration documentation in `docs/architecture/`; upstream docs were summarized here instead of copied verbatim.

## Integration Adjustments

Only import paths were adjusted in merged tests:

```text
from acpc -> from src.acpc.runtime
from acpc_live_ingest_gateway -> from src.acpc.ingest
from acpc_energy -> from src.acpc.energy.pv_diagnostics
```

Runtime/source logic from the selected ZIP modules was not intentionally refactored.

## Test Results

Required command:

```bash
python -m compileall src tests
```

Result:

```text
FAIL: python command not found in this WSL/bash environment
```

Available equivalent:

```bash
python3 -m compileall src tests
```

Result:

```text
PASS
```

Pytest:

```bash
python3 -m pytest tests/runtime tests/ingest tests/energy
```

Result:

```text
FAIL: No module named pytest
```

Fallback runner:

```bash
python3 scripts/run_tests.py tests/runtime tests/ingest tests/energy
```

Result:

```text
PASS: 12 passed, 0 failed, 0 skipped
```

ACPC test coverage executed:

```text
tests/runtime/test_acpc_runtime.py      4 passed
tests/ingest/test_gateway.py           4 passed
tests/energy/test_pv_diagnostic.py     4 passed
```

## Post-Merge Risk List

- `python` command is unavailable; validation currently requires `python3`.
- `pytest` is unavailable; validation currently relies on `scripts/run_tests.py`.
- ACPC runtime introduces a separate runtime namespace under `src/acpc/runtime`; future work must decide whether it remains separate or receives an adapter into `app/final_axis`.
- ACPC ingest WAL/cache/replay may overlap with existing KODEKS local storage/session conventions.
- ACPC PV diagnostics may overlap with `app/anchorgrid` and existing energy reporting; integration into user-facing reports should remain operator-gated.
- Upstream examples were not ported; dedicated smoke scripts can be added in a later pass.
