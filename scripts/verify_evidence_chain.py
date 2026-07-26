#!/usr/bin/env python3
"""Verify that decisive claims trace from data and code to LaTeX evidence."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from verify_latex_compatibility import reachable_tex_files


FIELDS = {
    "claim_id", "code_or_command", "source_data", "data_sha256", "result_file",
    "result_sha256", "verified_value_key", "latex_macro", "figure_label",
    "paper_location", "status",
}
COMPLETE = {"pass", "complete", "verified"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe(root: Path, raw: str) -> Path | None:
    item = Path(raw)
    if not raw or item.is_absolute() or ".." in item.parts:
        return None
    candidate = (root / item).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate


def read_csv(path: Path) -> tuple[list[dict[str, str]], set[str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), set(reader.fieldnames or [])


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify data-code-result-LaTeX evidence chains.")
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--out", default="reports/evidence_chain_verification.json")
    args = parser.parse_args()
    root = args.project_dir.resolve()
    out = safe(root, args.out)
    if out is None:
        raise SystemExit("output must stay inside --project-dir")
    errors: list[str] = []
    try:
        chains, fields = read_csv(root / "reports" / "evidence_chain.csv")
    except (OSError, UnicodeError, csv.Error) as exc:
        chains, fields = [], set()
        errors.append(f"cannot read reports/evidence_chain.csv: {exc}")
    if FIELDS - fields:
        errors.append("evidence_chain.csv missing columns: " + ", ".join(sorted(FIELDS - fields)))
    try:
        claims, _ = read_csv(root / "reports" / "claims.csv")
        claim_ids = {str(row.get("claim_id") or "").strip() for row in claims}
    except (OSError, UnicodeError, csv.Error) as exc:
        claim_ids = set()
        errors.append(f"cannot read reports/claims.csv: {exc}")
    try:
        values, _ = read_csv(root / "results" / "verified_values.csv")
        value_keys = {str(row.get("key") or "").strip() for row in values}
    except (OSError, UnicodeError, csv.Error) as exc:
        value_keys = set()
        errors.append(f"cannot read results/verified_values.csv: {exc}")
    try:
        figures, _ = read_csv(root / "reports" / "figure_manifest.csv")
        labels = {str(row.get("label") or "").strip() for row in figures}
    except (OSError, UnicodeError, csv.Error) as exc:
        labels = set()
        errors.append(f"cannot read reports/figure_manifest.csv: {exc}")
    paper = root / "paper"
    latex = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in reachable_tex_files(paper)) if paper.is_dir() else ""
    if not chains:
        errors.append("evidence_chain.csv has no decisive-claim rows")
    for line, row in enumerate(chains, 2):
        if any(not str(row.get(field) or "").strip() for field in FIELDS):
            errors.append(f"evidence_chain.csv:{line} has empty required fields")
        if row.get("status", "").strip().lower() not in COMPLETE:
            errors.append(f"evidence_chain.csv:{line} is not complete")
        if row.get("claim_id", "").strip() not in claim_ids:
            errors.append(f"evidence_chain.csv:{line} references an unknown claim_id")
        for path_field, hash_field in (("source_data", "data_sha256"), ("result_file", "result_sha256")):
            target = safe(root, str(row.get(path_field) or ""))
            if target is None or not target.is_file():
                errors.append(f"evidence_chain.csv:{line} {path_field} is missing or unsafe")
            elif digest(target).lower() != str(row.get(hash_field) or "").strip().lower():
                errors.append(f"evidence_chain.csv:{line} {hash_field} is stale")
        key = str(row.get("verified_value_key") or "").strip()
        macro = str(row.get("latex_macro") or "").strip()
        if key not in value_keys:
            errors.append(f"evidence_chain.csv:{line} verified value key is missing")
        if macro != f"\\VerifiedValue{{{key}}}" or macro not in latex:
            errors.append(f"evidence_chain.csv:{line} LaTeX macro is absent or inconsistent")
        if str(row.get("figure_label") or "").strip() not in labels:
            errors.append(f"evidence_chain.csv:{line} figure label is missing from manifest")
    payload = {
        "status": "PASS" if not errors else "FAIL",
        "scope": "declared data-code-result-LaTeX links only; not proof of mathematical correctness",
        "chain_rows": len(chains), "errors": errors,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(payload["status"])
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
