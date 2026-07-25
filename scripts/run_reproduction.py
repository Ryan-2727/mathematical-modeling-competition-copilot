#!/usr/bin/env python3
"""Run a declared pipeline in clean copies and compare repeated outputs."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import platform
import shlex
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_hashes(
    root: Path,
    excluded: set[Path],
) -> list[dict[str, Any]]:
    hashes: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or ".git" in path.relative_to(root).parts:
            continue
        resolved = path.resolve()
        if any(resolved == item or item in resolved.parents for item in excluded):
            continue
        hashes.append(
            {
                "file": path.relative_to(root).as_posix(),
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
        )
    return hashes


def windows_style_split(command: str) -> list[str]:
    tokens = shlex.split(command, posix=False)
    result: list[str] = []
    for token in tokens:
        if len(token) >= 2 and token[0] == token[-1] and token[0] in {'"', "'"}:
            token = token[1:-1]
        result.append(token)
    return result


def parse_argv(
    argv_json: str | None,
    arg_values: list[str] | None,
    command: str | None,
    allow_shell: bool,
) -> tuple[list[str] | str, bool, str]:
    if allow_shell:
        if command is None:
            raise ValueError("--allow-shell requires --command")
        return command, True, "explicit shell command"

    if argv_json is not None:
        raw = argv_json
        if raw.startswith("@"):
            raw = Path(raw[1:]).read_text(encoding="utf-8")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"--argv-json is not valid JSON: {exc}") from exc
        if not isinstance(parsed, list) or not parsed or not all(
            isinstance(item, str) and item for item in parsed
        ):
            raise ValueError("--argv-json must contain a non-empty JSON array of strings")
        return parsed, False, "JSON argv"

    if arg_values:
        return arg_values, False, "repeated --arg values"

    if command is None:
        raise ValueError("one of --argv-json, --arg, or --command is required")
    try:
        parsed = json.loads(command)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, list) and parsed and all(
        isinstance(item, str) and item for item in parsed
    ):
        return parsed, False, "JSON argv supplied through --command"

    values = windows_style_split(command) if os.name == "nt" else shlex.split(command)
    if not values:
        raise ValueError("--command produced an empty argv")
    return values, False, "compatibility command string parsed to argv without a shell"


def copy_ignore(
    excluded: set[Path],
):
    def ignore(directory: str, names: list[str]) -> set[str]:
        ignored: set[str] = set()
        parent = Path(directory)
        for name in names:
            candidate = (parent / name).resolve()
            if name in {".git", "__pycache__", ".pytest_cache"}:
                ignored.add(name)
            elif any(candidate == item or item in candidate.parents for item in excluded):
                ignored.add(name)
        return ignored

    return ignore


def parse_number(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None


def compare_csv(
    baseline: bytes,
    candidate: bytes,
    *,
    atol: float,
    rtol: float,
) -> list[str]:
    try:
        baseline_rows = list(csv.reader(io.StringIO(baseline.decode("utf-8-sig"))))
        candidate_rows = list(csv.reader(io.StringIO(candidate.decode("utf-8-sig"))))
    except UnicodeDecodeError:
        return ["CSV output is not UTF-8 decodable"]
    if len(baseline_rows) != len(candidate_rows):
        return [
            f"CSV row count differs: {len(baseline_rows)} versus {len(candidate_rows)}"
        ]
    errors: list[str] = []
    for row_index, (left_row, right_row) in enumerate(
        zip(baseline_rows, candidate_rows), 1
    ):
        if len(left_row) != len(right_row):
            errors.append(
                f"CSV row {row_index} column count differs: "
                f"{len(left_row)} versus {len(right_row)}"
            )
            continue
        for column_index, (left, right) in enumerate(zip(left_row, right_row), 1):
            left_number = parse_number(left.strip())
            right_number = parse_number(right.strip())
            if left_number is not None and right_number is not None:
                if not math.isclose(
                    left_number,
                    right_number,
                    rel_tol=rtol,
                    abs_tol=atol,
                ):
                    errors.append(
                        f"CSV cell {row_index},{column_index} differs beyond "
                        f"atol={atol}, rtol={rtol}: {left} versus {right}"
                    )
            elif left != right:
                errors.append(
                    f"CSV cell {row_index},{column_index} differs: "
                    f"{left!r} versus {right!r}"
                )
            if len(errors) >= 20:
                errors.append("CSV comparison stopped after 20 differences")
                return errors
    return errors


def compare_runs(
    snapshots: list[dict[str, bytes]],
    expected: list[str],
    *,
    mode: str,
    atol: float,
    rtol: float,
) -> tuple[list[dict[str, Any]], list[str]]:
    comparisons: list[dict[str, Any]] = []
    errors: list[str] = []
    if len(snapshots) < 2:
        return comparisons, errors
    baseline = snapshots[0]
    for run_index, current in enumerate(snapshots[1:], 2):
        for relative in expected:
            if relative not in baseline or relative not in current:
                continue
            selected = "csv" if mode == "auto" and relative.lower().endswith(".csv") else mode
            if selected == "auto":
                selected = "hash"
            if selected == "csv":
                differences = compare_csv(
                    baseline[relative],
                    current[relative],
                    atol=atol,
                    rtol=rtol,
                )
            else:
                differences = (
                    []
                    if hashlib.sha256(baseline[relative]).digest()
                    == hashlib.sha256(current[relative]).digest()
                    else ["SHA-256 differs"]
                )
            comparisons.append(
                {
                    "baseline_run": 1,
                    "candidate_run": run_index,
                    "file": relative,
                    "method": selected,
                    "match": not differences,
                    "differences": differences,
                }
            )
            errors.extend(
                f"run {run_index} {relative}: {difference}"
                for difference in differences
            )
    return comparisons, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, required=True)
    command_group = parser.add_mutually_exclusive_group(required=True)
    command_group.add_argument("--argv-json")
    command_group.add_argument("--arg", action="append", dest="arg_values")
    command_group.add_argument("--command")
    parser.add_argument("--allow-shell", action="store_true")
    parser.add_argument("--seed", default="0")
    parser.add_argument("--expected", action="append", default=[])
    parser.add_argument("--repeat", type=int, default=2)
    parser.add_argument(
        "--comparison",
        choices=("auto", "hash", "csv"),
        default="auto",
    )
    parser.add_argument("--csv-atol", type=float, default=1e-9)
    parser.add_argument("--csv-rtol", type=float, default=1e-7)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    errors: list[str] = []
    try:
        command, use_shell, command_source = parse_argv(
            args.argv_json,
            args.arg_values,
            args.command,
            args.allow_shell,
        )
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    if args.repeat < 1:
        parser.error("--repeat must be at least 1")
    if args.csv_atol < 0 or args.csv_rtol < 0:
        parser.error("CSV tolerances must be nonnegative")

    project_dir = args.project_dir.resolve()
    out = args.out.resolve()
    if not project_dir.is_dir():
        errors.append("project directory is missing")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    log_root = out.parent / f"{out.stem}_runs" / stamp
    log_root.mkdir(parents=True, exist_ok=True)
    excluded = {out, log_root.parent.resolve()}
    inputs = source_hashes(project_dir, excluded) if project_dir.is_dir() else []
    run_reports: list[dict[str, Any]] = []
    snapshots: list[dict[str, bytes]] = []

    if not errors:
        for run_index in range(1, args.repeat + 1):
            run_log_dir = log_root / f"run-{run_index:02d}"
            run_log_dir.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix=f"reproduction-{run_index:02d}-") as raw:
                clean_project = Path(raw) / "project"
                shutil.copytree(
                    project_dir,
                    clean_project,
                    ignore=copy_ignore(excluded),
                )
                env = os.environ.copy()
                env["PYTHONHASHSEED"] = args.seed
                env["REPRODUCTION_RUN_INDEX"] = str(run_index)
                result = subprocess.run(
                    command,
                    cwd=clean_project,
                    shell=use_shell,
                    text=True,
                    capture_output=True,
                    env=env,
                    encoding="utf-8",
                    errors="replace",
                    check=False,
                )
                (run_log_dir / "stdout.log").write_text(
                    result.stdout, encoding="utf-8"
                )
                (run_log_dir / "stderr.log").write_text(
                    result.stderr, encoding="utf-8"
                )
                run_errors: list[str] = []
                if result.returncode != 0:
                    run_errors.append(
                        f"command returned {result.returncode}"
                    )
                outputs: list[dict[str, Any]] = []
                snapshot: dict[str, bytes] = {}
                for item in args.expected:
                    relative_path = Path(item)
                    if relative_path.is_absolute() or ".." in relative_path.parts:
                        run_errors.append(f"unsafe expected output path: {item}")
                        continue
                    path = clean_project / relative_path
                    if not path.is_file():
                        run_errors.append(f"expected output missing: {item}")
                        continue
                    content = path.read_bytes()
                    normalized = relative_path.as_posix()
                    snapshot[normalized] = content
                    outputs.append(
                        {
                            "file": normalized,
                            "sha256": hashlib.sha256(content).hexdigest(),
                            "bytes": len(content),
                        }
                    )
                (run_log_dir / "outputs.json").write_text(
                    json.dumps(outputs, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                run_reports.append(
                    {
                        "run": run_index,
                        "returncode": result.returncode,
                        "clean_copy": True,
                        "stdout_log": str(run_log_dir / "stdout.log"),
                        "stderr_log": str(run_log_dir / "stderr.log"),
                        "expected_outputs": outputs,
                        "errors": run_errors,
                    }
                )
                snapshots.append(snapshot)
                errors.extend(
                    f"run {run_index}: {message}" for message in run_errors
                )

    normalized_expected = [Path(item).as_posix() for item in args.expected]
    comparisons, comparison_errors = compare_runs(
        snapshots,
        normalized_expected,
        mode=args.comparison,
        atol=args.csv_atol,
        rtol=args.csv_rtol,
    )
    errors.extend(comparison_errors)
    payload = {
        "status": "PASS" if not errors else "FAIL",
        "scope": (
            "isolated clean-copy execution and repeat comparison of declared outputs; "
            "this does not prove undeclared outputs, external services, or mathematical "
            "correctness are reproducible"
        ),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "command_source": command_source,
        "shell": use_shell,
        "seed": args.seed,
        "repeat": args.repeat,
        "comparison": {
            "mode": args.comparison,
            "csv_atol": args.csv_atol,
            "csv_rtol": args.csv_rtol,
        },
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "python_executable": os.path.basename(os.sys.executable),
        },
        "input_files": inputs,
        "reproduction_commands_sha256": sha256(
            project_dir / "support" / "reproduction_commands.txt"
        )
        if (project_dir / "support" / "reproduction_commands.txt").is_file()
        else "",
        "runs": run_reports,
        "comparisons": comparisons,
        "log_directory": str(log_root),
        "errors": errors,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(payload["status"])
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
