#!/usr/bin/env python3
"""Create a portable XeLaTeX paper project for Overleaf and VS Code."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = {
    "cumcm": ROOT / "assets" / "latex-paper-template",
    "mcm-icm": ROOT / "assets" / "latex-paper-template-mcm",
}


class ScaffoldError(RuntimeError):
    """Raised when scaffolding would be incomplete or unsafe."""


def paper_files(paper_dir: Path) -> list[Path]:
    if not paper_dir.is_dir():
        return []
    return sorted(path for path in paper_dir.rglob("*") if path.is_file())


def scaffold_latex_paper(project_dir: Path, force: bool = False, template: str = "cumcm") -> list[Path]:
    project_dir = project_dir.resolve()
    paper_dir = project_dir / "paper"
    existing = paper_files(paper_dir)
    if existing and not force:
        names = ", ".join(path.relative_to(project_dir).as_posix() for path in existing[:5])
        suffix = " ..." if len(existing) > 5 else ""
        raise ScaffoldError(f"paper directory is not empty; use --force to overwrite template files: {names}{suffix}")
    template_dir = TEMPLATES[template]
    if not template_dir.is_dir():
        raise ScaffoldError(f"template directory is missing: {template_dir}")

    created: list[Path] = []
    for source in sorted(template_dir.rglob("*")):
        if not source.is_file():
            continue
        relative = source.relative_to(template_dir)
        destination = paper_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        created.append(destination)
    for relative in ("figures", "build"):
        (paper_dir / relative).mkdir(parents=True, exist_ok=True)
    if not created:
        raise ScaffoldError("template contains no files")
    return created


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--template", choices=sorted(TEMPLATES), default="cumcm")
    args = parser.parse_args()
    try:
        created = scaffold_latex_paper(args.project_dir, force=args.force, template=args.template)
    except (OSError, ScaffoldError) as exc:
        print(f"ERROR: {exc}")
        return 1
    root = args.project_dir.resolve()
    for path in created:
        print(path.relative_to(root).as_posix())
    print(f"CREATED {len(created)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
