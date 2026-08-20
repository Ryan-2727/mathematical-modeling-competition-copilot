#!/usr/bin/env python3
"""Coordinate phase gates without replacing specialist verifiers."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

from contest_orchestration import (
    doctor_project,
    migrate_project,
    run_workflow,
    summarize_run,
)
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
        "reports/parameter_registry.csv",
        "reports/independent_routes.csv",
        "reports/result_reconciliation.csv",
        "reports/joint_inference_design.json",
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
        "reports/numeric_exemptions.csv",
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
        "reports/summary_numeric_traceability.json",
    ),
    "delivery": (
        "reports/delivery_profiles.json",
        "reports/paper_delivery.json",
    ),
    "freeze": (
        "reports/reproduction_report.json",
        "reports/anonymity_scan.txt",
        "reports/submission_manifest.json",
        "reports/evidence_chain_verification.json",
        "reports/decision_quality.json",
        "reports/figure_narrative_verification.json",
        "reports/page_readability_verification.json",
        "reports/modeling_argument_quality.json",
        "reports/model_reasoning_core.json",
        "reports/answer_density.json",
        "reports/visual_design_system.json",
        "reports/paper_presentation.json",
        "reports/abstract_structure.json",
        "reports/chinese_academic_style.json",
        "reports/result_story.json",
        "reports/decision_stability.json",
        "reports/figure_numeric_contract.json",
        "reports/model_budget.json",
        "reports/model_kernel_evidence.json",
        "reports/compute_budget_verification.json",
        "reports/three_minute_review.json",
        "reports/latex_dependency_lock.json",
    ),
}
CSV_LEDGERS = {
    "modeling": (
        "reports/model_decision_log.csv",
        "reports/parameter_registry.csv",
        "reports/independent_routes.csv",
        "reports/result_reconciliation.csv",
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
    "reports/model_reasoning_core.json": (
        ("model_decision_log_sha256", "reports/model_decision_log.csv", "file"),
        ("parameter_registry_sha256", "reports/parameter_registry.csv", "file"),
        ("independent_routes_sha256", "reports/independent_routes.csv", "file"),
        ("result_reconciliation_sha256", "reports/result_reconciliation.csv", "file"),
        ("joint_inference_design_sha256", "reports/joint_inference_design.json", "file"),
        ("verified_values_sha256", "results/verified_values.csv", "file"),
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
    "reports/answer_density.json": (
        ("abstract_sha256", "paper/sections/abstract.tex", "file"),
        ("conclusion_sha256", "paper/sections/conclusion.tex", "file"),
        ("conclusion_map_sha256", "reports/conclusion_map.csv", "file"),
    ),
    "reports/summary_numeric_traceability.json": (
        ("abstract_sha256", "paper/sections/abstract.tex", "file"),
        ("conclusion_sha256", "paper/sections/conclusion.tex", "file"),
        ("registry_sha256", "results/verified_values.csv", "file"),
        ("exemptions_sha256", "reports/numeric_exemptions.csv", "file"),
    ),
    "reports/visual_design_system.json": (
        ("figure_manifest_sha256", "reports/figure_manifest.csv", "file"),
        ("table_manifest_sha256", "reports/table_manifest.csv", "file"),
    ),
    "reports/paper_presentation.json": (
        ("paper_sha256", "paper/main.pdf", "file"),
        ("checklist_sha256", "reports/presentation_checklist.csv", "file"),
    ),
    "reports/abstract_structure.json": (
        ("source_sha256", "paper/sections/abstract.tex", "file"),
    ),
    "reports/chinese_academic_style.json": (
        ("paper_source_sha256", "paper", "paper_source"),
    ),
    "reports/result_story.json": (
        ("conclusion_map_sha256", "reports/conclusion_map.csv", "file"),
        ("verified_values_sha256", "results/verified_values.csv", "file"),
        ("simplification_log_sha256", "reports/model_simplification_log.csv", "file"),
        ("visual_storyboard_sha256", "reports/visual_storyboard.csv", "file"),
    ),
    "reports/decision_stability.json": (
        ("decision_stability_sha256", "reports/decision_stability.csv", "file"),
        ("conclusion_map_sha256", "reports/conclusion_map.csv", "file"),
    ),
    "reports/figure_numeric_contract.json": (
        ("contract_sha256", "reports/figure_numeric_contract.csv", "file"),
        ("figure_manifest_sha256", "reports/figure_manifest.csv", "file"),
        ("verified_values_sha256", "results/verified_values.csv", "file"),
    ),
    "reports/model_budget.json": (
        ("model_budget_sha256", "reports/model_budget.csv", "file"),
    ),
    "reports/model_kernel_evidence.json": (
        ("model_kernel_usage_sha256", "reports/model_kernel_usage.csv", "file"),
    ),
    "reports/compute_budget_verification.json": (
        ("compute_budget_sha256", "reports/compute_budget.csv", "file"),
        ("compute_runs_sha256", "reports/compute_runs.jsonl", "file"),
    ),
    "reports/three_minute_review.json": (
        ("review_sha256", "reports/three_minute_review.csv", "file"),
        ("figure_manifest_sha256", "reports/figure_manifest.csv", "file"),
        ("verified_values_sha256", "results/verified_values.csv", "file"),
        ("conclusion_map_sha256", "reports/conclusion_map.csv", "file"),
    ),
    "reports/latex_dependency_lock.json": (
        ("source_sha256", "paper", "paper_source"),
        ("latexmkrc_sha256", "paper/.latexmkrc", "file"),
        ("vscode_settings_sha256", "paper/.vscode/settings.json", "file"),
        ("vscode_extensions_sha256", "paper/.vscode/extensions.json", "file"),
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


def is_within_root(root: Path, path: Path) -> bool:
    """Compare resolved paths with Windows' case-insensitive semantics."""
    root_text = os.path.normcase(str(root))
    path_text = os.path.normcase(str(path))
    try:
        return os.path.commonpath((root_text, path_text)) == root_text
    except ValueError:
        return False


