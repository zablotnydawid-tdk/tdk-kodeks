from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from knowledge.ingestion_engine import run_knowledge_os, write_knowledge_os_result


def main() -> int:
    parser = argparse.ArgumentParser(description="EXIM knowledge ingestion engine")
    parser.add_argument("document", help="Path to local PDF/text/markdown/json/csv document")
    parser.add_argument("--output", default="", help="Optional JSON output path")
    parser.add_argument("--report", default="", help="Optional markdown operator report path")
    parser.add_argument("--max-chars", type=int, default=900)
    args = parser.parse_args()

    result = run_knowledge_os(args.document, max_chars=args.max_chars)
    payload = result.as_dict()
    if args.output:
        write_knowledge_os_result(result, args.output)
    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(result.operator_report_markdown, encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
