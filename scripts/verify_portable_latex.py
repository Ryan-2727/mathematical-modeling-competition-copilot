#!/usr/bin/env python3
"""Verify a portable LaTeX ZIP by reusing the canonical project validator."""
from __future__ import annotations

import argparse
import json
import re
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from verify_latex_compatibility import verify_latex_project


REQUIRED = {
    "main.tex",
    "README.md",
    "references.bib",
    ".latexmkrc",
    ".vscode/settings.json",
    ".vscode/extensions.json",
}
README_PHRASES = {"VS Code", "Overleaf", "XeLaTeX", "main.tex", "Ctrl+Alt+V"}


def archive_names(archive: zipfile.ZipFile) -> set[str]:
    names: set[str] = set()
    for item in archive.infolist():
        path = PurePosixPath(item.filename)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"unsafe archive entry: {item.filename}")
        if not item.is_dir():
            names.add(path.as_posix())
    return names


def page_count(log_path: Path) -> int | None:
    if not log_path.is_file():
        return None
    text = log_path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"Output written on main\.pdf \((\d+) pages?", text)
    return int(match.group(1)) if match else None


def verify_archive(path: Path, compile_requested: bool) -> dict[str, object]:
    errors: list[str] = []
    details: dict[str, object] = {
        "archive": str(path),
        "entries": 0,
        "pages": None,
    }
    if not path.is_file():
        errors.append(f"archive not found: {path}")
        return {"status": "FAIL", "details": details, "errors": errors}

    with tempfile.TemporaryDirectory(prefix="portable_latex_") as raw:
        root = Path(raw)
        try:
            with zipfile.ZipFile(path) as archive:
                names = archive_names(archive)
                details["entries"] = len(names)
                missing = sorted(REQUIRED - names)
                if missing:
                    errors.append("archive missing required files: " + ", ".join(missing))
                if any(name.startswith("paper/") for name in names):
                    errors.append("ZIP contents must be at the archive root, not inside paper/")
                if "README.md" in names:
                    readme = archive.read("README.md").decode("utf-8-sig", errors="replace")
                    for phrase in sorted(README_PHRASES):
                        if phrase not in readme:
                            errors.append(f"README.md missing portable-build instruction: {phrase}")
                if not errors:
                    archive.extractall(root)
        except (OSError, ValueError, zipfile.BadZipFile) as exc:
            errors.append(str(exc))

        compatibility: dict[str, object] = {}
        if not errors:
            compatibility = verify_latex_project(root, static_only=not compile_requested)
            errors.extend(str(item) for item in compatibility.get("errors", []))
            details["compatibility"] = compatibility
            details["pages"] = page_count(root / "main.log")

    return {
        "status": "PASS" if not errors else "FAIL",
        "scope": (
            "portable ZIP root and canonical Overleaf/VS Code project validation; "
            "not a remote Overleaf UI test"
        ),
        "compile_requested": compile_requested,
        "details": details,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--compile", action="store_true")
    parser.add_argument("--expected-pages", type=int)
    args = parser.parse_args()

    report = verify_archive(args.archive, args.compile)
    if args.expected_pages is not None and report["details"].get("pages") != args.expected_pages:
        report["errors"].append(
            f"expected {args.expected_pages} PDF pages, found {report['details'].get('pages')}"
        )
        report["status"] = "FAIL"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(report["status"])
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
