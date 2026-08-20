#!/usr/bin/env python3
"""Render complete AI-use evidence, an editable declaration, and an optional PDF."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


REQUIRED_RECORD_FIELDS = {
    "timestamp_utc",
    "tool",
    "version",
    "purpose",
    "stage",
    "prompt_summary",
    "adopted",
    "human_verification",
    "reviewer_role",
    "reviewed_artifact",
    "verification_method",
    "modifications",
}
PLACEHOLDERS = {"pending", "todo", "tbd", "unknown", "not_recorded", "placeholder"}
STARTER_PURPOSE = "请替换为真实、简要用途"


def latex(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "_": r"\_",
        "#": r"\#",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
        "$": r"\$",
    }
    return "".join(replacements.get(character, character) for character in value)


def load_records(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    records: list[dict[str, Any]] = []
    if not path.is_file():
        return [], [f"AI-use log is missing: {path}"]
    for line_number, raw in enumerate(
        path.read_text(encoding="utf-8-sig").splitlines(), 1
    ):
        if not raw.strip():
            continue
        try:
            item = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"AI-use log line {line_number} is invalid JSON: {exc}")
            continue
        if not isinstance(item, dict):
            errors.append(f"AI-use log line {line_number} must be an object")
            continue
        missing = REQUIRED_RECORD_FIELDS - set(item)
        if missing:
            errors.append(
                f"AI-use log line {line_number} missing fields: "
                + ", ".join(sorted(missing))
            )
        for field in REQUIRED_RECORD_FIELDS:
            value = str(item.get(field) or "").strip()
            if not value or value.casefold() in PLACEHOLDERS:
                errors.append(
                    f"AI-use log line {line_number} field {field} lacks actual evidence"
                )
        records.append(item)
    if not records:
        errors.append("AI-use log has no records")
    return records, errors


def declaration_source(purpose: str) -> str:
    return (
        "% !TeX root = ../main.tex\n"
        "% The purpose macro below is intentionally human-editable.\n"
        "% Automatic generation must not overwrite a non-placeholder human edit.\n"
        "\\section*{AI工具使用声明}\n\n"
        "% BEGIN HUMAN-EDITABLE AI PURPOSE\n"
        rf"\providecommand{{\AIUsePurpose}}{{{latex(purpose)}}}" + "\n"
        "% END HUMAN-EDITABLE AI PURPOSE\n\n"
        "本参赛队在竞赛过程中使用了AI工具，主要用于"
        "\\AIUsePurpose，详细使用情况见支撑材料。\n"
    )


def write_declaration(path: Path, purpose: str, *, force: bool) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or force:
        path.write_text(declaration_source(purpose), encoding="utf-8")
        return "written"
    existing = path.read_text(encoding="utf-8-sig")
    if STARTER_PURPOSE in existing:
        path.write_text(
            existing.replace(STARTER_PURPOSE, latex(purpose), 1), encoding="utf-8"
        )
        return "starter-updated"
    return "human-edit-preserved"


def unique_purposes(records: list[dict[str, Any]]) -> str:
    values: list[str] = []
    for item in records:
        value = str(item["purpose"]).strip()
        if value not in values:
            values.append(value)
    return "、".join(values)


def render_markdown(records: list[dict[str, Any]]) -> str:
    lines = [
        "# AI tool use details",
        "",
        "| Time (UTC) | Tool/version | Stage | Purpose | Adoption | Reviewer role | Reviewed artifact | Verification | Modifications |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in records:
        lines.append(
            f"| {item['timestamp_utc']} | {item['tool']} {item['version']} | "
            f"{item['stage']} | {item['purpose']} | {item['adopted']} | "
            f"{item['reviewer_role']} | {item['reviewed_artifact']} | "
            f"{item['verification_method']}: {item['human_verification']} | "
            f"{item['modifications']} |"
        )
    lines += ["", "## Key interaction summaries", ""]
    for index, item in enumerate(records, 1):
        lines += [
            f"### {index}. {item['tool']} - {item['stage']}",
            str(item["prompt_summary"]),
            "",
        ]
    return "\n".join(lines)


def render_pdf(records: list[dict[str, Any]], path: Path) -> None:
    engine = shutil.which("xelatex") or shutil.which("pdflatex")
    if not engine:
        raise SystemExit("PDF requested but xelatex/pdflatex is unavailable")
    is_xelatex = Path(engine).stem.lower().startswith("xelatex")
    document_class = (
        r"\documentclass[11pt]{ctexart}"
        if is_xelatex
        else r"\documentclass[11pt]{article}"
    )
    title = "AI工具使用详情" if is_xelatex else "AI Tool Use Details"
    body = [
        document_class,
        r"\usepackage[margin=2.5cm]{geometry}",
        r"\usepackage{longtable}",
        r"\begin{document}",
        r"\section*{" + title + r"}",
        r"\begin{longtable}{p{0.2\textwidth}p{0.72\textwidth}}",
    ]
    for index, item in enumerate(records, 1):
        summary = (
            f"Purpose: {item['purpose']}; Stage: {item['stage']}; "
            f"Adoption: {item['adopted']}; Reviewer role: {item['reviewer_role']}; "
            f"Reviewed artifact: {item['reviewed_artifact']}; Verification method: "
            f"{item['verification_method']}; Human verification: "
            f"{item['human_verification']}; Modifications: {item['modifications']}; "
            f"Key interaction: {item['prompt_summary']}"
        )
        body += [
            latex(f"{index}. {item['tool']} {item['version']}")
            + " & "
            + latex(summary)
            + r"\\"
        ]
    body += [r"\end{longtable}", r"\end{document}"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as raw:
        work = Path(raw)
        tex = work / "ai_use.tex"
        tex.write_text("\n".join(body), encoding="utf-8")
        result = subprocess.run(
            [engine, "-interaction=nonstopmode", tex.name],
            cwd=work,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        pdf = work / "ai_use.pdf"
        if result.returncode != 0 or not pdf.is_file():
            raise SystemExit("AI report PDF compilation failed: " + result.stdout[-1000:])
        shutil.copy2(pdf, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True, help="Markdown output")
    parser.add_argument("--pdf-out", type=Path)
    parser.add_argument("--declaration-out", type=Path)
    parser.add_argument("--declaration-purpose")
    parser.add_argument("--force-declaration", action="store_true")
    args = parser.parse_args()
    records, errors = load_records(args.log)
    if errors:
        for error in errors:
            print(f"ERROR {error}")
        return 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render_markdown(records), encoding="utf-8")
    if args.declaration_out:
        purpose = (args.declaration_purpose or unique_purposes(records)).strip()
        if not purpose or purpose.casefold() in PLACEHOLDERS:
            raise SystemExit("AI declaration purpose must record actual use")
        status = write_declaration(
            args.declaration_out, purpose, force=args.force_declaration
        )
        print(f"declaration: {status}")
    if args.pdf_out:
        render_pdf(records, args.pdf_out)
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
