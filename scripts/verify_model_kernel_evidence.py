#!/usr/bin/env python3
"""Bind project use of a bundled kernel to inputs, outputs, and synthetic checks."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / "assets" / "model-library" / "cumcm-bc-model-cards.json"
FIELDS = {
    "model_id",
    "card_id",
    "kernel_id",
    "used",
    "backend",
    "input_file",
    "input_sha256",
    "output_file",
    "output_sha256",
    "synthetic_regression_report",
    "synthetic_regression_sha256",
    "adaptation_note",
    "status",
}
COMPLETE = {"verified", "pass", "complete"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_file(root: Path, relative: str) -> Path:
    root = root.resolve()
    target = (root / relative).resolve()
    try:
        common = os.path.commonpath((os.path.normcase(str(root)), os.path.normcase(str(target))))
    except ValueError as exc:
        raise ValueError(f"unsafe project path: {relative}") from exc
    if common != os.path.normcase(str(root)):
        raise ValueError(f"unsafe project path: {relative}")
    return target


def truthy(value: Any) -> bool:
    return str(value or "").strip().casefold() in {"yes", "true", "1"}


def load_json(path: Path, label: str, errors: list[str]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(value, dict):
            raise ValueError("must contain an object")
        return value
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        errors.append(f"cannot read {label}: {exc}")
        return {}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--usage", default="reports/model_kernel_usage.csv")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    root = args.project_dir.resolve()
    usage_path = safe_file(root, args.usage)
    errors: list[str] = []
    warnings: list[str] = []
    library = load_json(LIBRARY, "bundled model library", errors)
    card_map = {
        str(card.get("id")): card
        for card in library.get("cards", [])
        if isinstance(card, dict)
    }
    rows: list[dict[str, str]] = []
    fields: set[str] = set()
    try:
        with usage_path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = set(reader.fieldnames or [])
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        errors.append(f"cannot read model kernel usage: {exc}")
    if missing := FIELDS - fields:
        errors.append("model_kernel_usage.csv missing fields: " + ", ".join(sorted(missing)))
    used_rows = [row for row in rows if truthy(row.get("used"))]
    seen_models: set[str] = set()
    verified_records: list[dict[str, Any]] = []
    for row_number, row in enumerate(used_rows, 2):
        prefix = f"model_kernel_usage.csv:{row_number}"
        model_id = str(row.get("model_id") or "").strip()
        if not model_id or model_id in seen_models:
            errors.append(f"{prefix} has missing or duplicate model_id")
        seen_models.add(model_id)
        card_id = str(row.get("card_id") or "").strip()
        kernel_id = str(row.get("kernel_id") or "").strip()
        backend = str(row.get("backend") or "").strip()
        card = card_map.get(card_id)
        implementation = card.get("implementation") if isinstance(card, dict) else None
        if not isinstance(implementation, dict) or not implementation.get("bundled"):
            errors.append(f"{prefix} does not reference a bundled executable card")
        elif implementation.get("kernel_id") != kernel_id:
            errors.append(f"{prefix} kernel_id does not match the model card")
        if backend not in {"stdlib", "scientific"}:
            errors.append(f"{prefix} backend must be stdlib or scientific")
        if str(row.get("status") or "").strip().casefold() not in COMPLETE:
            errors.append(f"{prefix} is not verified")
        if len(str(row.get("adaptation_note") or "").strip()) < 20:
            errors.append(f"{prefix} needs a substantive adaptation note")
        bound: dict[str, Path] = {}
        for field, hash_field in (
            ("input_file", "input_sha256"),
            ("output_file", "output_sha256"),
            ("synthetic_regression_report", "synthetic_regression_sha256"),
        ):
            relative = str(row.get(field) or "").strip()
            try:
                path = safe_file(root, relative)
            except ValueError as exc:
                errors.append(f"{prefix} {exc}")
                continue
            bound[field] = path
            if not path.is_file():
                errors.append(f"{prefix} missing {field}: {relative}")
            elif str(row.get(hash_field) or "").strip().lower() != sha256(path):
                errors.append(f"{prefix} has stale {hash_field}")
        input_path = bound.get("input_file")
        output_path = bound.get("output_file")
        regression_path = bound.get("synthetic_regression_report")
        output = load_json(output_path, f"{prefix} kernel output", errors) if output_path and output_path.is_file() else {}
        regression = load_json(regression_path, f"{prefix} regression report", errors) if regression_path and regression_path.is_file() else {}
        if output:
            if output.get("status") != "PASS" or output.get("kernel") != kernel_id:
                errors.append(f"{prefix} kernel output did not pass or names another kernel")
            if output.get("backend_used") != backend:
                errors.append(f"{prefix} recorded backend differs from kernel output")
            if input_path and input_path.is_file() and output.get("input_sha256") != sha256(input_path):
                errors.append(f"{prefix} kernel output is stale relative to its input")
        if regression:
            if regression.get("status") != "PASS":
                errors.append(f"{prefix} synthetic regression did not pass")
            if backend not in set(regression.get("backends_used") or []):
                errors.append(f"{prefix} synthetic regression did not exercise {backend}")
            if kernel_id not in set((regression.get("fixture_hashes") or {}).keys()):
                errors.append(f"{prefix} synthetic regression lacks the selected kernel")
        verified_records.append(
            {
                "model_id": model_id,
                "card_id": card_id,
                "kernel_id": kernel_id,
                "backend": backend,
            }
        )
    if not used_rows:
        warnings.append("no bundled reference kernel is declared for this project")
    status = "FAIL" if errors else "PASS"
    payload = {
        "schema_version": 1,
        "status": status,
        "model_kernel_usage_sha256": sha256(usage_path) if usage_path.is_file() else "",
        "model_library_sha256": sha256(LIBRARY) if LIBRARY.is_file() else "",
        "used_kernel_count": len(used_rows),
        "verified_records": verified_records,
        "errors": errors,
        "warnings": warnings,
        "scope_limitation": "Bundled synthetic checks validate implementation behavior, not contest-specific assumptions, model fit, or truth.",
    }
    out = args.out if args.out.is_absolute() else root / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(status)
    for error in errors:
        print(f"ERROR {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
