#!/usr/bin/env python3
"""Create contest-mode manifests and audit templates without fetching the web."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def write_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--contest", required=True)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--mode", choices=["training", "live", "posthoc"], required=True)
    parser.add_argument("--rules-url", action="append", default=[])
    parser.add_argument("--deadline", default="unknown")
    args = parser.parse_args()
    root = args.project_dir
    for name in ("data/raw", "data/processed", "code", "results", "figures", "paper", "reports", "support", "environment"):
        (root / name).mkdir(parents=True, exist_ok=True)
    manifest = {
        "contest": args.contest,
        "year": args.year,
        "mode": args.mode,
        "deadline": args.deadline,
        "rules_urls": args.rules_url,
        "rules_verified_at": None,
        "rules_snapshot_file": "reports/contest_rules_snapshot.md",
        "live_mode_policy": "static-authoritative-sources-only" if args.mode == "live" else "not-applicable",
        "submission_state": "draft",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (root / "contest_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_if_missing(root / "reports/contest_rules_snapshot.md", "# Contest rules snapshot\n\nRecord the official source, access time, rule version, page limit, AI policy, submission method, deadline/time zone, and unresolved items. Do not mark this file verified until every field is checked.\n")
    write_if_missing(root / "reports/data_audit.md", "# Data audit\n\n| Dataset | Source | License/permission | Rows/columns | Units | Missing/outlier handling | Leakage risk | Hash |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n")
    write_if_missing(root / "reports/traceability.md", "# Traceability\n\n| Subproblem | Data | Model | Validation | Result file | Figure/table | Paper section | Status |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n")
    write_if_missing(root / "reports/ai_usage_log.jsonl", "")
    write_if_missing(root / "reports/verification_report.md", "# Verification report\n\n## Submission state\n\ndraft\n\n## Checks\n\n| Check | Status | Evidence |\n| --- | --- | --- |\n")
    print(root / "contest_manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
