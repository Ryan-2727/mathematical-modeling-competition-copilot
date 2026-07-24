#!/usr/bin/env python3
"""Verify and compile a portable LaTeX project for Overleaf and VS Code."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


REQUIRED_FILES = {
    "main.tex",
    "references.bib",
    ".latexmkrc",
    ".vscode/settings.json",
    ".vscode/extensions.json",
}
REQUIRED_DIRS = {"sections", "figures"}
SOURCE_SUFFIXES = {
    ".tex", ".bib", ".cls", ".sty", ".bst", ".json",
    ".pdf", ".png", ".jpg", ".jpeg", ".eps",
}
GRAPHIC_SUFFIXES = (".pdf", ".png", ".jpg", ".jpeg", ".eps")
OS_FONT_RE = re.compile(
    r"(?i)(times new roman|arial|calibri|cambria|simsun|simhei|"
    r"microsoft yahei|fangsong|kaiti|宋体|黑体|微软雅黑|仿宋|楷体)"
)
INPUT_RE = re.compile(r"\\(?:input|include)\s*\{([^{}]+)\}")
GRAPHIC_RE = re.compile(r"\\includegraphics(?:\s*\[[^\]]*\])?\s*\{([^{}]+)\}")
LOG_ERROR_PATTERNS = (
    re.compile(r"^!", re.MULTILINE),
    re.compile(r"LaTeX Error:", re.IGNORECASE),
    re.compile(r"Emergency stop", re.IGNORECASE),
    re.compile(r"Fatal error", re.IGNORECASE),
    re.compile(r"undefined citations?", re.IGNORECASE),
    re.compile(r"undefined references?", re.IGNORECASE),
    re.compile(r"Citation .+ undefined", re.IGNORECASE),
    re.compile(r"Reference .+ undefined", re.IGNORECASE),
    re.compile(r"File .+ not found", re.IGNORECASE),
)


def strip_comments(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        match = re.search(r"(?<!\\)%", line)
        lines.append(line[: match.start()] if match else line)
    return "\n".join(lines)


def source_files(paper_dir: Path) -> list[Path]:
    result: list[Path] = []
    for path in paper_dir.rglob("*"):
        if not path.is_file() or "build" in path.relative_to(paper_dir).parts:
            continue
        if path.name == ".latexmkrc" or path.suffix.lower() in SOURCE_SUFFIXES:
            if path.name != "main.pdf":
                result.append(path)
    return sorted(result, key=lambda path: path.relative_to(paper_dir).as_posix())


def source_fingerprint(paper_dir: Path) -> str:
    digest = hashlib.sha256()
    for path in source_files(paper_dir):
        relative = path.relative_to(paper_dir).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        content = path.read_bytes()
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def resolve_input(paper_dir: Path, owner: Path, argument: str, suffix: str) -> Path | None:
    if any(marker in argument for marker in ("\\", "#", "$")):
        return None
    candidate = Path(argument)
    if candidate.suffix == "":
        candidate = candidate.with_suffix(suffix)
    for base in (owner.parent, paper_dir):
        resolved = (base / candidate).resolve()
        try:
            resolved.relative_to(paper_dir.resolve())
        except ValueError:
            continue
        if resolved.is_file():
            return resolved
    return None


def reachable_tex_files(paper_dir: Path) -> list[Path]:
    """Return the TeX files that are statically reachable from main.tex."""
    main_path = (paper_dir / "main.tex").resolve()
    if not main_path.is_file():
        return []
    pending = [main_path]
    visited: set[Path] = set()
    while pending:
        owner = pending.pop()
        if owner in visited:
            continue
        visited.add(owner)
        text = strip_comments(owner.read_text(encoding="utf-8", errors="replace"))
        for argument in INPUT_RE.findall(text):
            resolved = resolve_input(paper_dir, owner, argument, ".tex")
            if resolved is not None and resolved.resolve() not in visited:
                pending.append(resolved.resolve())
    return sorted(visited, key=lambda path: path.relative_to(paper_dir.resolve()).as_posix())


def static_checks(paper_dir: Path) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []
    details: dict[str, Any] = {}
    for relative in sorted(REQUIRED_FILES):
        if not (paper_dir / relative).is_file():
            errors.append(f"missing required file: {relative}")
    for relative in sorted(REQUIRED_DIRS):
        if not (paper_dir / relative).is_dir():
            errors.append(f"missing required directory: {relative}/")

    text_files: dict[Path, str] = {}
    for path in source_files(paper_dir):
        if path.suffix.lower() not in {".tex", ".bib", ".cls", ".sty", ".bst", ".json"} and path.name != ".latexmkrc":
            continue
        try:
            text_files[path] = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"not valid UTF-8: {path.relative_to(paper_dir).as_posix()}")
    all_text = "\n".join(text_files.values())
    if re.search(r"(?i)(?:[a-z]:[\\/]|file://|\\\\[^\\\s]+\\|/(?:home|users)/)", all_text):
        errors.append("source contains an absolute or user-specific filesystem path")
    if OS_FONT_RE.search(all_text):
        errors.append("source contains an operating-system-specific font name")

    main_path = paper_dir / "main.tex"
    main_text = text_files.get(main_path, "")
    for directive in (
        "% !TeX program = xelatex",
        "% !TeX encoding = UTF-8",
        "% !TeX root = main.tex",
        "% !BIB program = bibtex",
    ):
        if directive not in main_text:
            errors.append(f"main.tex missing editor directive: {directive}")
    if "\\documentclass" not in main_text:
        errors.append("main.tex has no document class")
    if not (
        re.search(r"\\bibliography\s*\{[^{}]*references[^{}]*\}", strip_comments(main_text))
        or re.search(r"\\addbibresource\s*\{references\.bib\}", strip_comments(main_text))
    ):
        errors.append("main.tex does not use references.bib")

    latexmk_text = text_files.get(paper_dir / ".latexmkrc", "")
    for marker in ("$pdf_mode = 5", "xelatex", "-synctex=1", "-halt-on-error", "-file-line-error"):
        if marker not in latexmk_text:
            errors.append(f".latexmkrc missing portable build marker: {marker}")
    if re.search(r"(?m)^\s*\$(?:out_dir|aux_dir)\s*=", latexmk_text):
        errors.append(".latexmkrc must not force an output directory; VS Code owns build/")

    settings_path = paper_dir / ".vscode" / "settings.json"
    settings: dict[str, Any] = {}
    if settings_path in text_files:
        try:
            settings = json.loads(text_files[settings_path])
        except json.JSONDecodeError as exc:
            errors.append(f".vscode/settings.json is invalid JSON: {exc}")
    if settings:
        if settings.get("latex-workshop.latex.outDir") != "%DIR%/build":
            errors.append("VS Code must write LaTeX output to %DIR%/build")
        if settings.get("latex-workshop.view.pdf.viewer") != "tab":
            errors.append("VS Code PDF viewer must be set to tab")
        tools = settings.get("latex-workshop.latex.tools", [])
        recipes = settings.get("latex-workshop.latex.recipes", [])
        xelatex_tools = [
            item for item in tools
            if isinstance(item, dict)
            and item.get("command") == "latexmk"
            and "-xelatex" in item.get("args", [])
            and "-outdir=%OUTDIR%" in item.get("args", [])
        ]
        if not xelatex_tools:
            errors.append("VS Code has no latexmk XeLaTeX tool using %OUTDIR%")
        if not any(
            isinstance(item, dict)
            and item.get("name") == "latexmk (XeLaTeX)"
            and "latexmk-xelatex" in item.get("tools", [])
            for item in recipes
        ):
            errors.append("VS Code has no latexmk (XeLaTeX) recipe")

    extensions_path = paper_dir / ".vscode" / "extensions.json"
    if extensions_path in text_files:
        try:
            extensions = json.loads(text_files[extensions_path])
        except json.JSONDecodeError as exc:
            errors.append(f".vscode/extensions.json is invalid JSON: {exc}")
        else:
            recommendations = [str(item).lower() for item in extensions.get("recommendations", [])]
            if "james-yu.latex-workshop" not in recommendations:
                errors.append("VS Code does not recommend James-Yu.latex-workshop")

    referenced_inputs: list[str] = []
    referenced_graphics: list[str] = []
    active_tex_files = reachable_tex_files(paper_dir)
    for owner in active_tex_files:
        raw_text = text_files.get(owner)
        if raw_text is None:
            raw_text = owner.read_text(encoding="utf-8", errors="replace")
        text = strip_comments(raw_text)
        for argument in INPUT_RE.findall(text):
            referenced_inputs.append(argument)
            if resolve_input(paper_dir, owner, argument, ".tex") is None:
                errors.append(
                    f"missing or nonportable TeX input from {owner.relative_to(paper_dir).as_posix()}: {argument}"
                )
        for argument in GRAPHIC_RE.findall(text):
            referenced_graphics.append(argument)
            if any(marker in argument for marker in ("\\", "#", "$")):
                warnings.append(f"dynamic graphic path was not resolved statically: {argument}")
                continue
            candidate = Path(argument)
            found = False
            suffixes = ("",) if candidate.suffix else GRAPHIC_SUFFIXES
            for suffix in suffixes:
                relative = candidate if suffix == "" else Path(str(candidate) + suffix)
                for base in (owner.parent, paper_dir, paper_dir / "figures"):
                    if (base / relative).is_file():
                        found = True
                        break
                if found:
                    break
            if not found:
                errors.append(
                    f"missing graphic from {owner.relative_to(paper_dir).as_posix()}: {argument}"
                )
    details["referenced_inputs"] = referenced_inputs
    details["referenced_graphics"] = referenced_graphics
    details["reachable_tex_files"] = [
        path.relative_to(paper_dir).as_posix() for path in active_tex_files
    ]
    details["source_files"] = [
        path.relative_to(paper_dir).as_posix() for path in source_files(paper_dir)
    ]
    return errors, warnings, details


def log_errors(log_path: Path) -> list[str]:
    if not log_path.is_file():
        return [f"build log is missing: {log_path.name}"]
    text = log_path.read_text(encoding="utf-8", errors="replace")
    findings: list[str] = []
    for pattern in LOG_ERROR_PATTERNS:
        if pattern.search(text):
            findings.append(f"{log_path.name} matches {pattern.pattern}")
    return findings


def run_build(paper_dir: Path, output_dir: str | None) -> tuple[list[str], dict[str, Any]]:
    command = [
        shutil.which("latexmk") or "latexmk",
        "-xelatex",
        "-synctex=1",
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-file-line-error",
    ]
    if output_dir:
        command.append(f"-outdir={output_dir}")
    command.append("main.tex")
    result = subprocess.run(command, cwd=paper_dir, capture_output=True, text=True, errors="replace")
    pdf_path = paper_dir / output_dir / "main.pdf" if output_dir else paper_dir / "main.pdf"
    log_path = paper_dir / output_dir / "main.log" if output_dir else paper_dir / "main.log"
    errors: list[str] = []
    if result.returncode != 0:
        tail = "\n".join((result.stdout + "\n" + result.stderr).splitlines()[-20:])
        errors.append(f"latexmk failed for {output_dir or 'paper root'}:\n{tail}")
    if not pdf_path.is_file() or pdf_path.stat().st_size == 0:
        errors.append(f"PDF is missing or empty: {pdf_path.relative_to(paper_dir).as_posix()}")
    errors.extend(log_errors(log_path))
    return errors, {
        "command": command,
        "returncode": result.returncode,
        "pdf": pdf_path.relative_to(paper_dir).as_posix(),
        "pdf_bytes": pdf_path.stat().st_size if pdf_path.is_file() else 0,
        "log": log_path.relative_to(paper_dir).as_posix(),
    }


def verify_latex_project(paper_dir: Path, static_only: bool = False) -> dict[str, Any]:
    paper_dir = paper_dir.resolve()
    errors, warnings, details = static_checks(paper_dir)
    builds: list[dict[str, Any]] = []
    compile_backed = False
    latexmk = shutil.which("latexmk")
    if not static_only and latexmk and not errors:
        root_errors, root_build = run_build(paper_dir, None)
        errors.extend(root_errors)
        builds.append(root_build)
        vscode_errors, vscode_build = run_build(paper_dir, "build")
        errors.extend(vscode_errors)
        builds.append(vscode_build)
        compile_backed = not errors
    elif not static_only and not latexmk:
        warnings.append("latexmk is unavailable; compilation was not verified")
    elif static_only:
        warnings.append("static-only mode does not verify PDF compilation")
    status = "FAIL" if errors else ("PASS" if compile_backed else "LIMITED")
    return {
        "status": status,
        "compile_backed": compile_backed,
        "engine": "xelatex",
        "build_driver": "latexmk",
        "source_sha256": source_fingerprint(paper_dir),
        "builds": builds,
        "details": details,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--paper-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--static-only", action="store_true")
    args = parser.parse_args()
    payload = verify_latex_project(args.paper_dir, static_only=args.static_only)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(payload["status"])
    if payload["status"] == "PASS":
        return 0
    return 1 if payload["status"] == "FAIL" else 2


if __name__ == "__main__":
    raise SystemExit(main())
