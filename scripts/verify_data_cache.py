#!/usr/bin/env python3
"""Verify a hashed aggregate cache and its leakage-safe time split."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def project_file(root: Path, raw: Any) -> Path | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    candidate = Path(raw)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return None
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a reusable aggregate-cache manifest.")
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", default="reports/data_cache_verification.json")
    args = parser.parse_args()
    root = args.project_dir.resolve()
    manifest_path = project_file(root, args.manifest)
    out = project_file(root, args.out)
    if manifest_path is None or out is None:
        raise SystemExit("manifest and output must be relative paths inside --project-dir")
    errors: list[str] = []
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        payload = {}
        errors.append(f"cannot read cache manifest: {exc}")
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        errors.append("schema_version must equal 1")
        payload = payload if isinstance(payload, dict) else {}
    verified: dict[str, dict[str, object]] = {}
    for name in ("source", "cache"):
        item = payload.get(name)
        if not isinstance(item, dict):
            errors.append(f"{name} must be an object")
            continue
        path = project_file(root, item.get("path"))
        expected = item.get("sha256")
        if path is None:
            errors.append(f"{name}.path must stay inside project")
        elif not path.is_file():
            errors.append(f"{name}.path is missing")
        elif not isinstance(expected, str) or len(expected) != 64:
            errors.append(f"{name}.sha256 must be a SHA-256 hex string")
        else:
            actual = sha256(path)
            verified[name] = {"path": path.relative_to(root).as_posix(), "sha256": actual}
            if actual.lower() != expected.lower():
                errors.append(f"{name}.sha256 does not match current file")
    cache = payload.get("cache") if isinstance(payload.get("cache"), dict) else {}
    if not isinstance(cache.get("aggregation_rule"), str) or not cache["aggregation_rule"].strip():
        errors.append("cache.aggregation_rule must be non-empty")
    split = payload.get("time_split") if isinstance(payload.get("time_split"), dict) else {}
    try:
        training_end = date.fromisoformat(str(split.get("training_end")))
        target_start = date.fromisoformat(str(split.get("target_start")))
        if training_end >= target_start:
            errors.append("time_split.training_end must precede target_start")
    except ValueError:
        errors.append("time_split dates must use ISO YYYY-MM-DD")
    status = "PASS" if not errors else "FAIL"
    report = {
        "schema_version": 1,
        "status": status,
        "scope": "hash binding and declared time split only; not a proof that aggregation is statistically appropriate",
        "verified": verified,
        "errors": errors,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(status)
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
