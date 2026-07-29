#!/usr/bin/env python3
"""Freeze portable LaTeX dependency and configuration evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

from verify_latex_compatibility import source_fingerprint


PACKAGE_RE = re.compile(r"\\usepackage(?:\[[^\]]*\])?\{([^}]+)\}")
FONT_RE = re.compile(r"\\(?:setmainfont|setsansfont|setmonofont|setCJKmainfont|setCJKsansfont|setCJKmonofont)\{([^}]+)\}")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def version(command: str) -> str:
    executable = shutil.which(command)
    if executable is None:
        return ""
    try:
        result = subprocess.run([executable, "--version"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return next((line.strip() for line in (result.stdout + "\n" + result.stderr).splitlines() if line.strip()), "")


def main() -> int:
    parser = argparse.ArgumentParser(description="Freeze LaTeX package, font, and editor-build evidence.")
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--out", default="reports/latex_dependency_lock.json")
    args = parser.parse_args()
    root = args.project_dir.resolve()
    paper = root / "paper"
    main_tex = paper / "main.tex"
    latexmkrc = paper / ".latexmkrc"
    settings = paper / ".vscode" / "settings.json"
    extensions = paper / ".vscode" / "extensions.json"
    required = (main_tex, latexmkrc, settings, extensions)
    errors = [f"missing required portable-build file: {path.relative_to(root).as_posix()}" for path in required if not path.is_file()]
    text = main_tex.read_text(encoding="utf-8", errors="replace") if main_tex.is_file() else ""
    packages = sorted({item.strip() for match in PACKAGE_RE.findall(text) for item in match.split(",") if item.strip()})
    fonts = sorted({item.strip() for item in FONT_RE.findall(text) if item.strip()})
    latexmk_version = version("latexmk")
    xelatex_version = version("xelatex")
    warnings: list[str] = []
    if not latexmk_version:
        warnings.append("latexmk is unavailable; dependency lock is not compiler-backed")
    if not xelatex_version:
        warnings.append("xelatex is unavailable; dependency lock is not compiler-backed")
    status = "FAIL" if errors else ("PASS" if not warnings else "LIMITED")
    payload = {
        "status": status,
        "scope": "portable dependency/configuration lock only; use verify_latex_compatibility.py for actual dual-layout compilation",
        "source_sha256": source_fingerprint(paper) if paper.is_dir() else "",
        "main_tex_sha256": digest(main_tex) if main_tex.is_file() else "",
        "latexmkrc_sha256": digest(latexmkrc) if latexmkrc.is_file() else "",
        "vscode_settings_sha256": digest(settings) if settings.is_file() else "",
        "vscode_extensions_sha256": digest(extensions) if extensions.is_file() else "",
        "engine": "xelatex", "latexmk_version": latexmk_version, "xelatex_version": xelatex_version,
        "packages": packages, "fonts": fonts, "errors": errors, "warnings": warnings,
    }
    out = root / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(payload["status"])
    return 0 if status == "PASS" else (1 if status == "FAIL" else 2)


if __name__ == "__main__":
    raise SystemExit(main())
