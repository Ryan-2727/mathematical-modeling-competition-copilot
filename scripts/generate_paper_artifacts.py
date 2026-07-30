#!/usr/bin/env python3
"""Generate traceable LaTeX result fragments from verified project ledgers."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


COMPLETE = {"pass", "verified", "complete", "accepted", "included"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_path(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"path escapes project root: {relative}") from exc
    return path


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def tex(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(character, character) for character in value)


def table(headers: list[str], rows: list[list[str]], alignment: str) -> str:
    lines = [
        "% Generated file. Do not edit manually.",
        rf"\begin{{tabular}}{{{alignment}}}",
        r"\toprule",
        " & ".join(tex(item) for item in headers) + r" \\",
        r"\midrule",
    ]
    lines.extend(" & ".join(tex(item) for item in row) + r" \\" for row in rows)
    lines.extend([r"\bottomrule", r"\end{tabular}", ""])
    return "\n".join(lines)


def validate_values(root: Path, rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for line, row in enumerate(rows, 2):
        key = str(row.get("key") or "").strip()
        value = str(row.get("value") or "").strip()
        source_relative = str(row.get("source_file") or "").strip()
        locator = str(row.get("source_locator") or "").strip()
        if not key or key in seen:
            errors.append(f"verified values row {line}: missing or duplicate key")
        seen.add(key)
        if not value:
            errors.append(f"verified values row {line}: value is missing")
        if not source_relative or not locator:
            errors.append(f"verified values row {line}: source file/locator is missing")
            continue
        try:
            source = safe_path(root, source_relative)
        except ValueError as exc:
            errors.append(f"verified values row {line}: {exc}")
            continue
        if not source.is_file():
            errors.append(f"verified values row {line}: source file is missing")
            continue
        expected = str(row.get("source_sha256") or "").strip().lower()
        if expected and expected != sha256(source):
            errors.append(f"verified values row {line}: source digest is stale")
    if not rows:
        errors.append("results/verified_values.csv has no verified result rows")
    return errors


def generate(root: Path) -> dict[str, Any]:
    values_path = root / "results" / "verified_values.csv"
    conclusion_path = root / "reports" / "conclusion_map.csv"
    comparison_path = root / "reports" / "model_decision_log.csv"
    robustness_path = root / "reports" / "stress_tests.csv"
    figure_path = root / "reports" / "figure_manifest.csv"
    values = read_rows(values_path)
    conclusions = read_rows(conclusion_path)
    comparisons = read_rows(comparison_path)
    robustness = read_rows(robustness_path)
    figures = read_rows(figure_path)
    errors = validate_values(root, values)
    known_values = {str(row.get("key") or "").strip(): row for row in values}
    generated = root / "paper" / "generated"
    generated.mkdir(parents=True, exist_ok=True)
    core_rows = [
        [
            str(row.get("key") or ""),
            str(row.get("value") or ""),
            str(row.get("unit") or ""),
            str(row.get("source_locator") or ""),
        ]
        for row in values
    ]
    selected_rows = [
        [
            str(row.get("subproblem") or ""),
            str(row.get("baseline") or ""),
            str(row.get("candidate") or ""),
            str(row.get("selection_evidence") or ""),
        ]
        for row in comparisons
        if str(row.get("selected") or "").strip().lower() in {"true", "yes", "1"}
        and str(row.get("status") or "").strip().lower() in COMPLETE
    ]
    robustness_rows = [
        [
            str(row.get("subproblem") or ""),
            str(row.get("stress_type") or ""),
            str(row.get("change") or ""),
            str(row.get("outcome") or ""),
            str(row.get("verdict") or ""),
        ]
        for row in robustness
        if str(row.get("status") or "").strip().lower() in COMPLETE
    ]
    snippets: list[str] = [
        "% Generated file. Do not edit manually.",
        r"\begin{itemize}",
    ]
    for line, row in enumerate(conclusions, 2):
        if str(row.get("status") or "").strip().lower() not in COMPLETE:
            continue
        key = str(row.get("decisive_value_key") or "").strip()
        if key and key not in known_values:
            errors.append(f"conclusion map row {line}: unknown decisive value {key!r}")
            continue
        answer = str(row.get("answer_or_recommendation") or "").strip()
        limitation = str(row.get("limitation_location") or "").strip()
        if not answer or not limitation:
            errors.append(f"conclusion map row {line}: answer or limitation is missing")
            continue
        suffix = ""
        if key:
            item = known_values[key]
            suffix = (
                f" ({tex(key)}={tex(str(item.get('value') or ''))}"
                f" {tex(str(item.get('unit') or ''))})"
            )
        snippets.append(
            rf"\item \textbf{{{tex(str(row.get('subproblem') or ''))}:}} "
            rf"{tex(answer)}{suffix}. "
            rf"\emph{{Boundary: {tex(limitation)}.}}"
        )
    snippets.extend([r"\end{itemize}", ""])
    note_rows: list[list[str]] = []
    for row in figures:
        if str(row.get("status") or "").strip().lower() not in COMPLETE:
            continue
        label = str(row.get("label") or "").strip()
        caption = str(row.get("caption_insight") or "").strip()
        source = str(row.get("source_data") or "").strip()
        if label and caption and source:
            note_rows.append([label, caption, source])
    files = {
        "core_results.tex": table(
            ["Result key", "Value", "Unit", "Evidence"],
            core_rows,
            "llll",
        ),
        "model_comparison.tex": table(
            ["Subproblem", "Baseline", "Selected route", "Evidence"],
            selected_rows,
            "llll",
        ),
        "robustness.tex": table(
            ["Subproblem", "Stress test", "Change", "Outcome", "Verdict"],
            robustness_rows,
            "lllll",
        ),
        "conclusion_snippets.tex": "\n".join(snippets),
        "figure_notes.tex": table(
            ["Figure label", "Caption insight", "Source note"],
            note_rows,
            "lll",
        ),
    }
    output_hashes: dict[str, str] = {}
    for name, content in files.items():
        target = generated / name
        target.write_text(content, encoding="utf-8")
        output_hashes[target.relative_to(root).as_posix()] = sha256(target)
    inputs = {}
    for path in (
        values_path,
        conclusion_path,
        comparison_path,
        robustness_path,
        figure_path,
    ):
        if path.is_file():
            inputs[path.relative_to(root).as_posix()] = sha256(path)
    return {
        "status": "FAIL" if errors else "PASS",
        "scope": (
            "LaTeX fragments are generated only from traceable ledgers; this "
            "does not validate mathematical truth or prose quality"
        ),
        "inputs": inputs,
        "outputs": output_hashes,
        "errors": errors,
        "warnings": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument(
        "--out", default="reports/paper_artifacts_manifest.json", type=Path
    )
    args = parser.parse_args()
    root = args.project_dir.resolve()
    out = args.out if args.out.is_absolute() else root / args.out
    try:
        out.resolve().relative_to(root / "reports")
    except ValueError as exc:
        raise SystemExit("output must stay inside project reports/") from exc
    try:
        payload = generate(root)
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        payload = {"status": "FAIL", "errors": [str(exc)], "warnings": []}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(payload["status"])
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
