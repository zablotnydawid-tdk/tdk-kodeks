from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.vma.session_recorder import (  # noqa: E402
    append_turn,
    create_session,
    finalize_session,
    load_session,
    save_report,
    save_session,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VMA real user session recorder")
    parser.add_argument("action", choices=("help", "start", "add", "finalize"))
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--session-path", default="")
    parser.add_argument("--user-input", default="")
    parser.add_argument("--assistant-output", default="")
    parser.add_argument(
        "--event-type", choices=("turn", "interruption", "recovery_attempt"), default="turn"
    )
    parser.add_argument("--notes", default="")
    parser.add_argument("--visual-reentry-required", action="store_true")
    return parser


def run(args: argparse.Namespace) -> dict:
    root = Path(args.root)

    if args.action == "help":
        return {
            "status": "help",
            "actions": ["start", "add", "finalize"],
            "required_add_parameters": ["--session-path", "--user-input or --assistant-output"],
            "examples": [
                "scripts/vma_record_session.ps1 -Action start",
                "scripts/vma_record_session.ps1 -Action add -SessionPath <path> -UserInput <text> -AssistantOutput <text>",
                "scripts/vma_record_session.ps1 -Action add -SessionPath <path> -EventType interruption -UserInput <text> -AssistantOutput <text>",
                "scripts/vma_record_session.ps1 -Action finalize -SessionPath <path>",
            ],
        }

    session_dir = root / "data" / "vma" / "sessions"
    session_dir.mkdir(parents=True, exist_ok=True)

    if args.action == "start":
        session = create_session(notes=args.notes)
        session_path = session_dir / f"{session['session_id']}.json"
        save_session(session, session_path)
        return {
            "session_path": str(session_path),
            "session_id": session["session_id"],
            "status": "started",
        }

    if not args.session_path:
        raise ValueError("SessionPath is required for add/finalize")

    session_path = Path(args.session_path)
    if args.action == "add":
        if not args.user_input and not args.assistant_output:
            raise ValueError("UserInput or AssistantOutput is required for add")
        session = load_session(session_path)
        session = append_turn(
            session,
            user_input=args.user_input,
            assistant_output=args.assistant_output,
            event_type=args.event_type,
            notes=args.notes,
            visual_reentry_required=args.visual_reentry_required,
        )
        save_session(session, session_path)
        return {
            "session_path": str(session_path),
            "turns": len(session["turns"]),
            "status": "turn-added",
        }

    session = finalize_session(load_session(session_path))
    save_session(session, session_path)
    report_path = session_path.with_suffix(".md")
    save_report(session, report_path)
    return {
        "session_path": str(session_path),
        "report_path": str(report_path),
        "turns": len(session["turns"]),
        "continuity_score": session["continuity_metrics"].get("continuity_score"),
        "topology_retention_score": session["continuity_metrics"].get(
            "topology_retention_score"
        ),
        "recovery_efficiency": session["continuity_metrics"].get("recovery_efficiency"),
        "visual_reentry_required": session["continuity_metrics"].get(
            "visual_reentry_required"
        ),
        "first_real_user_continuity_win": session["first_real_user_continuity_win"],
        "status": "finalized",
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        print(json.dumps(run(args), sort_keys=True))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"controlled-error: {exc}", file=sys.stderr)
        return 1
    except Exception:
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
