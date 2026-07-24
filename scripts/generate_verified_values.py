#!/usr/bin/env python3
"""Generate deterministic LaTeX macros from a verified result registry."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


REQUIRED_COLUMNS = {"key", "value", "unit", "source_file", "source_sha256"}
KEY_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]*$")
SHA256_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")
SUPPORTED_TYPES = {"integer", "number", "boolean", "string"}
TRUE_VALUES = {"1", "true", "yes"}
FALSE_VALUES = {"0", "false", "no"}


@dataclass(frozen=True)
class VerifiedValue:
    key: str
    value: str
    value_type: str
    unit: str
    source_file: str
    source_sha256: str
    source_locator: str
    source_kind: str
    justification: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def project_file(root: Path, relative: str) -> Path | None:
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    resolved_root = root.resolve()
    resolved = (resolved_root / candidate).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError:
        return None
    return resolved


def canonical_value(raw: str, value_type: str) -> tuple[str | None, Any, str | None]:
    text = raw.strip()
    if value_type == "integer":
        try:
            decimal = Decimal(text)
        except InvalidOperation:
            return None, None, f"invalid integer value: {raw!r}"
        if not decimal.is_finite() or decimal != decimal.to_integral_value():
            return None, None, f"invalid integer value: {raw!r}"
        integer = int(decimal)
        return str(integer), integer, None
    if value_type == "number":
        try:
            decimal = Decimal(text)
        except InvalidOperation:
            return None, None, f"invalid numeric value: {raw!r}"
        if not decimal.is_finite():
            return None, None, f"numeric value must be finite: {raw!r}"
        canonical = format(decimal.normalize(), "f")
        if "." in canonical:
            canonical = canonical.rstrip("0").rstrip(".")
        if canonical in {"-0", ""}:
            canonical = "0"
        return canonical, decimal, None
    if value_type == "boolean":
        lowered = text.lower()
        if lowered in TRUE_VALUES:
            return "true", True, None
        if lowered in FALSE_VALUES:
            return "false", False, None
        return None, None, f"invalid boolean value: {raw!r}"
    if value_type == "string":
        if not text:
            return None, None, "string value must not be empty"
        return text, text, None
    return None, None, f"unsupported value type: {value_type!r}"


def typed_equal(actual: Any, expected: Any, value_type: str) -> bool:
    if value_type == "integer":
        if isinstance(actual, bool):
            return False
        try:
            return Decimal(str(actual)) == Decimal(expected)
        except (InvalidOperation, ValueError):
            return False
    if value_type == "number":
        if isinstance(actual, bool):
            return False
        try:
            left = Decimal(str(actual))
            return left.is_finite() and left == expected
        except (InvalidOperation, ValueError):
            return False
    if value_type == "boolean":
        if isinstance(actual, bool):
            return actual is expected
        if isinstance(actual, str):
            lowered = actual.strip().lower()
            return (expected and lowered in TRUE_VALUES) or (
                not expected and lowered in FALSE_VALUES
            )
        return False
    return str(actual).strip() == str(expected)


def json_pointer(payload: Any, pointer: str) -> Any:
    if pointer == "":
        return payload
    if not pointer.startswith("/"):
        raise ValueError("JSON locator must be an RFC 6901 pointer beginning with '/'")
    current = payload
    for raw_token in pointer[1:].split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            try:
                current = current[int(token)]
            except (ValueError, IndexError) as exc:
                raise ValueError(f"JSON pointer index not found: {token}") from exc
        elif isinstance(current, dict) and token in current:
            current = current[token]
        else:
            raise ValueError(f"JSON pointer key not found: {token}")
    return current


def contains_typed_value(payload: Any, expected: Any, value_type: str) -> bool:
    if isinstance(payload, dict):
        return any(contains_typed_value(item, expected, value_type) for item in payload.values())
    if isinstance(payload, list):
        return any(contains_typed_value(item, expected, value_type) for item in payload)
    return typed_equal(payload, expected, value_type)


def source_value_matches(
    path: Path,
    locator: str,
    expected: Any,
    value_type: str,
) -> tuple[bool, str | None]:
    suffix = path.suffix.lower()
    try:
        if suffix == ".json":
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
            pointer = locator
            if pointer.startswith("json:"):
                pointer = pointer[5:]
            if pointer:
                actual = json_pointer(payload, pointer)
                return typed_equal(actual, expected, value_type), None
            return contains_typed_value(payload, expected, value_type), None

        if suffix == ".csv":
            with path.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            if locator.startswith("csv:"):
                locator = locator[4:]
            if locator:
                match = re.fullmatch(r"row=(\d+);column=([A-Za-z_][A-Za-z0-9_.-]*)", locator)
                if not match:
                    return False, "CSV locator must use row=<1-based-data-row>;column=<name>"
                row_number = int(match.group(1))
                column = match.group(2)
                if row_number < 1 or row_number > len(rows):
                    return False, f"CSV row is outside 1..{len(rows)}"
                if column not in rows[row_number - 1]:
                    return False, f"CSV column not found: {column}"
                return typed_equal(rows[row_number - 1][column], expected, value_type), None
            return any(
                typed_equal(cell, expected, value_type)
                for row in rows
                for cell in row.values()
            ), None

        text = path.read_text(encoding="utf-8-sig")
        if locator.startswith("text:"):
            locator = locator[5:]
        if locator:
            match = re.fullmatch(r"line=(\d+)", locator)
            if not match:
                return False, "text locator must use line=<1-based-line>"
            lines = text.splitlines()
            line_number = int(match.group(1))
            if line_number < 1 or line_number > len(lines):
                return False, f"text line is outside 1..{len(lines)}"
            text = lines[line_number - 1]
        canonical, _, error = canonical_value(str(expected), value_type)
        if error:
            return False, error
        if value_type in {"integer", "number"}:
            pattern = re.compile(
                r"(?<![A-Za-z0-9_.])" + re.escape(canonical) + r"(?![A-Za-z0-9_.])"
            )
            return pattern.search(text) is not None, None
        if value_type == "boolean":
            return canonical in text.lower(), None
        return canonical in text, None
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        return False, str(exc)


def load_registry(
    project_dir: Path,
    registry_path: Path,
) -> tuple[list[VerifiedValue], list[str], str]:
    errors: list[str] = []
    values: list[VerifiedValue] = []
    if not registry_path.is_file():
        return [], [f"registry is missing: {registry_path}"], ""

    registry_sha256 = sha256_file(registry_path)
    try:
        with registry_path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = set(reader.fieldnames or [])
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        return [], [f"cannot read registry: {exc}"], registry_sha256

    missing = REQUIRED_COLUMNS - fields
    if "value_type" not in fields and "type" not in fields:
        missing.add("value_type")
    if missing:
        errors.append("registry missing columns: " + ", ".join(sorted(missing)))
        return [], errors, registry_sha256
    if not rows:
        errors.append("registry has no value rows")
        return [], errors, registry_sha256

    seen: set[str] = set()
    for line_number, row in enumerate(rows, 2):
        key = (row.get("key") or "").strip()
        raw_value = (row.get("value") or "").strip()
        value_type = (row.get("value_type") or row.get("type") or "").strip().lower()
        unit = (row.get("unit") or "").strip()
        source_file = (row.get("source_file") or "").strip()
        source_hash = (row.get("source_sha256") or "").strip().lower()
        locator = (row.get("source_locator") or "").strip()
        source_kind = (row.get("source_kind") or "computed").strip().lower()
        justification = (row.get("justification") or "").strip()
        prefix = f"{registry_path.name}:{line_number}"

        if not KEY_PATTERN.fullmatch(key):
            errors.append(f"{prefix} invalid key: {key!r}")
        elif key in seen:
            errors.append(f"{prefix} duplicate key: {key}")
        else:
            seen.add(key)
        if value_type not in SUPPORTED_TYPES:
            errors.append(f"{prefix} unsupported value_type: {value_type!r}")
        canonical, typed, type_error = canonical_value(raw_value, value_type)
        if type_error:
            errors.append(f"{prefix} {type_error}")
        if not unit:
            errors.append(f"{prefix} unit must not be empty; use 'dimensionless' when appropriate")
        if source_kind not in {"computed", "manual"}:
            errors.append(f"{prefix} source_kind must be computed or manual")
        if source_kind == "manual" and not justification:
            errors.append(f"{prefix} manual value requires a justification")
        if not source_file:
            errors.append(f"{prefix} source_file must not be empty")
            source_path = None
        else:
            source_path = project_file(project_dir, source_file)
            if source_path is None:
                errors.append(f"{prefix} source_file must stay inside the project: {source_file}")
            elif not source_path.is_file():
                errors.append(f"{prefix} source file is missing: {source_file}")
        if not SHA256_PATTERN.fullmatch(source_hash):
            errors.append(f"{prefix} source_sha256 must be a 64-character hexadecimal digest")
        elif source_path is not None and source_path.is_file():
            actual_hash = sha256_file(source_path)
            if actual_hash != source_hash:
                errors.append(
                    f"{prefix} source SHA-256 mismatch for {source_file}: "
                    f"registered {source_hash}, actual {actual_hash}"
                )
            elif type_error is None:
                matches, locator_error = source_value_matches(
                    source_path, locator, typed, value_type
                )
                if locator_error:
                    errors.append(f"{prefix} invalid source_locator: {locator_error}")
                elif not matches:
                    location = f" at {locator}" if locator else ""
                    errors.append(
                        f"{prefix} value {canonical!r} not found in {source_file}{location}"
                    )

        if (
            key
            and KEY_PATTERN.fullmatch(key)
            and canonical is not None
            and value_type in SUPPORTED_TYPES
        ):
            values.append(
                VerifiedValue(
                    key=key,
                    value=canonical,
                    value_type=value_type,
                    unit=unit,
                    source_file=source_file,
                    source_sha256=source_hash,
                    source_locator=locator,
                    source_kind=source_kind,
                    justification=justification,
                )
            )
    return values, errors, registry_sha256


def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "{": r"\{",
        "}": r"\}",
        "$": r"\$",
        "&": r"\&",
        "#": r"\#",
        "%": r"\%",
        "_": r"\_",
        "^": r"\textasciicircum{}",
        "~": r"\textasciitilde{}",
    }
    return "".join(replacements.get(character, character) for character in text)


def render_latex(values: list[VerifiedValue], registry_sha256: str) -> str:
    lines = [
        "% Generated by scripts/generate_verified_values.py; do not edit.",
        f"% registry-sha256: {registry_sha256}",
        r"\providecommand{\VerifiedValue}[1]{\csname verifiedvalue@#1\endcsname}",
        r"\providecommand{\VerifiedUnit}[1]{\csname verifiedunit@#1\endcsname}",
        r"\providecommand{\VerifiedValueWithUnit}[1]{\VerifiedValue{#1}\,\VerifiedUnit{#1}}",
    ]
    for item in values:
        rendered_value = (
            item.value
            if item.value_type in {"integer", "number"}
            else latex_escape(item.value)
        )
        lines.extend(
            [
                f"% {item.key}: {item.value_type}; source-sha256: {item.source_sha256}",
                rf"\expandafter\def\csname verifiedvalue@{item.key}\endcsname{{{rendered_value}}}",
                rf"\expandafter\def\csname verifiedunit@{item.key}\endcsname{{{latex_escape(item.unit)}}}",
            ]
        )
    return "\n".join(lines) + "\n"


def resolve_cli_path(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate paper/generated/results.tex from results/verified_values.csv."
    )
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument(
        "--registry", type=Path, default=Path("results/verified_values.csv")
    )
    parser.add_argument(
        "--out", type=Path, default=Path("paper/generated/results.tex")
    )
    args = parser.parse_args()
    root = args.project_dir.resolve()
    registry = resolve_cli_path(root, args.registry).resolve()
    out = resolve_cli_path(root, args.out).resolve()
    try:
        registry.relative_to(root)
    except ValueError:
        raise SystemExit("registry must stay inside the project directory")
    try:
        out.relative_to(root)
    except ValueError:
        raise SystemExit("output must stay inside the project directory")

    values, errors, registry_sha256 = load_registry(root, registry)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    rendered = render_latex(values, registry_sha256)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(rendered, encoding="utf-8")
    print(f"PASS: generated {out.relative_to(root).as_posix()} with {len(values)} values")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
