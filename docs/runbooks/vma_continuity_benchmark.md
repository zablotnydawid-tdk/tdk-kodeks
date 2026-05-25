# VMA Continuity Benchmark

This runbook describes the operator command for the first measurable VMA continuity proof.

## Command

```powershell
cd C:\KODEKS
.\scripts\vma_continuity_benchmark.ps1
```

## Dependency

The command needs either:

- Windows Python available as `python`, `py`, or `.venv\Scripts\python.exe`, or
- WSL interop available through `wsl.exe` with `.venv\bin\python`.

If neither runtime is available from Windows PowerShell, the command exits with code `2`.

## Flow

The command:

1. reads `sample_data\vma_continuity_session.json`,
2. runs the VMA continuity benchmark,
3. writes a continuity report JSON,
4. writes a summary Markdown file,
5. writes the continuity state update,
6. prints the benchmark metrics in the terminal.

## Outputs

Runtime outputs are written to:

```text
data\vma\vma_continuity_report.json
data\vma\vma_continuity_summary.md
data\vma\vma_continuity_state.json
```

These files are runtime artifacts and are ignored by Git.

## Terminal Metrics

The command prints:

- `continuity_score`
- `topology_retention_score`
- `recovery_efficiency`
- `recursive_stability`
- `visual_reentry_required`
- `FIRST_REAL_CONTINUITY_WIN`

## Scope Boundary

This command does not add UI, dashboard frontend, cloud runtime, SaaS, multimodal sync, enterprise telemetry, adaptive pacing AI, full copilot behavior, live orchestration, cognition mesh, or autonomous reasoning.

It is one operator-driven continuity benchmark command.
