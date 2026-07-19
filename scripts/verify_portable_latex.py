#!/usr/bin/env python3
"""Verify that a LaTeX source ZIP is portable for VS Code and Overleaf."""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


REQUIRED = {"main.tex", "README.md", ".latexmkrc", ".vscode/settings.json", "references.bib"}
TEXT_SUFFIXES = {".tex", ".bib", ".cls", ".sty", ".md", ".json", ".rc"}
ABSOLUTE_PATH = re.compile(r"(?:[A-Za-z]:[\\/]|/(?:Users|home)/)")
INPUT_RE = re.compile(r"\\(?:input|include)\s*\{([^{}]+)\}")
GRAPHIC_RE = re.compile(r"\\includegraphics(?:\s*\[[^\]]*\])?\s*\{([^{}]+)\}")
LISTING_RE = re.compile(r"\\lstinputlisting(?:\s*\[[^\]]*\])?\s*\{([^{}]+)\}")
FATAL_LOG = re.compile(
    r"Undefined control sequence|LaTeX Warning: There were undefined references|"
    r"Overfull \\hbox|File .* not found"
)


def add_error(errors: list[str], message: str) -> None:
    if message not in errors:
        errors.append(message)


def archive_names(archive: zipfile.ZipFile) -> set[str]:
    names: set[str] = set()
    for item in archive.infolist():
        path = PurePosixPath(item.filename)
        if item.is_dir():
            continue
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"unsafe archive entry: {item.filename}")
        names.add(path.as_posix())
    return names


def read_text(archive: zipfile.ZipFile, name: str) -> str:
    return archive.read(name).decode("utf-8-sig", errors="replace")


def is_portable_reference(value: str) -> bool:
    path = value.strip().replace("\\", "/")
    return bool(path) and not path.startswith("/") and ".." not in PurePosixPath(path).parts and not ABSOLUTE_PATH.search(path)


def referenced_candidates(value: str, kind: str) -> set[str]:
    path = value.strip().replace("\\", "/")
    if kind == "input" and not Path(path).suffix:
        return {path, f"{path}.tex"}
    if kind == "graphic" and not Path(path).suffix:
        return {f"{path}{suffix}" for suffix in (".pdf", ".png", ".jpg", ".jpeg", ".eps")}
    return {path}


def validate_settings(payload: dict, errors: list[str]) -> None:
    if payload.get("latex-workshop.latex.outDir") != "%DIR%":
        add_error(errors, "VS Code latex-workshop.latex.outDir must be %DIR%")
    if payload.get("latex-workshop.view.pdf.viewer") != "tab":
        add_error(errors, "VS Code PDF viewer must be tab")
    if payload.get("latex-workshop.view.pdf.tab.editorGroup") != "right":
        add_error(errors, "VS Code PDF tab editor group must be right")
    tools = {item.get("name"): item for item in payload.get("latex-workshop.latex.tools", []) if isinstance(item, dict)}
    xelatex = tools.get("xelatex")
    if not xelatex or xelatex.get("command") != "xelatex" or "%DOCFILE%" not in xelatex.get("args", []):
        add_error(errors, "VS Code must define xelatex with %DOCFILE%")
    valid_recipe = any(
        isinstance(item, dict) and item.get("tools") == ["xelatex", "xelatex"]
        for item in payload.get("latex-workshop.latex.recipes", [])
    )
    if not valid_recipe:
        add_error(errors, "VS Code must define a two-pass xelatex recipe")


