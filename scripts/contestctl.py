#!/usr/bin/env python3
"""Coordinate phase gates without replacing specialist verifiers."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from verify_latex_compatibility import source_fingerprint

PHASE_ORDER = ("setup", "modeling", "paper", "delivery", "freeze")
FILES = {
    "setup": (
        "contest_manifest.json",
        "rules.lock.json",
        "plan.md",
        "todo.md",
        "reports/contest_rules_snapshot.md",
    ),
    "modeling": (
        "reports/traceability.md",
        "reports/model_decision_log.csv",
        "reports/stress_tests.csv",
        "reports/claims.csv",
        "results/verified_values.csv",
    ),
    "paper": (
        "paper/main.tex",
        "paper/main.pdf",
        "paper/references.bib",
        "reports/paper_depth_plan.csv",
        "reports/bibliography.csv",
        "reports/figure_manifest.csv",
    ),
    "delivery": (
        "delivery/manifest.csv",
        "official-submission/manifest.csv",
    ),
    "freeze": (
        "support/reproduction_commands.txt",
    ),
}
REPORTS = {
    "setup": ("reports/rules_lock_verification.json",),
    "modeling": (
        "reports/model_validation_report.json",
        "reports/verified_values_verification.json",
    ),
    "paper": (
        "reports/abstract_quality.json",
        "reports/manuscript_quality.json",
        "reports/bibliography_verification.json",
        "reports/latex_compatibility.json",
        "reports/paper_depth.json",
    ),
    "delivery": (
        "reports/delivery_profiles.json",
        "reports/paper_delivery.json",
    ),
    "freeze": (
        "reports/reproduction_report.json",
        "reports/anonymity_scan.txt",
        "reports/submission_manifest.json",
    ),
}
CSV_LEDGERS = {
    "modeling": (
        "reports/model_decision_log.csv",
        "reports/stress_tests.csv",
        "reports/claims.csv",
    ),
}
COMPLETE = {"pass", "verified", "complete", "included", "accepted"}
REPORT_BINDINGS = {
    "reports/rules_lock_verification.json": (
        ("rules_lock_sha256", "rules.lock.json", "file"),
    ),
    "reports/model_validation_report.json": (
        ("manifest_sha256", "reports/model_validation.json", "file"),
    ),
    "reports/verified_values_verification.json": (
        ("registry_sha256", "results/verified_values.csv", "file"),
    ),
    "reports/abstract_quality.json": (
        ("source_sha256", "paper/sections/abstract.tex", "file"),
    ),
    "reports/manuscript_quality.json": (
        ("manuscript_source_sha256", "paper", "paper_source"),
        ("figure_manifest_sha256", "reports/figure_manifest.csv", "file"),
    ),
    "reports/bibliography_verification.json": (
        ("bibliography_sha256", "reports/bibliography.csv", "file"),
    ),
    "reports/latex_compatibility.json": (
        ("source_sha256", "paper", "paper_source"),
    ),
    "reports/paper_depth.json": (
        ("paper_depth_plan_sha256", "reports/paper_depth_plan.csv", "file"),
    ),
    "reports/delivery_profiles.json": (
        ("delivery_manifest_sha256", "delivery/manifest.csv", "file"),
        (
            "official_manifest_sha256",
            "official-submission/manifest.csv",
            "file",
        ),
    ),
    "reports/paper_delivery.json": (
        ("paper_source_sha256", "paper", "paper_source"),
        ("bibliography_sha256", "reports/bibliography.csv", "file"),
        ("support_archive_sha256", "support.zip", "file"),
    ),
    "reports/reproduction_report.json": (
        (
            "reproduction_commands_sha256",
            "support/reproduction_commands.txt",
            "file",
        ),
    ),
}


def safe_file(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    path.relative_to(root)
    return path


def same_file(left: Path, right: Path) -> bool:
    if left == right:
        return True
    try:
        return left.exists() and right.exists() and left.samefile(right)
    except OSError:
        return False


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tree_fingerprint(root: Path, report_path: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(root.rglob("*")):
        if not item.is_file() or ".git" in item.relative_to(root).parts:
            continue
        relative = item.relative_to(root).as_posix()
        if item.resolve() == report_path.resolve() or (
            relative.startswith("reports/phase_") and relative.endswith(".json")
        ):
            continue
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        with item.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        digest.update(b"\0")
    return digest.hexdigest()


def report_status(root: Path, relative: str, path: Path) -> tuple[str, str]:
    if path.suffix.lower() != ".json":
        try:
            lines = path.read_text(
                encoding="utf-8-sig", errors="replace"
            ).splitlines()
            first_line = lines[0]
        except (OSError, UnicodeError, IndexError) as exc:
            return "FAIL", f"cannot read text report: {exc}"
        match = re.fullmatch(r"STATUS\s+(PASS|LIMITED|FAIL)", first_line.strip())
        if match is None:
            return "FAIL", "text report must start with STATUS PASS, LIMITED, or FAIL"
        if relative == "reports/anonymity_scan.txt":
            values = {
                key: value
                for line in lines
                if " " in line
                for key, value in [line.split(" ", 1)]
                if key
                in {
                    "ROOT",
                    "INPUT_FINGERPRINT",
                    "SCANNER",
                    "FILES_SCANNED",
                    "OCR_REQUESTED",
                    "PATTERNS_SHA256",
                }
            }
            scan_root = Path(values.get("ROOT", "")).resolve()
            try:
                scan_root.relative_to(root)
            except ValueError:
                return "FAIL", "anonymity scan root must stay inside the project"
            if (
                not scan_root.is_dir()
                or values.get("INPUT_FINGERPRINT")
                != tree_fingerprint(scan_root, path)
            ):
                return "FAIL", "anonymity report is stale or lacks an input fingerprint"
            if (
                values.get("SCANNER") != "anonymity_scan.py/v2"
                or not str(values.get("FILES_SCANNED") or "").isdigit()
                or int(values["FILES_SCANNED"]) < 1
                or values.get("OCR_REQUESTED") not in {"true", "false"}
                or not re.fullmatch(
                    r"[0-9a-f]{64}", str(values.get("PATTERNS_SHA256") or "")
                )
                or not any(line.startswith("SCOPE ") for line in lines)
                or not any(line.startswith("NOTE ") for line in lines)
            ):
                return "FAIL", "anonymity report lacks specialist scan evidence"
        return match.group(1), ""
    try:
        payload: Any = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return "FAIL", f"cannot read JSON report: {exc}"
    if not isinstance(payload, dict):
        return "FAIL", "JSON report must be an object"
    status = str(payload.get("status") or "").upper()
    if status not in {"PASS", "LIMITED", "FAIL"}:
        return "FAIL", f"invalid or missing report status: {status or '<empty>'}"
    reported_errors = payload.get("errors")
    if not isinstance(reported_errors, list):
        return "FAIL", "JSON report must contain an errors list"
    if status == "PASS" and reported_errors:
        return "FAIL", "PASS report contains recorded errors"
    for field, source_relative, kind in REPORT_BINDINGS.get(relative, ()):
        source = safe_file(root, source_relative)
        if kind == "paper_source":
            expected = source_fingerprint(source) if source.is_dir() else ""
        else:
            expected = sha256_file(source) if source.is_file() else ""
        actual = str(payload.get(field) or "").strip().lower()
        if not expected:
            return "FAIL", f"cannot verify report binding source: {source_relative}"
        if actual != expected.lower():
            return "FAIL", (
                f"stale or unbound report: {field} does not match {source_relative}"
            )
    if relative == "reports/rules_lock_verification.json":
        try:
            lock = json.loads((root / "rules.lock.json").read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            return "FAIL", f"cannot read bound rules lock: {exc}"
        for field in ("profile", "valid_through"):
            if str(payload.get(field) or "") != str(lock.get(field) or ""):
                return "FAIL", f"stale rules report: {field} does not match rules lock"
        for index, source_record in enumerate(lock.get("sources") or [], 1):
            if not isinstance(source_record, dict):
                return "FAIL", f"rules lock source {index} is not an object"
            snapshot = safe_file(root, str(source_record.get("snapshot") or ""))
            expected = str(source_record.get("sha256") or "").lower()
            if not snapshot.is_file() or sha256_file(snapshot) != expected:
                return "FAIL", f"rules lock source {index} snapshot is stale or missing"
    if relative == "reports/submission_manifest.json":
        artifacts = payload.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            return "FAIL", "submission report has no bound artifacts"
        if (
            not isinstance(payload.get("checks"), list)
            or not payload["checks"]
            or not isinstance(payload.get("profile_snapshot"), dict)
            or not payload["profile_snapshot"]
        ):
            return "FAIL", "submission report lacks profile and specialist checks"
        manifest_path = root / "official-submission" / "manifest.csv"
        try:
            with manifest_path.open(encoding="utf-8-sig", newline="") as handle:
                manifest_rows = list(csv.DictReader(handle))
        except (OSError, UnicodeError, csv.Error) as exc:
            return "FAIL", f"cannot read official submission manifest: {exc}"
        expected_files: dict[Path, str] = {}
        for index, row in enumerate(manifest_rows, 2):
            target = safe_file(
                root / "official-submission", str(row.get("path") or "")
            )
            expected_hash = str(row.get("sha256") or "").strip().lower()
            if not target.is_file() or sha256_file(target) != expected_hash:
                return "FAIL", f"official submission manifest row {index} is stale"
            expected_files[target] = expected_hash
        bound_files: dict[Path, str] = {}
        for index, artifact in enumerate(artifacts, 1):
            if not isinstance(artifact, dict):
                return "FAIL", f"submission artifact {index} is not an object"
            source = Path(str(artifact.get("source_path") or "")).resolve()
            try:
                source.relative_to(root)
            except ValueError:
                return "FAIL", f"submission artifact {index} is outside the project"
            if (
                not source.is_file()
                or sha256_file(source)
                != str(artifact.get("sha256") or "").strip().lower()
            ):
                return "FAIL", f"submission artifact {index} is stale or missing"
            bound_files[source] = str(artifact.get("sha256") or "").strip().lower()
        if bound_files != expected_files:
            return "FAIL", "submission report is not bound to official-submission/"
    if relative == "reports/reproduction_report.json":
        input_files = payload.get("input_files")
        runs = payload.get("runs")
        if (
            not payload.get("created_at_utc")
            or not payload.get("command")
            or not payload.get("command_source")
            or not isinstance(input_files, list)
            or not input_files
            or not isinstance(runs, list)
            or not runs
            or not isinstance(payload.get("comparisons"), list)
        ):
            return "FAIL", "reproduction report lacks specialist execution evidence"
        for index, item in enumerate(input_files, 1):
            if not isinstance(item, dict):
                return "FAIL", f"reproduction input {index} is not an object"
            source = safe_file(root, str(item.get("file") or ""))
            if (
                not source.is_file()
                or sha256_file(source)
                != str(item.get("sha256") or "").strip().lower()
            ):
                return "FAIL", f"reproduction input {index} is stale or missing"
        for index, run in enumerate(runs, 1):
            if (
                not isinstance(run, dict)
                or run.get("returncode") != 0
                or run.get("clean_copy") is not True
                or run.get("errors") != []
                or not isinstance(run.get("expected_outputs"), list)
                or not run.get("expected_outputs")
            ):
                return "FAIL", f"reproduction run {index} lacks successful clean-copy evidence"
    return status, ""


def csv_status(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
            fields = set(reader.fieldnames or [])
    except (OSError, UnicodeError, csv.Error) as exc:
        return [f"cannot read CSV ledger: {exc}"]
    if not rows:
        return ["CSV ledger has no evidence rows"]
    if "status" not in fields:
        return ["CSV ledger has no status column"]
    for line, row in enumerate(rows, 2):
        if str(row.get("status") or "").strip().lower() not in COMPLETE:
            errors.append(f"row {line} is not complete")
    return errors


def check_phase(root: Path, phase: str) -> dict[str, Any]:
    target_index = PHASE_ORDER.index(phase)
    checks: list[dict[str, str]] = []
    errors: list[str] = []
    warnings: list[str] = []
    for current in PHASE_ORDER[: target_index + 1]:
        for relative in FILES.get(current, ()):
            path = safe_file(root, relative)
            passed = path.is_file() and path.stat().st_size > 0
            checks.append(
                {
                    "phase": current,
                    "kind": "file",
                    "path": relative,
                    "status": "PASS" if passed else "FAIL",
                }
            )
            if not passed:
                errors.append(f"{current}: missing or empty file: {relative}")
        for relative in REPORTS.get(current, ()):
            path = safe_file(root, relative)
            if not path.is_file():
                status, detail = "FAIL", "report is missing"
            else:
                status, detail = report_status(root, relative, path)
            checks.append(
                {
                    "phase": current,
                    "kind": "report",
                    "path": relative,
                    "status": status,
                    "detail": detail,
                }
            )
            if status == "FAIL":
                errors.append(f"{current}: {relative}: {detail or 'reported FAIL'}")
            elif status == "LIMITED":
                warnings.append(f"{current}: {relative} is LIMITED")
        for relative in CSV_LEDGERS.get(current, ()):
            path = safe_file(root, relative)
            ledger_errors = csv_status(path) if path.is_file() else []
            checks.append(
                {
                    "phase": current,
                    "kind": "ledger",
                    "path": relative,
                    "status": "PASS" if not ledger_errors else "FAIL",
                    "detail": "; ".join(ledger_errors),
                }
            )
            errors.extend(f"{current}: {relative}: {item}" for item in ledger_errors)
    status = "FAIL" if errors else ("LIMITED" if warnings else "PASS")
    return {
        "status": status,
        "phase": phase,
        "scope": (
            "phase artifact and specialist-report coordination only; specialist "
            "reports remain authoritative and mathematical truth is not certified"
        ),
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check")
    check.add_argument("--project-dir", type=Path, required=True)
    check.add_argument("--phase", choices=PHASE_ORDER, required=True)
    check.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.project_dir.resolve()
    payload = check_phase(root, args.phase)
    out = (args.out if args.out.is_absolute() else root / args.out).resolve()
    try:
        out.relative_to(root / "reports")
    except ValueError as exc:
        raise SystemExit("phase report output must stay inside project reports/") from exc
    protected = {
        safe_file(root, relative)
        for group in (FILES, REPORTS, CSV_LEDGERS)
        for values in group.values()
        for relative in values
    }
    if any(same_file(out, item) for item in protected):
        raise SystemExit("phase report output must not overwrite a required artifact")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(payload["status"])
    return {"PASS": 0, "FAIL": 1, "LIMITED": 2}[payload["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
