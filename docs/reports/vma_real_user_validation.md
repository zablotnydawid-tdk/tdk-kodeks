# VMA Real User Validation

This report defines the real-user validation stage for VMA continuity.

The validation moves beyond synthetic benchmark sessions by allowing the operator to manually record real conversation turns as transcript data.

## Output

The recorder produces:

- session JSON,
- Markdown report,
- continuity metrics,
- `FIRST_REAL_USER_CONTINUITY_WIN` status.

## Required Fields

Each recorded turn stores:

- `user_input`
- `assistant_output`
- `detected_structure`
- `topology_map`
- `continuity_score`
- `cognitive_load`
- `recovery_required`
- `recovery_triggered`
- `visual_reentry_required`
- `interruption_detected`
- `notes`

## Safety

No microphone, no audio recording, no cloud, no dashboard, and no sensitive data collection.

