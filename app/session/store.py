import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def save_session(
    raw_input: str,
    normalized_input: str,
    selected_mask: str,
    route_reason: str,
    process_result: dict,
    output_text: str,
) -> str:
    session_id = str(uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    session_data = {
        "session_id": session_id,
        "created_at": created_at,
        "input": {
            "raw": raw_input,
            "normalized": normalized_input,
        },
        "route": {
            "mask": selected_mask,
            "reason": route_reason,
        },
        "process": {
            "observation": process_result["observation"],
            "hypothesis": process_result["hypothesis"],
            "verification": process_result["verification"],
            "conclusion": process_result["conclusion"],
        },
        "output": {
            "text": output_text,
        },
    }

    sessions_dir = Path("data") / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    file_path = sessions_dir / f"{session_id}.json"
    file_path.write_text(
        json.dumps(session_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return str(file_path)
