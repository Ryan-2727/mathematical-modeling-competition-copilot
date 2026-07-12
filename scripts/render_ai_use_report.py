#!/usr/bin/env python3
"""Render an AI-use Markdown report and optional CUMCM-ready PDF."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


def latex(value: str) -> str:
    return value.replace("\\", r"\textbackslash{}").replace("&", r"\&").replace("%", r"\%").replace("_", r"\_").replace("#", r"\#").replace("{", r"\{").replace("}", r"\}").replace("~", r"\textasciitilde{}").replace("^", r"\textasciicircum{}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True, help="Markdown output")
    parser.add_argument("--pdf-out", type=Path)
    args = parser.parse_args()
    records = [json.loads(line) for line in args.log.read_text(encoding="utf-8").splitlines() if line.strip()] if args.log.exists() else []
    lines = ["# AI tool use details", "", "| Time (UTC) | Tool/version | Stage | Purpose | Adoption | Human verification |", "| --- | --- | --- | --- | --- | --- |"]
    for item in records: lines.append(f"| {item['timestamp_utc']} | {item['tool']} {item['version']} | {item['stage']} | {item['purpose']} | {item['adopted']} | {item['human_verification']} |")
    lines += ["", "## Key interaction summaries", ""]
    for index, item in enumerate(records, 1): lines += [f"### {index}. {item['tool']} - {item['stage']}", item['prompt_summary'], ""]
    args.out.parent.mkdir(parents=True, exist_ok=True); args.out.write_text("\n".join(lines), encoding="utf-8")
    if args.pdf_out:
        engine = shutil.which("xelatex") or shutil.which("pdflatex")
        if not engine: raise SystemExit("PDF requested but xelatex/pdflatex is unavailable")
        document_class = r"\documentclass[11pt]{ctexart}" if Path(engine).name.startswith("xelatex") else r"\documentclass[11pt]{article}"
        title = "AI工具使用详情" if Path(engine).name.startswith("xelatex") else "AI Tool Use Details"
        body = [document_class, r"\usepackage[margin=2.5cm]{geometry}", r"\usepackage{longtable}", r"\begin{document}", r"\section*{" + title + r"}", r"\begin{longtable}{p{0.2\textwidth}p{0.72\textwidth}}"]
        for index, item in enumerate(records, 1): body += [latex(f"{index}. {item['tool']} {item['version']} ({item['stage']})") + " & " + latex(f"Purpose: {item['purpose']}; Adoption: {item['adopted']}; Human verification: {item['human_verification']}. Key interaction: {item['prompt_summary']}") + r"\\"]
        body += [r"\end{longtable}", r"\end{document}"]
        args.pdf_out.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as raw:
            work = Path(raw); tex = work / "ai_use.tex"; tex.write_text("\n".join(body), encoding="utf-8")
            result = subprocess.run([engine, "-interaction=nonstopmode", tex.name], cwd=work, capture_output=True, text=True)
            if result.returncode != 0 or not (work / "ai_use.pdf").is_file(): raise SystemExit("AI report PDF compilation failed: " + result.stdout[-1000:])
            shutil.copy2(work / "ai_use.pdf", args.pdf_out)
    return 0


if __name__ == "__main__": raise SystemExit(main())