def safe_file(root: Path, relative: str) -> Path:
    resolved_root = root.resolve()
    path = (resolved_root / relative).resolve()
    if not is_within_root(resolved_root, path):
        raise ValueError(f"{path!r} is not inside project root {resolved_root!r}")
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


def report_output(root: Path, value: Path, default: str) -> Path:
    out = value if value else Path(default)
    out = (out if out.is_absolute() else root / out).resolve()
    try:
        out.relative_to(root / "reports")
    except ValueError as exc:
        raise SystemExit("command output must stay inside project reports/") from exc
    return out


def write_payload(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def selected_profile(root: Path, requested: str | None) -> str:
    if requested:
        return requested
    try:
        manifest = json.loads(
            (root / "contest_manifest.json").read_text(encoding="utf-8-sig")
        )
    except (OSError, UnicodeError, json.JSONDecodeError):
        return "standard"
    value = str(manifest.get("quality_profile") or "standard")
    return value if value in {"minimal", "standard", "strict"} else "standard"


def command_check(args: argparse.Namespace) -> int:
    root = args.project_dir.resolve()
    payload = check_phase(root, args.phase)
    out = report_output(root, args.out, f"reports/phase_{args.phase}.json")
    protected = {
        safe_file(root, relative)
        for group in (FILES, REPORTS, CSV_LEDGERS)
        for values in group.values()
        for relative in values
    }
    if any(same_file(out, item) for item in protected):
        raise SystemExit("phase report output must not overwrite a required artifact")
    write_payload(out, payload)
    print(payload["status"])
    return {"PASS": 0, "FAIL": 1, "LIMITED": 2}[payload["status"]]


def command_doctor(args: argparse.Namespace) -> int:
    root = args.project_dir.resolve()
    profile = selected_profile(root, args.profile)
    payload = doctor_project(root, profile)
    write_payload(
        report_output(root, args.out, "reports/contestctl_doctor.json"), payload
    )
    print(payload["status"])
    return {"PASS": 0, "FAIL": 1, "LIMITED": 2}[payload["status"]]


def command_migrate(args: argparse.Namespace) -> int:
    root = args.project_dir.resolve()
    payload = migrate_project(
        root,
        args.apply,
        report_output(root, args.out, "reports/project_migration.json"),
    )
    print(payload["status"])
    return 0 if payload["status"] == "PASS" else 1


def command_run(args: argparse.Namespace) -> int:
    root = args.project_dir.resolve()
    profile = selected_profile(root, args.profile)
    custom = args.profile_file.resolve() if args.profile_file else None
    try:
        payload = run_workflow(
            root,
            args.phase,
            profile,
            custom,
            force=args.force,
            dry_run=args.dry_run,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        payload = {
            "status": "FAIL",
            "phase": args.phase,
            "profile": profile,
            "nodes": [],
            "errors": [str(exc)],
            "warnings": [],
        }
    if profile == "strict" and not args.dry_run:
        coordination = check_phase(root, args.phase)
        payload["nodes"].append(
            {
                "node": f"coordinate-{args.phase}",
                "phase": args.phase,
                "status": coordination["status"],
                "reason": "existing phase artifact and report coordination",
                "returncode": {
                    "PASS": 0,
                    "FAIL": 1,
                    "LIMITED": 2,
                }[coordination["status"]],
                "output_hashes": {},
            }
        )
        payload["errors"].extend(coordination["errors"])
        payload["warnings"].extend(coordination["warnings"])
        if coordination["status"] == "FAIL":
            payload["status"] = "FAIL"
        elif coordination["status"] == "LIMITED" and payload["status"] == "PASS":
            payload["status"] = "LIMITED"
    out = report_output(
        root, args.out, f"reports/workflow_{args.phase}.json"
    )
    write_payload(out, payload)
    print(payload["status"])
    return {"PASS": 0, "FAIL": 1, "LIMITED": 2}[payload["status"]]


def command_summary(args: argparse.Namespace) -> int:
    root = args.project_dir.resolve()
    if args.run_report:
        report = (
            args.run_report
            if args.run_report.is_absolute()
            else root / args.run_report
        ).resolve()
    else:
        candidates = [
            root / "reports" / "workflow_freeze.json",
            root / "reports" / "workflow_paper.json",
        ]
        report = next((item for item in candidates if item.is_file()), candidates[0])
    try:
        payload = json.loads(report.read_text(encoding="utf-8-sig"))
        if not isinstance(payload, dict):
            raise ValueError("workflow report must be a JSON object")
        summary = summarize_run(payload)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        summary = {
            "status": "FAIL",
            "phase": None,
            "profile": None,
            "counts": {},
            "errors": [str(exc)],
            "warnings": [],
        }
    if args.out:
        write_payload(report_output(root, args.out, "reports/workflow_summary.json"), summary)
    if args.format == "json":
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        counts = " ".join(
            f"{key}={value}" for key, value in summary.get("counts", {}).items()
        )
        print(
            f"{summary['status']} phase={summary.get('phase') or '-'} "
            f"profile={summary.get('profile') or '-'} {counts}".rstrip()
        )
        for item in summary.get("errors", []):
            print(f"ERROR {item}")
        for item in summary.get("warnings", []):
            print(f"WARNING {item}")
    return {"PASS": 0, "FAIL": 1, "LIMITED": 2}.get(summary["status"], 1)


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check")
    check.add_argument("--project-dir", type=Path, required=True)
    check.add_argument("--phase", choices=PHASE_ORDER, required=True)
    check.add_argument("--out", type=Path, required=True)
    check.set_defaults(handler=command_check)
    doctor = subparsers.add_parser("doctor")
    doctor.add_argument("--project-dir", type=Path, required=True)
    doctor.add_argument(
        "--profile",
        choices=["minimal", "standard", "strict"],
    )
    doctor.add_argument("--out", type=Path)
    doctor.set_defaults(handler=command_doctor)
    migrate = subparsers.add_parser("migrate")
    migrate.add_argument("--project-dir", type=Path, required=True)
    migrate.add_argument("--apply", action="store_true")
    migrate.add_argument("--out", type=Path)
    migrate.set_defaults(handler=command_migrate)
    run = subparsers.add_parser("run")
    run.add_argument("--project-dir", type=Path, required=True)
    run.add_argument("--phase", choices=["paper", "freeze"], required=True)
    run.add_argument(
        "--profile",
        choices=["minimal", "standard", "strict", "custom"],
    )
    run.add_argument("--profile-file", type=Path)
    run.add_argument("--force", action="store_true")
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("--out", type=Path)
    run.set_defaults(handler=command_run)
    summary = subparsers.add_parser("summary")
    summary.add_argument("--project-dir", type=Path, required=True)
    summary.add_argument("--run-report", type=Path)
    summary.add_argument("--format", choices=["human", "json"], default="human")
    summary.add_argument("--out", type=Path)
    summary.set_defaults(handler=command_summary)
    args = parser.parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
