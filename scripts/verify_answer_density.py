#!/usr/bin/env python3
"""Verify that the abstract and conclusion foreground direct, bounded answers."""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

from contestlib import sha256_bytes as digest


FIELDS = {
    "subproblem", "question", "answer_or_recommendation", "decisive_value_key",
    "method_rationale_location", "validation_location", "limitation_location",
    "figure_or_table", "paper_location", "status",
}
COMPLETE = {"pass", "complete", "verified"}
METHOD = re.compile(r"模型|算法|方法|优化|回归|预测|仿真|model|method|algorithm|optimization|regression|forecast|simulation", re.I)
VALIDATION = re.compile(r"验证|检验|敏感|鲁棒|误差|残差|置信|对比|validat|sensitiv|robust|error|residual|confidence|backtest", re.I)
NUMBER = re.compile(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?\s*(?:%|[A-Za-z]+)?")


def plain_tex(text: str) -> str:
    text = re.sub(r"(?<!\\)%.*", " ", text)
    text = re.sub(r"\\(?:begin|end)\{[^{}]+\}", " ", text)
    text = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^\]]*\])?", " ", text)
    return re.sub(r"\s+", " ", text.replace("{", " ").replace("}", " ")).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify direct, evidence-linked abstract and conclusion answers.")
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--abstract", default="paper/sections/abstract.tex")
    parser.add_argument("--conclusion", default="paper/sections/conclusion.tex")
    parser.add_argument("--out", default="reports/answer_density.json")
    args = parser.parse_args()
    root = args.project_dir.resolve()
    abstract, conclusion = root / args.abstract, root / args.conclusion
    ledger = root / "reports/conclusion_map.csv"
    errors: list[str] = []
    texts: dict[str, str] = {}
    for name, path in (("abstract", abstract), ("conclusion", conclusion)):
        if not path.is_file():
            errors.append(f"{name} source is missing")
            texts[name] = ""
        else:
            texts[name] = plain_tex(path.read_text(encoding="utf-8", errors="replace"))
    combined = texts["abstract"] + " " + texts["conclusion"]
    checks = {"method": bool(METHOD.search(texts["abstract"])), "quantified_outcome": bool(NUMBER.search(texts["abstract"])), "validation": bool(VALIDATION.search(texts["abstract"]))}
    for name, passed in checks.items():
        if not passed:
            errors.append(f"abstract lacks {name.replace('_', ' ')} evidence")
    try:
        with ledger.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            rows, columns = list(reader), set(reader.fieldnames or [])
    except (OSError, UnicodeError, csv.Error) as exc:
        rows, columns = [], set()
        errors.append(f"cannot read conclusion_map.csv: {exc}")
    if FIELDS - columns:
        errors.append("conclusion_map.csv missing columns: " + ", ".join(sorted(FIELDS - columns)))
    for line, row in enumerate(rows, 2):
        if any(not str(row.get(field) or "").strip() for field in FIELDS):
            errors.append(f"conclusion_map.csv:{line} has incomplete answer evidence")
        if str(row.get("status") or "").strip().lower() not in COMPLETE:
            errors.append(f"conclusion_map.csv:{line} is not complete")
        answer = str(row.get("answer_or_recommendation") or "").strip()
        if answer and answer.lower() not in combined.lower():
            errors.append(f"conclusion text does not state the mapped answer for {row.get('subproblem')}")
    if not rows:
        errors.append("conclusion_map.csv has no subproblem answers")
    payload = {
        "status": "PASS" if not errors else "FAIL",
        "scope": "answer prominence and ledger linkage; not factual, mathematical, or stylistic certification",
        "abstract_sha256": digest(abstract) if abstract.is_file() else "",
        "conclusion_sha256": digest(conclusion) if conclusion.is_file() else "",
        "conclusion_map_sha256": digest(ledger) if ledger.is_file() else "",
        "checks": checks, "subproblems": len(rows), "errors": errors,
    }
    out = root / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(payload["status"])
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
