#!/usr/bin/env python3
"""Separate user delivery artifacts from official contest submissions."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


FIELDS = {"path", "role", "source_path", "sha256"}
ROLES = {"paper_pdf", "latex_source", "support_archive", "other"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_file(base: Path, relative: str) -> Path | None:
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    resolved = (base / candidate).resolve()
    try:
        resolved.relative_to(base.resolve())
    except ValueError:
        return None
    return resolved


def read_manifest(
    root: Path, folder_name: str
) -> tuple[list[dict[str, str]], list[str], set[str]]:
    folder = root / folder_name
    manifest = folder / "manifest.csv"
    errors: list[str] = []
    rows: list[dict[str, str]] = []
    fields: set[str] = set()
    if not manifest.is_file():
        return [], [f"{folder_name}/manifest.csv is missing"], fields
    try:
        with manifest.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = set(reader.fieldnames or [])
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        return [], [f"cannot read {folder_name}/manifest.csv: {exc}"], fields
    if missing := FIELDS - fields:
        errors.append(
            f"{folder_name}/manifest.csv missing columns: " + ", ".join(sorted(missing))
        )
    if not rows:
        errors.append(f"{folder_name}/manifest.csv has no artifact rows")
    seen: set[str] = set()
    for line, row in enumerate(rows, 2):
        relative = str(row.get("path") or "").strip().replace("\\", "/")
        role = str(row.get("role") or "").strip()
        source_relative = str(row.get("source_path") or "").strip().replace("\\", "/")
        if role not in ROLES:
            errors.append(f"{folder_name}/manifest.csv:{line} has invalid role: {role}")
        if relative in seen:
            errors.append(f"{folder_name}/manifest.csv:{line} duplicates path: {relative}")
        seen.add(relative)
        artifact = safe_file(folder, relative)
        source = safe_file(root, source_relative)
        if artifact is None or not artifact.is_file():
            errors.append(f"{folder_name}/manifest.csv:{line} artifact is missing or unsafe")
            continue
        expected = str(row.get("sha256") or "").strip().lower()
        actual = sha256_file(artifact)
        if expected != actual:
            errors.append(f"{folder_name}/manifest.csv:{line} SHA-256 mismatch")
        if source is None or not source.is_file():
            errors.append(f"{folder_name}/manifest.csv:{line} source_path is missing or unsafe")
        elif sha256_file(source) != actual:
            errors.append(f"{folder_name}/manifest.csv:{line} differs from source_path")
    return rows, errors, fields


def profile_family(profile: str) -> str:
    lowered = profile.lower()
    if lowered.startswith("cumcm"):
        return "cumcm"
    if lowered.startswith("mcm") or lowered.startswith("icm"):
        return "mcm-icm"
    return "generic"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.project_dir.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    try:
        contest: Any = json.loads(
            (root / "contest_manifest.json").read_text(encoding="utf-8-sig")
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        contest = {}
        errors.append(f"cannot read contest_manifest.json: {exc}")
    profile = str(contest.get("submission_profile") or "generic")
    family = profile_family(profile)
    delivery_rows, delivery_errors, _ = read_manifest(root, "delivery")
    official_rows, official_errors, _ = read_manifest(root, "official-submission")
    errors.extend(delivery_errors)
    errors.extend(official_errors)
    delivery_roles = {str(row.get("role") or "") for row in delivery_rows}
    required_delivery = {"paper_pdf", "latex_source", "support_archive"}
    if missing := required_delivery - delivery_roles:
        errors.append(
            "user delivery is missing roles: " + ", ".join(sorted(missing))
        )
    official_roles = [str(row.get("role") or "") for row in official_rows]
    official_paths = [str(row.get("path") or "") for row in official_rows]
    if family == "mcm-icm":
        if len(official_rows) != 1 or official_roles != ["paper_pdf"]:
            errors.append("MCM/ICM official submission must contain exactly one paper PDF")
        if any(Path(path).suffix.lower() != ".pdf" for path in official_paths):
            errors.append("MCM/ICM official submission file must be PDF")
    elif family == "cumcm":
        allowed_roles = {"paper_pdf", "support_archive"}
        disallowed_roles = sorted(set(official_roles) - allowed_roles)
        if disallowed_roles:
            errors.append(
                "CUMCM official submission has disallowed roles: "
                + ", ".join(disallowed_roles)
            )
        paper_rows = [
            row
            for row in official_rows
            if str(row.get("role") or "") == "paper_pdf"
        ]
        support_rows = [
            row
            for row in official_rows
            if str(row.get("role") or "") == "support_archive"
        ]
        if len(paper_rows) != 1:
            errors.append("CUMCM official submission needs exactly one paper file")
        for row in paper_rows:
            if Path(str(row.get("path") or "")).suffix.lower() not in {
                ".pdf",
                ".doc",
                ".docx",
            }:
                errors.append("CUMCM paper file must be PDF or Word")
        if len(support_rows) > 1 or len(official_rows) > 2:
            errors.append("CUMCM official submission allows at most one support archive")
        for row in support_rows:
            if Path(str(row.get("path") or "")).suffix.lower() not in {".zip", ".rar"}:
                errors.append("CUMCM support archive must be ZIP or RAR")
    else:
        if "paper_pdf" not in official_roles:
            errors.append("generic official submission needs a paper file")
        warnings.append("generic profile requires manual official-file review")
    payload = {
        "status": "FAIL" if errors else ("LIMITED" if warnings else "PASS"),
        "scope": (
            "artifact separation, hashes, and profile file-count rules; the "
            "specialist submission verifier remains authoritative for format details"
        ),
        "profile": profile,
        "profile_family": family,
        "counts": {
            "delivery_files": len(delivery_rows),
            "official_submission_files": len(official_rows),
        },
        "delivery_manifest_sha256": sha256_file(root / "delivery" / "manifest.csv")
        if (root / "delivery" / "manifest.csv").is_file()
        else "",
        "official_manifest_sha256": sha256_file(
            root / "official-submission" / "manifest.csv"
        )
        if (root / "official-submission" / "manifest.csv").is_file()
        else "",
        "errors": errors,
        "warnings": warnings,
    }
    out = args.out if args.out.is_absolute() else root / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(payload["status"])
    return {"PASS": 0, "FAIL": 1, "LIMITED": 2}[payload["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
