#!/usr/bin/env python3
"""Inventory and isolate user-owned historical benchmark inputs.

All manifests and reports produced by this script are private artifacts. Do not
place them, copied statements, attachments, scores, or run outputs in Git.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any


CASE_RE = re.compile(r"(?:cumcm\d{4}[-_ ]*)?([abc])(?:题)?$", re.IGNORECASE)
YEAR_RE = re.compile(r"20\d{2}$")
HIGH_RISK_PARTS = {
    "code",
    "docs",
    "figures",
    "output",
    "tmp",
    "build",
    "paper",
    "latex",
    "latex_vscode_overleaf",
    "skill_revision",
    "publish_repo",
    "__pycache__",
}
GENERATED_SUFFIXES = {".aux", ".log", ".out", ".pyc", ".synctex.gz", ".xdv"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_relative(value: str) -> Path | None:
    candidate = Path(value)
    if not value or candidate.is_absolute() or ".." in candidate.parts:
        return None
    return candidate


def inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def risk_tags(relative: Path) -> list[str]:
    lowered_parts = {part.casefold() for part in relative.parts}
    tags: list[str] = []
    if lowered_parts & HIGH_RISK_PARTS:
        tags.append("generated_or_solution_directory")
    if relative.suffix.casefold() in GENERATED_SUFFIXES:
        tags.append("generated_file_extension")
    if relative.name.casefold().startswith("result"):
        tags.append("result_named_input")
    return tags


def case_key(name: str) -> str | None:
    stem = Path(name).stem.strip()
    match = CASE_RE.fullmatch(stem)
    return match.group(1).lower() if match else None


def discover_cases(corpus_root: Path) -> list[dict[str, Any]]:
    discovered: list[dict[str, Any]] = []
    for year_dir in sorted(path for path in corpus_root.iterdir() if path.is_dir()):
        if not YEAR_RE.fullmatch(year_dir.name):
            continue
        for child in sorted(year_dir.iterdir()):
            key = case_key(child.name)
            if key is None:
                continue
            if child.is_dir():
                source_dir = child
                files = sorted(path for path in child.rglob("*") if path.is_file())
            elif child.is_file() and child.suffix.casefold() == ".pdf":
                source_dir = year_dir
                files = [child]
            else:
                continue
            candidates = []
            all_tags: set[str] = set()
            for path in files:
                relative = path.relative_to(source_dir)
                tags = risk_tags(relative)
                all_tags.update(tags)
                candidates.append(
                    {
                        "path": relative.as_posix(),
                        "sha256": sha256_file(path),
                        "bytes": path.stat().st_size,
                        "risk_tags": tags,
                    }
                )
            discovered.append(
                {
                    "id": f"historical-{year_dir.name}-{key}",
                    "year": int(year_dir.name),
                    "case": key.upper(),
                    "enabled": False,
                    "source_dir": source_dir.relative_to(corpus_root).as_posix(),
                    "allowed_inputs": [],
                    "acknowledged_risks": [],
                    "source_tree_risks": sorted(all_tags),
                    "candidates": candidates,
                    "status": "needs_allowlist",
                }
            )
    return discovered


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_manifest(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, [f"cannot read manifest: {exc}"]
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        return None, ["manifest must be a schema_version 1 JSON object"]
    if not isinstance(payload.get("cases"), list):
        return None, ["manifest cases must be an array"]
    return payload, []


def prepare(
    corpus_root: Path, private_root: Path, manifest: dict[str, Any]
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    copied_cases: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, raw_case in enumerate(manifest["cases"], 1):
        if not isinstance(raw_case, dict):
            errors.append(f"cases[{index}] must be an object")
            continue
        case_id = str(raw_case.get("id") or "").strip()
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", case_id):
            errors.append(f"cases[{index}] has invalid id")
            continue
        if case_id in seen_ids:
            errors.append(f"duplicate case id: {case_id}")
            continue
        seen_ids.add(case_id)
        if raw_case.get("enabled") is not True:
            copied_cases.append({"id": case_id, "status": "SKIPPED", "files": []})
            continue
        source_dir_value = raw_case.get("source_dir")
        if not isinstance(source_dir_value, str):
            errors.append(f"{case_id}: source_dir must be a relative string")
            continue
        source_relative = safe_relative(source_dir_value)
        source_dir = corpus_root / source_relative if source_relative else None
        if source_dir is None or not source_dir.is_dir() or not inside(source_dir, corpus_root):
            errors.append(f"{case_id}: source_dir is missing or outside corpus root")
            continue
        allowed = raw_case.get("allowed_inputs")
        if not isinstance(allowed, list) or not allowed:
            errors.append(f"{case_id}: enabled case needs a non-empty allowed_inputs array")
            continue
        acknowledgements = {
            str(item) for item in raw_case.get("acknowledged_risks", [])
            if isinstance(item, str)
        }
        source_risks = {
            tag
            for path in source_dir.rglob("*")
            if path.is_file()
            for tag in risk_tags(path.relative_to(source_dir))
            if tag != "result_named_input"
        }
        if source_risks and "contaminated_source_tree" not in acknowledgements:
            errors.append(
                f"{case_id}: source tree is contaminated; explicitly acknowledge "
                "contaminated_source_tree after reviewing the allow-list"
            )
            continue
        case_files: list[dict[str, Any]] = []
        case_errors: list[str] = []
        for raw_relative in allowed:
            if not isinstance(raw_relative, str):
                case_errors.append("allowed input paths must be strings")
                continue
            relative = safe_relative(raw_relative)
            source = source_dir / relative if relative else None
            if source is None or not source.is_file() or not inside(source, source_dir):
                case_errors.append(f"allowed input is missing or unsafe: {raw_relative}")
                continue
            tags = risk_tags(relative)
            if "generated_or_solution_directory" in tags or "generated_file_extension" in tags:
                case_errors.append(f"allowed input is a generated artifact: {raw_relative}")
                continue
            acknowledgement = f"result_named_input:{relative.as_posix()}"
            if "result_named_input" in tags and acknowledgement not in acknowledgements:
                case_errors.append(
                    f"result-named input requires explicit acknowledgement: {acknowledgement}"
                )
                continue
            destination = private_root / "inputs" / case_id / relative
            if destination.exists() and sha256_file(destination) != sha256_file(source):
                case_errors.append(f"refusing to overwrite different private input: {destination}")
                continue
            case_files.append(
                {
                    "source_relative": (source_relative / relative).as_posix(),
                    "private_relative": destination.relative_to(private_root).as_posix(),
                    "sha256": sha256_file(source),
                    "bytes": source.stat().st_size,
                    "risk_tags": tags,
                }
            )
        if case_errors:
            errors.extend(f"{case_id}: {item}" for item in case_errors)
            copied_cases.append({"id": case_id, "status": "FAIL", "files": case_files})
            continue
        for record in case_files:
            source = corpus_root / record["source_relative"]
            destination = private_root / record["private_relative"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                shutil.copy2(source, destination)
        copied_cases.append({"id": case_id, "status": "PASS", "files": case_files})
    return {
        "status": "PASS" if not errors else "FAIL",
        "scope": (
            "private allow-list copy and contamination audit only; does not solve, "
            "score, or publish historical contest material"
        ),
        "counts": {
            "cases": len(copied_cases),
            "prepared": sum(item["status"] == "PASS" for item in copied_cases),
            "skipped": sum(item["status"] == "SKIPPED" for item in copied_cases),
            "failed": sum(item["status"] == "FAIL" for item in copied_cases),
        },
        "cases": copied_cases,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    inventory = subparsers.add_parser("inventory")
    inventory.add_argument("--corpus-root", type=Path, required=True)
    inventory.add_argument("--out", type=Path, required=True)
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--corpus-root", type=Path, required=True)
    prepare_parser.add_argument("--private-root", type=Path, required=True)
    prepare_parser.add_argument("--manifest", type=Path, required=True)
    prepare_parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    corpus_root = args.corpus_root.resolve()
    if not corpus_root.is_dir():
        raise SystemExit("corpus root is missing")
    if args.command == "inventory":
        out = args.out.resolve()
        if inside(out, corpus_root):
            raise SystemExit("inventory output must stay outside the source corpus")
        payload = {
            "schema_version": 1,
            "scope": "private historical corpus inventory; do not commit this file",
            "cases": discover_cases(corpus_root),
        }
        write_json(out, payload)
        print(f"cases={len(payload['cases'])}")
        return 0
    private_root = args.private_root.resolve()
    manifest_path = args.manifest.resolve()
    out = args.out.resolve()
    if inside(private_root, corpus_root) or inside(corpus_root, private_root):
        raise SystemExit("private root and source corpus must not overlap")
    if not inside(manifest_path, private_root) or not inside(out, private_root):
        raise SystemExit("manifest and output must stay inside private root")
    if manifest_path == out:
        raise SystemExit("output must not overwrite the private manifest")
    manifest, errors = load_manifest(manifest_path)
    if errors or manifest is None:
        payload = {"status": "FAIL", "errors": errors, "cases": []}
    else:
        payload = prepare(corpus_root, private_root, manifest)
    write_json(out, payload)
    print(payload["status"])
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
