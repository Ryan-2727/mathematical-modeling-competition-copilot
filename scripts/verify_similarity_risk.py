#!/usr/bin/env python3
"""Verify official CUMCM similarity-report evidence and threshold risk."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from contest_profile import load_contest_profile


METRICS = ("overall_text_copy_ratio", "excluding_own_published_ratio")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_path(root: Path, value: object, field: str, errors: list[str]) -> Path | None:
    text = str(value or "").strip()
    if not text:
        return None
    path = (root / text).resolve() if not Path(text).is_absolute() else Path(text).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        errors.append(f"{field} must stay inside the project directory")
        return None
    return path


def verify(root: Path, ledger_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    limitations: list[str] = []
    try:
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "FAIL", "errors": [f"cannot read similarity ledger: {exc}"], "limitations": []}
    try:
        profile = load_contest_profile(str(ledger.get("profile", "cumcm-2026")))
        national = float(profile.get("national_similarity_threshold", 0.25))
    except (TypeError, ValueError) as exc:
        return {"status": "FAIL", "errors": [f"invalid similarity threshold: {exc}"], "limitations": []}
    regional_raw = ledger.get("regional_threshold")
    try:
        regional = float(regional_raw) if regional_raw not in (None, "") else None
    except (TypeError, ValueError):
        errors.append("regional_threshold must be a ratio between 0 and 1")
        regional = None
    if regional is not None and not 0 <= regional <= 1:
        errors.append("regional_threshold must be a ratio between 0 and 1")
    threshold = min(national, regional) if regional is not None and 0 <= regional <= 1 else national

    paper = local_path(root, ledger.get("paper_path"), "paper_path", errors)
    actual_hash = None
    if paper is None or not paper.is_file():
        errors.append("paper_path is missing or not a file")
    else:
        actual_hash = sha256(paper)
        recorded_hash = str(ledger.get("paper_sha256", "")).strip().lower()
        if not recorded_hash:
            limitations.append("paper_sha256 is missing")
        elif recorded_hash != actual_hash:
            errors.append("paper_sha256 does not match the frozen paper")

    evidence_text = str(ledger.get("evidence", "")).strip()
    evidence = local_path(root, evidence_text, "evidence", errors)
    if not evidence_text:
        limitations.append("official Tongfang/CNKI report evidence is unavailable")
    elif evidence is None or not evidence.is_file():
        errors.append("official similarity report evidence does not exist")
    for field in ("provider", "report_time", "reviewer"):
        if not str(ledger.get(field, "")).strip():
            limitations.append(f"{field} is missing")

    values: dict[str, float | None] = {}
    metrics = ledger.get("metrics")
    if not isinstance(metrics, dict):
        metrics = {}
    for name in METRICS:
        raw = metrics.get(name)
        if raw in (None, ""):
            limitations.append(f"official metric {name} is missing")
            values[name] = None
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError):
            errors.append(f"official metric {name} must be a ratio between 0 and 1")
            values[name] = None
            continue
        if not 0 <= value <= 1:
            errors.append(f"official metric {name} must be a ratio between 0 and 1")
        elif value >= threshold:
            errors.append(f"official metric {name} reaches the applicable similarity threshold")
        values[name] = value

    status = "FAIL" if errors else "LIMITED" if limitations else "PASS"
    return {
        "status": status,
        "profile": profile["profile_id"],
        "national_threshold": national,
        "regional_threshold": regional,
        "applicable_threshold": threshold,
        "paper_sha256": actual_hash,
        "metrics": values,
        "errors": errors,
        "limitations": limitations,
        "note": (
            "Only evidence from the official report can establish these two metrics; "
            "the local long-phrase preflight is separate and advisory."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.project_dir.resolve()
    ledger = args.ledger.resolve()
    out = args.out.resolve()
    for name, path in (("--ledger", ledger), ("--out", out)):
        try:
            path.relative_to(root / "reports")
        except ValueError as exc:
            raise SystemExit(f"{name} must stay inside project reports") from exc
    report = verify(root, ledger)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(report["status"])
    return {"PASS": 0, "FAIL": 1, "LIMITED": 2}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
