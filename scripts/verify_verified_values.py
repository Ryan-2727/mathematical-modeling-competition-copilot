#!/usr/bin/env python3
"""Verify numerical registry provenance, generated LaTeX, and actual paper use."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from generate_verified_values import (
    load_registry,
    render_latex,
    resolve_cli_path,
    sha256_file,
)


INPUT_PATTERN = re.compile(r"\\(?:input|include)\s*\{([^{}]+)\}")


def strip_comments(text: str) -> str:
    cleaned: list[str] = []
    for line in text.splitlines():
        index = 0
        while True:
            marker = line.find("%", index)
            if marker < 0:
                cleaned.append(line)
                break
            slashes = 0
            cursor = marker - 1
            while cursor >= 0 and line[cursor] == "\\":
                slashes += 1
                cursor -= 1
            if slashes % 2 == 0:
                cleaned.append(line[:marker])
                break
            index = marker + 1
    return "\n".join(cleaned)


def reachable_tex_files(paper_dir: Path) -> tuple[list[Path], list[str]]:
    main_tex = paper_dir / "main.tex"
    if not main_tex.is_file():
        return [], ["paper/main.tex is missing"]
    errors: list[str] = []
    visited: set[Path] = set()
    pending = [main_tex.resolve()]
    paper_root = paper_dir.resolve()
    while pending:
        path = pending.pop()
        if path in visited:
            continue
        visited.add(path)
        try:
            text = strip_comments(path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError) as exc:
            errors.append(f"cannot read reachable TeX file {path}: {exc}")
            continue
        for raw_name in INPUT_PATTERN.findall(text):
            name = raw_name.strip()
            if "\\" in name:
                errors.append(f"dynamic TeX input cannot be verified in {path.name}: {name}")
                continue
            candidate = Path(name)
            if not candidate.suffix:
                candidate = candidate.with_suffix(".tex")
            resolved = (path.parent / candidate).resolve()
            try:
                resolved.relative_to(paper_root)
            except ValueError:
                errors.append(f"reachable TeX input escapes paper directory: {name}")
                continue
            if not resolved.is_file():
                errors.append(f"reachable TeX input is missing: {name}")
                continue
            pending.append(resolved)
    return sorted(visited), errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify the decisive-value registry and its reachable LaTeX use."
    )
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument(
        "--registry", type=Path, default=Path("results/verified_values.csv")
    )
    parser.add_argument(
        "--generated", type=Path, default=Path("paper/generated/results.tex")
    )
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.project_dir.resolve()
    registry = resolve_cli_path(root, args.registry).resolve()
    generated = resolve_cli_path(root, args.generated).resolve()
    out = resolve_cli_path(root, args.out).resolve()
    errors: list[str] = []
    warnings: list[str] = []

    for label, path in (("registry", registry), ("generated output", generated)):
        try:
            path.relative_to(root)
        except ValueError:
            errors.append(f"{label} must stay inside the project directory")
    try:
        out.relative_to(root)
    except ValueError:
        raise SystemExit("report must stay inside the project directory")

    values, registry_errors, registry_sha256 = (
        load_registry(root, registry)
        if registry.is_relative_to(root)
        else ([], [], "")
    )
    errors.extend(registry_errors)
    expected = render_latex(values, registry_sha256) if not registry_errors else ""
    generated_inside = generated.is_relative_to(root)
    if not generated_inside:
        generated_sha256 = ""
    elif not generated.is_file():
        errors.append("paper/generated/results.tex is missing; run generate_verified_values.py")
        generated_sha256 = ""
    else:
        generated_sha256 = sha256_file(generated)
        try:
            actual = generated.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as exc:
            errors.append(f"cannot read generated LaTeX: {exc}")
            actual = ""
        if expected and actual != expected:
            errors.append(
                "generated LaTeX is stale or manually modified; rerun generate_verified_values.py"
            )

    paper_dir = root / "paper"
    reachable, reachability_errors = reachable_tex_files(paper_dir)
    errors.extend(reachability_errors)
    generated_resolved = generated.resolve()
    if generated_inside and reachable and generated_resolved not in reachable:
        errors.append(
            "paper/generated/results.tex is not reachable from paper/main.tex"
        )

    source_texts: list[str] = []
    for path in reachable:
        if path == generated_resolved:
            continue
        try:
            source_texts.append(strip_comments(path.read_text(encoding="utf-8-sig")))
        except (OSError, UnicodeError):
            pass
    paper_source = "\n".join(source_texts)
    used_keys: list[str] = []
    for item in values:
        use_pattern = re.compile(
            r"\\VerifiedValue(?:WithUnit)?\s*\{\s*" + re.escape(item.key) + r"\s*\}"
        )
        if use_pattern.search(paper_source):
            used_keys.append(item.key)
        else:
            errors.append(
                f"verified value is not actually used in reachable LaTeX: {item.key}"
            )

    payload = {
        "status": "PASS" if not errors else "FAIL",
        "scope": (
            "registry schema, declared source provenance, deterministic generated "
            "LaTeX, and reachable macro use; not mathematical correctness"
        ),
        "registry": str(registry.relative_to(root)).replace("\\", "/")
        if registry.is_relative_to(root)
        else str(registry),
        "generated": str(generated.relative_to(root)).replace("\\", "/")
        if generated.is_relative_to(root)
        else str(generated),
        "registry_sha256": registry_sha256,
        "generated_sha256": generated_sha256,
        "counts": {
            "registered_values": len(values),
            "used_values": len(used_keys),
            "reachable_tex_files": len(reachable),
        },
        "used_keys": sorted(used_keys),
        "reachable_tex_files": [
            path.relative_to(root).as_posix()
            for path in reachable
            if path.is_relative_to(root)
        ],
        "errors": errors,
        "warnings": warnings,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(payload["status"])
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
