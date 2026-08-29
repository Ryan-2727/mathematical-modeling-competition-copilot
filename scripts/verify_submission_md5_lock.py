#!/usr/bin/env python3
"""Verify actual MD5 locks for frozen CUMCM submission artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from contest_profile import load_contest_profile


def digest(path: Path, algorithm: str) -> str:
    hasher = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


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


def parse_time(value: object, field: str, errors: list[str]) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        errors.append(f"{field} must be an ISO-8601 timestamp")
        return None
    if parsed.tzinfo is None:
        errors.append(f"{field} must include a timezone")
        return None
    return parsed


def verify(root: Path, ledger_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    limitations: list[str] = []
    try:
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "FAIL", "errors": [f"cannot read MD5 ledger: {exc}"], "limitations": [], "artifacts": []}

    try:
        profile = load_contest_profile(str(ledger.get("profile", "cumcm-2026")))
        deadline = datetime.fromisoformat(profile["hash_deadline"])
    except (KeyError, TypeError, ValueError) as exc:
        return {"status": "FAIL", "errors": [f"invalid contest profile or MD5 deadline: {exc}"], "limitations": [], "artifacts": []}

    artifacts = ledger.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        errors.append("artifacts must be a non-empty list")
        artifacts = []
    results: list[dict[str, Any]] = []
    roles: set[str] = set()
    for index, item in enumerate(artifacts):
        label = f"artifacts[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue
        role = str(item.get("role", "")).strip()
        if role not in {"paper", "support"} or role in roles:
            errors.append(f"{label}.role must be unique paper or support")
        roles.add(role)
        path = local_path(root, item.get("path"), f"{label}.path", errors)
        if path is None or not path.is_file():
            errors.append(f"{label}.path is missing or not a file")
            continue
        actual_md5 = digest(path, "md5")
        actual_sha256 = digest(path, "sha256")
        recorded_md5 = str(item.get("recorded_md5", "")).strip().lower()
        generated_at = parse_time(item.get("md5_generated_at"), f"{label}.md5_generated_at", errors)
        submitted_at = parse_time(item.get("md5_submitted_at"), f"{label}.md5_submitted_at", errors)
        evidence_text = str(item.get("evidence", "")).strip()
        evidence = local_path(root, evidence_text, f"{label}.evidence", errors)

        missing = []
        if not recorded_md5:
            missing.append("recorded_md5")
        if generated_at is None and not item.get("md5_generated_at"):
            missing.append("md5_generated_at")
        if submitted_at is None and not item.get("md5_submitted_at"):
            missing.append("md5_submitted_at")
        if not evidence_text:
            missing.append("official-client evidence")
        if missing:
            limitations.append(f"{label} lacks " + ", ".join(missing))
        if recorded_md5 and recorded_md5 != actual_md5:
            errors.append(f"{label} MD5 mismatch: the frozen file changed or the recorded MD5 is stale")
        if recorded_md5 and (len(recorded_md5) != 32 or any(c not in "0123456789abcdef" for c in recorded_md5)):
            errors.append(f"{label}.recorded_md5 is not a valid MD5 hex digest")
        if evidence_text and (evidence is None or not evidence.is_file()):
            errors.append(f"{label}.evidence does not exist")
        for name, timestamp in (("generated", generated_at), ("submitted", submitted_at)):
            if timestamp is not None and timestamp > deadline:
                errors.append(f"{label} MD5 was {name} after the official deadline")
        if generated_at is not None and submitted_at is not None and submitted_at < generated_at:
            errors.append(f"{label}.md5_submitted_at precedes generation")
        results.append({
            "role": role,
            "path": path.relative_to(root).as_posix(),
            "size_bytes": path.stat().st_size,
            "actual_md5": actual_md5,
            "actual_sha256": actual_sha256,
            "recorded_md5": recorded_md5 or None,
        })

    status = "FAIL" if errors else "LIMITED" if limitations else "PASS"
    return {
        "status": status,
        "profile": profile["profile_id"],
        "hash_deadline": profile["hash_deadline"],
        "errors": errors,
        "limitations": limitations,
        "artifacts": results,
        "note": "This local verifier does not operate or replace the official CUMCM client.",
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
