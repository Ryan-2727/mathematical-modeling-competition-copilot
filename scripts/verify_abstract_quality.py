#!/usr/bin/env python3
"""Check whether a contest abstract contains answer-oriented evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


PLACEHOLDERS = re.compile(r"\b(?:TODO|TBD|FIXME|XXX)\b|待补|占位", re.IGNORECASE)
METHOD = re.compile(
    r"模型|算法|方法|优化|回归|预测|仿真|聚类|微分方程|"
    r"\b(?:model|method|algorithm|optimization|regression|forecast|simulation)\b",
    re.IGNORECASE,
)
VALIDATION = re.compile(
    r"验证|检验|敏感性|鲁棒|误差|残差|置信区间|对比|"
    r"\b(?:validat|sensitiv|robust|error|residual|confidence|backtest)\w*",
    re.IGNORECASE,
)
CONCLUSION = re.compile(
    r"结果表明|最终|建议|结论|因此|说明|"
    r"\b(?:result|conclud|recommend|therefore|suggest|indicat)\w*",
    re.IGNORECASE,
)
NUMBER = re.compile(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?\s*(?:%|％|[A-Za-z]+)?")
VERIFIED_NUMBER = re.compile(r"\\VerifiedValue(?:WithUnit)?\s*\{[^{}]+\}")
TASK = re.compile(
    r"问题\s*[一二三四五六七八九十\d]+|"
    r"第[一二三四五六七八九十\d]+(?:个)?问题|"
    r"\b(?:problem|task|question)\s*(?:[A-F]|\d+)\b|"
    r"\bQ\s*\d+\b",
    re.IGNORECASE,
)


def plain_tex(text: str) -> str:
    text = re.sub(r"(?<!\\)%.*", " ", text)
    text = re.sub(r"\\(?:begin|end)\{[^{}]+\}", " ", text)
    text = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^\]]*\])?", " ", text)
    text = text.replace("{", " ").replace("}", " ").replace("~", " ")
    return re.sub(r"\s+", " ", text).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument(
        "--abstract", type=Path, default=Path("paper/sections/abstract.tex")
    )
    parser.add_argument("--expected-subproblems", type=int, required=True)
    parser.add_argument("--minimum-content-units", type=int, default=250)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.project_dir.resolve()
    path = args.abstract if args.abstract.is_absolute() else root / args.abstract
    errors: list[str] = []
    warnings: list[str] = []
    if not path.is_file():
        raw_text = ""
        text = ""
        errors.append(f"abstract source is missing: {path}")
    else:
        raw_text = path.read_text(encoding="utf-8", errors="replace")
        text = plain_tex(raw_text)
    content_units = len(re.findall(r"[\u4e00-\u9fff]|[A-Za-z0-9]+", text))
    if content_units < args.minimum_content_units:
        errors.append(
            f"abstract has {content_units} content units; minimum is "
            f"{args.minimum_content_units}"
        )
    if PLACEHOLDERS.search(text):
        errors.append("abstract contains a placeholder")
    checks = {
        "method": bool(METHOD.search(text)),
        "quantified_result": bool(
            NUMBER.search(TASK.sub(" ", text)) or VERIFIED_NUMBER.search(raw_text)
        ),
        "validation": bool(VALIDATION.search(text)),
        "conclusion_or_recommendation": bool(CONCLUSION.search(text)),
    }
    for name, passed in checks.items():
        if not passed:
            errors.append(f"abstract lacks {name.replace('_', ' ')} evidence")
    task_markers = {match.group(0).lower().replace(" ", "") for match in TASK.finditer(text)}
    if len(task_markers) < args.expected_subproblems:
        errors.append(
            f"abstract identifies {len(task_markers)} subproblems; expected "
            f"{args.expected_subproblems}"
        )
    if len(text) > 3000:
        warnings.append("abstract is unusually long; verify the official one-page limit")
    payload = {
        "status": "PASS" if not errors else "FAIL",
        "scope": (
            "answer-oriented abstract structure only; does not certify factual "
            "correctness, mathematical quality, or official page fit"
        ),
        "source": path.as_posix(),
        "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest()
        if path.is_file()
        else "",
        "content_units": content_units,
        "task_markers": sorted(task_markers),
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
    }
    out = args.out if args.out.is_absolute() else root / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(payload["status"])
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
