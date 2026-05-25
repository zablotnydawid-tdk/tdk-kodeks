# VMA Real User Session Recorder

This runbook describes the first manual real-user continuity recorder for VMA.

## Scope

The recorder is manual transcript tooling only:

- no UI,
- no microphone,
- no audio recording,
- no cloud,
- no sensitive data,
- no voice analysis,
- no dashboard.

The operator manually types or pastes turns from a real conversation.

## Help

```powershell
cd C:\KODEKS
.\scripts\vma_record_session.ps1 -Action help
```

Help shows:

- `start`
- `add -SessionPath <path> -UserInput <text> -AssistantOutput <text>`
- `finalize -SessionPath <path>`
- required `add` parameters: `-SessionPath` and at least one turn text field

## Start Session

```powershell
cd C:\KODEKS
.\scripts\vma_record_session.ps1 -Action start
```

The script creates a session JSON in:

```text
data\vma\sessions\
```

## Add Turn

```powershell
.\scripts\vma_record_session.ps1 -Action add -SessionPath data\vma\sessions\<session>.json -UserInput "..." -AssistantOutput "..."
```

Optional fields:

- `-EventType turn | interruption | recovery_attempt`
- `-Notes "..."`
- `-VisualReentryRequired`

## Finalize

```powershell
.\scripts\vma_record_session.ps1 -Action finalize -SessionPath data\vma\sessions\<session>.json
```

Finalize computes continuity metrics and writes a Markdown report next to the session JSON.

## FIRST_REAL_USER_CONTINUITY_WIN

The win is achieved when:

- `continuity_score >= 0.75`
- `topology_retention_score >= 0.75`
- `recovery_efficiency >= 0.60`
- `visual_reentry_required == false`
- minimum 5 turns
- minimum 1 interruption or recovery event

## Git Boundary

Runtime outputs in `data\vma\sessions\` are ignored by Git.
