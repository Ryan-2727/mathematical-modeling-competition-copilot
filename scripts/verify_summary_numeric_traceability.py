#!/usr/bin/env python3
"""Require every abstract/conclusion number to be generated or explicitly exempted."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from generate_verified_values import load_registry


COMPLETE = {"pass", "complete", "verified"}
EXEMPTION_FIELDS = {
    "source_file",
    "line",
    "literal",
    "occurrence",
    "category",
    "reason",
    "status",
}
EXEMPTION_CATEGORIES = {
    "question_id",
    "calendar_date",
    "formula_index",
    "official_limit",
}
VERIFIED_MACRO = re.compile(
    r"\\VerifiedValue(?:WithUnit)?\s*\{\s*([A-Za-z][A-Za-z0-9_.:-]*)\s*\}"
)
IGNORED_COMMAND = re.compile(
    r"\\(?:cite|citep|citet|parencite|textcite|autocite|footcite|supercite|"
    r"ref|pageref|eqref|label)\*?(?:\s*\[[^\]]*\]){0,2}\s*\{[^{}]*\}"
)
NUMBER = re.compile(
    r"(?<![A-Za-z0-9_.])[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)"
    r"(?:\.\d+)?(?:[eE][-+]?\d+)?(?:\s*(?:%|％))?"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def strip_comment(line: str) -> str:
    for index, character in enumerate(line):
        if character != "%":
            continue
        slashes = 0
        cursor = index - 1
        while cursor >= 0 and line[cursor] == "\\":
            slashes += 1
            cursor -= 1
        if slashes % 2 == 0:
            return line[:index]
    return line


def normalize_literal(value: str) -> str:
    return re.sub(r"\s+", "", value)


def numeric_occurrences(path: Path, relative: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for line_number, raw in enumerate(
        path.read_text(encoding="utf-8-sig", errors="replace").splitlines(), 1
    ):
        text = strip_comment(raw)
        text = VERIFIED_MACRO.sub(" ", text)
        text = IGNORED_COMMAND.sub(" ", text)
        counts: Counter[str] = Counter()
        for match in NUMBER.finditer(text):
            literal = normalize_literal(match.group(0))
            counts[literal] += 1
            results.append(
                {
                    "source_file": relative,
                    "line": line_number,
                    "literal": literal,
                    "occurrence": counts[literal],
                }
            )
    return results


def read_exemptions(path: Path) -> tuple[list[dict[str, str]], set[str], str | None]:
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            return list(reader), set(reader.fieldnames or []), None
    except (OSError, UnicodeError, csv.Error) as exc:
        return [], set(), str(exc)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--abstract", default="paper/sections/abstract.tex")
    parser.add_argument("--conclusion", default="paper/sections/conclusion.tex")
    parser.add_argument(
        "--exemptions", default="reports/numeric_exemptions.csv"
    )
    parser.add_argument(
        "--registry", default="results/verified_values.csv"
    )
    parser.add_argument(
        "--out", default="reports/summary_numeric_traceability.json"
    )
    args = parser.parse_args()
    root = args.project_dir.resolve()
    source_relatives = (args.abstract, args.conclusion)
    errors: list[str] = []
    warnings: list[str] = []
    sources: dict[str, Path] = {}
    source_hashes: dict[str, str] = {}
    all_occurrences: list[dict[str, Any]] = []
    macro_usage: dict[str, list[str]] = {}
    registry_path = root / args.registry
    values, registry_errors, registry_sha256 = load_registry(root, registry_path)
    errors.extend(registry_errors)
    known = {item.key: item for item in values}
    for relative in source_relatives:
        path = root / relative
        sources[relative] = path
        if not path.is_file():
            errors.append(f"summary source is missing: {relative}")
            macro_usage[relative] = []
            continue
        source_hashes[relative] = sha256(path)
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        keys = VERIFIED_MACRO.findall(text)
        macro_usage[relative] = keys
        for key in keys:
            if key not in known:
                errors.append(f"{relative} uses unknown verified-value key: {key}")
        numeric_keys = [
            key
            for key in keys
            if key in known and known[key].value_type in {"integer", "number"}
        ]
        if not numeric_keys:
            errors.append(
                f"{relative} must state at least one result through a numeric "
                "\\VerifiedValue macro"
            )
        all_occurrences.extend(numeric_occurrences(path, relative))
    exemption_path = root / args.exemptions
    exemption_rows, exemption_fields, exemption_error = read_exemptions(exemption_path)
    if exemption_error:
        errors.append(f"cannot read numeric exemptions: {exemption_error}")
    if missing := EXEMPTION_FIELDS - exemption_fields:
        errors.append(
            "numeric_exemptions.csv missing columns: " + ", ".join(sorted(missing))
        )
    exemptions: dict[tuple[str, int, str, int], int] = {}
    for line_number, row in enumerate(exemption_rows, 2):
        try:
            source_line = int(str(row.get("line") or ""))
            occurrence = int(str(row.get("occurrence") or ""))
        except ValueError:
            errors.append(
                f"numeric_exemptions.csv:{line_number} line/occurrence must be integers"
            )
            continue
        key = (
            str(row.get("source_file") or "").strip().replace("\\", "/"),
            source_line,
            normalize_literal(str(row.get("literal") or "").strip()),
            occurrence,
        )
        if key in exemptions:
            errors.append(f"numeric_exemptions.csv:{line_number} duplicates an occurrence")
        exemptions[key] = line_number
        if key[0] not in source_relatives:
            errors.append(
                f"numeric_exemptions.csv:{line_number} source_file is not an audited summary source"
            )
        if source_line < 1 or occurrence < 1 or not key[2]:
            errors.append(f"numeric_exemptions.csv:{line_number} locator is invalid")
        if str(row.get("category") or "").strip() not in EXEMPTION_CATEGORIES:
            errors.append(f"numeric_exemptions.csv:{line_number} category is invalid")
        if not str(row.get("reason") or "").strip():
            errors.append(f"numeric_exemptions.csv:{line_number} reason is empty")
        if str(row.get("status") or "").strip().lower() not in COMPLETE:
            errors.append(f"numeric_exemptions.csv:{line_number} is not verified")
    occurrence_keys = {
        (
            item["source_file"],
            item["line"],
            item["literal"],
            item["occurrence"],
        )
        for item in all_occurrences
    }
    unregistered = sorted(occurrence_keys - set(exemptions))
    for source_file, line, literal, occurrence in unregistered:
        errors.append(
            f"untraceable raw number {literal!r} at {source_file}:{line} "
            f"occurrence {occurrence}; use a verified-value macro or a narrow exemption"
        )
    for key, line_number in exemptions.items():
        if key not in occurrence_keys:
            errors.append(
                f"numeric_exemptions.csv:{line_number} does not match a current raw number"
            )
    payload = {
        "status": "FAIL" if errors else ("LIMITED" if warnings else "PASS"),
        "scope": (
            "literal-level numeric provenance in abstract and conclusion; "
            "mathematical correctness and the semantic validity of an exemption "
            "remain human responsibilities"
        ),
        "source_sha256": source_hashes,
        "abstract_sha256": source_hashes.get(args.abstract, ""),
        "conclusion_sha256": source_hashes.get(args.conclusion, ""),
        "registry_sha256": registry_sha256,
        "exemptions_sha256": sha256(exemption_path)
        if exemption_path.is_file()
        else "",
        "macro_usage": macro_usage,
        "raw_numeric_occurrences": all_occurrences,
        "errors": errors,
        "warnings": warnings,
    }
    out = root / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(payload["status"])
    return {"PASS": 0, "FAIL": 1, "LIMITED": 2}[payload["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
