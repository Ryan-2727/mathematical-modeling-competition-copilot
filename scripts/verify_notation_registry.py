#!/usr/bin/env python3
"""Verify mathematical notation, first definitions, mappings, and dimensions."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any


COMPLETE = {"pass", "verified", "complete", "accepted"}
KINDS = {"scalar", "vector", "matrix", "set", "random_variable", "index", "parameter"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def location_file(root: Path, locator: str) -> Path | None:
    relative = locator.split("#", 1)[0].strip()
    if not relative:
        return None
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return None
    return path


def verify(root: Path) -> dict[str, Any]:
    registry_path = root / "reports" / "notation_registry.csv"
    dimensions_path = root / "reports" / "equation_dimensions.csv"
    registry = rows(registry_path)
    dimensions = rows(dimensions_path)
    errors: list[str] = []
    warnings: list[str] = []
    symbols: dict[str, dict[str, str]] = {}
    code_names: dict[str, str] = {}
    figure_labels: dict[str, str] = {}
    for line, row in enumerate(registry, 2):
        symbol = str(row.get("symbol") or "").strip()
        canonical = str(row.get("canonical_tex") or "").strip()
        meaning = str(row.get("meaning") or "").strip()
        kind = str(row.get("kind") or "").strip()
        first = str(row.get("first_definition") or "").strip()
        status = str(row.get("status") or "").strip().lower()
        if not symbol or not canonical or not meaning:
            errors.append(f"notation row {line}: symbol, canonical_tex, and meaning are required")
            continue
        if symbol in symbols and symbols[symbol].get("meaning") != meaning:
            errors.append(f"notation row {line}: symbol {symbol!r} has conflicting meanings")
        symbols[symbol] = row
        if kind not in KINDS:
            errors.append(f"notation row {line}: invalid kind {kind!r}")
        if status not in COMPLETE:
            errors.append(f"notation row {line}: status is not verified")
        source = location_file(root, first)
        if source is None or not source.is_file():
            errors.append(f"notation row {line}: first definition file is missing")
        else:
            content = source.read_text(encoding="utf-8-sig", errors="replace")
            plain_symbol = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff]", "", symbol)
            if canonical not in content and (not plain_symbol or plain_symbol not in content):
                errors.append(
                    f"notation row {line}: first definition does not contain {canonical!r}"
                )
        if kind in {"vector", "matrix"} and not any(
            marker in canonical for marker in (r"\mathbf", r"\boldsymbol", r"\vec")
        ):
            errors.append(f"notation row {line}: {kind} lacks vector/matrix styling")
        if kind == "set" and not any(
            marker in canonical for marker in (r"\mathcal", r"\mathbb")
        ):
            warnings.append(f"notation row {line}: set styling needs human review")
        for code_name in filter(None, re.split(r"[;|]", str(row.get("code_names") or ""))):
            code_name = code_name.strip()
            owner = code_names.setdefault(code_name, symbol)
            if owner != symbol:
                errors.append(
                    f"notation row {line}: code name {code_name!r} maps to multiple symbols"
                )
        for label in filter(None, re.split(r"[;|]", str(row.get("figure_labels") or ""))):
            label = label.strip()
            owner = figure_labels.setdefault(label, symbol)
            if owner != symbol:
                errors.append(
                    f"notation row {line}: figure label {label!r} maps to multiple symbols"
                )
    if not registry:
        errors.append("reports/notation_registry.csv has no notation rows")
    equation_ids: set[str] = set()
    for line, row in enumerate(dimensions, 2):
        equation_id = str(row.get("equation_id") or "").strip()
        left = str(row.get("left_dimension") or "").strip()
        right = str(row.get("right_dimension") or "").strip()
        status = str(row.get("status") or "").strip().lower()
        if not equation_id or equation_id in equation_ids:
            errors.append(f"dimension row {line}: missing or duplicate equation_id")
        equation_ids.add(equation_id)
        if not left or left != right:
            errors.append(f"dimension row {line}: left and right dimensions differ")
        if status not in COMPLETE:
            errors.append(f"dimension row {line}: status is not verified")
        used = filter(
            None,
            re.split(r"[;|]", str(row.get("notation_symbols") or "")),
        )
        for symbol in (item.strip() for item in used):
            if symbol not in symbols:
                errors.append(
                    f"dimension row {line}: unregistered symbol {symbol!r}"
                )
    if not dimensions:
        warnings.append("no equation dimension records; dimensional QA is LIMITED")
    inputs = {
        path.relative_to(root).as_posix(): sha256(path)
        for path in (registry_path, dimensions_path)
        if path.is_file()
    }
    status = "FAIL" if errors else ("LIMITED" if warnings else "PASS")
    return {
        "status": status,
        "scope": (
            "declared notation and dimension consistency only; TeX scanning is "
            "conservative and ambiguous notation remains a human review item"
        ),
        "registered_symbols": len(symbols),
        "equations_checked": len(dimensions),
        "inputs": inputs,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--out", default="reports/notation_verification.json")
    args = parser.parse_args()
    root = args.project_dir.resolve()
    out = (root / args.out).resolve()
    try:
        out.relative_to(root / "reports")
    except ValueError as exc:
        raise SystemExit("output must stay inside project reports/") from exc
    try:
        payload = verify(root)
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        payload = {"status": "FAIL", "errors": [str(exc)], "warnings": []}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(payload["status"])
    return {"PASS": 0, "FAIL": 1, "LIMITED": 2}[payload["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