def validate_archive(path: Path, errors: list[str]) -> dict:
    details: dict = {"archive": str(path), "entries": 0, "referenced_files": 0}
    if not path.is_file():
        add_error(errors, f"archive not found: {path}")
        return details
    with zipfile.ZipFile(path) as archive:
        try:
            names = archive_names(archive)
        except ValueError as exc:
            add_error(errors, str(exc))
            return details
        details["entries"] = len(names)
        missing = sorted(REQUIRED - names)
        if missing:
            add_error(errors, "archive missing required files: " + ", ".join(missing))
            return details
        if any(name.startswith("paper/") for name in names) and "main.tex" not in names:
            add_error(errors, "main.tex must be at the archive root, not inside paper/")
        main_tex = read_text(archive, "main.tex")
        if "% !TeX program = xelatex" not in main_tex or "% !TeX encoding = UTF-8" not in main_tex:
            add_error(errors, "main.tex must declare XeLaTeX and UTF-8")
        try:
            settings = json.loads(read_text(archive, ".vscode/settings.json"))
        except json.JSONDecodeError as exc:
            add_error(errors, f"invalid VS Code settings JSON: {exc.msg}")
        else:
            validate_settings(settings, errors)
        latexmk = read_text(archive, ".latexmkrc")
        if "$pdf_mode = 5" not in latexmk or "xelatex" not in latexmk:
            add_error(errors, ".latexmkrc must select XeLaTeX PDF mode")
        readme = read_text(archive, "README.md")
        for phrase in ("VS Code", "Overleaf", "XeLaTeX", "main.tex", "Ctrl+Alt+V"):
            if phrase not in readme:
                add_error(errors, f"README.md missing portable-build instruction: {phrase}")
        text_files = [
            name for name in names
            if PurePosixPath(name).suffix.lower() in TEXT_SUFFIXES or PurePosixPath(name).name == ".latexmkrc"
        ]
        for name in text_files:
            if ABSOLUTE_PATH.search(read_text(archive, name)):
                add_error(errors, f"absolute path found in {name}")
        tex_files = [name for name in names if PurePosixPath(name).suffix.lower() == ".tex"]
        references: list[tuple[str, str]] = []
        for name in tex_files:
            text = read_text(archive, name)
            for regex, kind in ((INPUT_RE, "input"), (GRAPHIC_RE, "graphic"), (LISTING_RE, "listing")):
                for match in regex.findall(text):
                    if not is_portable_reference(match):
                        add_error(errors, f"non-portable {kind} reference in {name}: {match}")
                        continue
                    candidates = referenced_candidates(match, kind)
                    if not any(candidate in names for candidate in candidates):
                        add_error(errors, f"missing {kind} dependency referenced by {name}: {match}")
                    references.append((name, match))
        details["referenced_files"] = len(references)
    return details


def compile_archive(path: Path, errors: list[str]) -> dict:
    details: dict = {"compiled": False, "pages": None}
    engine = shutil.which("xelatex")
    if not engine:
        add_error(errors, "xelatex is unavailable for portable archive compilation")
        return details
    with tempfile.TemporaryDirectory(prefix="portable_latex_") as raw:
        root = Path(raw)
        with zipfile.ZipFile(path) as archive:
            archive.extractall(root)
        commands = [[engine, "-interaction=nonstopmode", "-halt-on-error", "-file-line-error", "main.tex"]] * 2
        for command in commands:
            result = subprocess.run(
                command, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                encoding="utf-8", errors="replace",
            )
            if result.returncode:
                add_error(errors, "XeLaTeX portable rebuild failed: " + result.stdout[-1000:])
                return details
        pdf = root / "main.pdf"
        log = root / "main.log"
        if not pdf.is_file() or not pdf.stat().st_size:
            add_error(errors, "XeLaTeX did not produce main.pdf")
            return details
        log_text = log.read_text(encoding="utf-8", errors="replace") if log.is_file() else ""
        if FATAL_LOG.search(log_text):
            add_error(errors, "portable rebuild log contains fatal reference or layout finding")
            return details
        page_match = re.search(r"Output written on main\.pdf \((\d+) pages?", log_text)
        details.update({"compiled": True, "pages": int(page_match.group(1)) if page_match else None, "pdf_bytes": pdf.stat().st_size})
    return details


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--compile", action="store_true")
    parser.add_argument("--expected-pages", type=int)
    args = parser.parse_args()

    errors: list[str] = []
    details = validate_archive(args.archive, errors)
    if args.compile and not errors:
        details.update(compile_archive(args.archive, errors))
    if args.expected_pages is not None and details.get("pages") != args.expected_pages:
        add_error(errors, f"expected {args.expected_pages} PDF pages, found {details.get('pages')}")
    report = {
        "status": "PASS" if not errors else "FAIL",
        "scope": "portable ZIP structure and local XeLaTeX rebuild; not a remote Overleaf UI test",
        "compile_requested": args.compile,
        "details": details,
        "errors": errors,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(report["status"])
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
