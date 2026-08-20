#!/usr/bin/env python3
"""Versioned project migration and deterministic contest workflow orchestration."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CURRENT_PROJECT_SCHEMA_VERSION = 2
REGISTRY_VERSION = 3
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
PROFILE_DIR = SKILL_ROOT / "assets" / "contestctl" / "profiles"
VALID_STATUSES = {"PASS", "FAIL", "LIMITED", "SKIPPED"}


@dataclass(frozen=True)
class Node:
    node_id: str
    phase: str
    script: str
    argv: tuple[str, ...]
    dependencies: tuple[str, ...]
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]


NODE_REGISTRY = {
    node.node_id: node
    for node in (
        Node(
            "generate-paper-artifacts",
            "paper",
            "generate_paper_artifacts.py",
            ("--project-dir", "{project}"),
            (),
            (
                "results/verified_values.csv",
                "results/**/*",
                "reports/conclusion_map.csv",
                "reports/model_decision_log.csv",
                "reports/parameter_registry.csv",
                "reports/independent_routes.csv",
                "reports/result_reconciliation.csv",
                "reports/stress_tests.csv",
                "reports/figure_manifest.csv",
            ),
            ("reports/paper_artifacts_manifest.json",),
        ),
        Node(
            "verify-notation",
            "paper",
            "verify_notation_registry.py",
            ("--project-dir", "{project}"),
            ("generate-paper-artifacts",),
            (
                "reports/notation_registry.csv",
                "paper/**/*.tex",
                "results/verified_values.csv",
            ),
            ("reports/notation_verification.json",),
        ),
        Node(
            "verify-rendered-figures",
            "paper",
            "verify_rendered_figures.py",
            ("--project-dir", "{project}", "--profile", "{profile}"),
            (),
            ("reports/rendered_figure_manifest.csv", "figures/**/*", "paper/figures/**/*"),
            ("reports/rendered_figure_verification.json",),
        ),
        Node(
            "verify-abstract-structure",
            "paper",
            "verify_abstract_structure.py",
            ("--project-dir", "{project}"),
            (),
            ("paper/sections/abstract.tex",),
            ("reports/abstract_structure.json",),
        ),
        Node(
            "verify-chinese-style",
            "paper",
            "verify_chinese_academic_style.py",
            (
                "--project-dir",
                "{project}",
                "--out",
                "{project}/reports/chinese_academic_style.json",
            ),
            (),
            (
                "contest_manifest.json",
                "paper/**/*.tex",
                "reports/prose_style_exemptions.csv",
            ),
            ("reports/chinese_academic_style.json",),
        ),
        Node(
            "verify-answer-density",
            "paper",
            "verify_answer_density.py",
            ("--project-dir", "{project}"),
            (),
            (
                "paper/sections/abstract.tex",
                "paper/sections/conclusion.tex",
                "reports/conclusion_map.csv",
            ),
            ("reports/answer_density.json",),
        ),
        Node(
            "verify-summary-numbers",
            "paper",
            "verify_summary_numeric_traceability.py",
            ("--project-dir", "{project}"),
            ("generate-paper-artifacts",),
            (
                "paper/sections/abstract.tex",
                "paper/sections/conclusion.tex",
                "results/verified_values.csv",
                "reports/numeric_exemptions.csv",
            ),
            ("reports/summary_numeric_traceability.json",),
        ),
        Node(
            "verify-result-story",
            "paper",
            "verify_result_story.py",
            ("--project-dir", "{project}"),
            ("generate-paper-artifacts",),
            (
                "reports/conclusion_map.csv",
                "results/verified_values.csv",
                "reports/model_simplification_log.csv",
                "reports/visual_storyboard.csv",
            ),
            ("reports/result_story.json",),
        ),
        Node(
            "verify-visual-design",
            "paper",
            "verify_visual_design_system.py",
            ("--project-dir", "{project}"),
            ("verify-rendered-figures",),
            ("reports/figure_manifest.csv", "reports/table_manifest.csv"),
            ("reports/visual_design_system.json",),
        ),
        Node(
            "verify-figure-narrative",
            "paper",
            "verify_figure_narrative.py",
            ("--project-dir", "{project}"),
            ("verify-rendered-figures",),
            ("reports/figure_manifest.csv",),
            ("reports/figure_narrative_verification.json",),
        ),
        Node(
            "verify-latex-compatibility",
            "paper",
            "verify_latex_compatibility.py",
            (
                "--paper-dir",
                "{project}/paper",
                "--out",
                "{project}/reports/latex_compatibility.json",
            ),
            ("generate-paper-artifacts",),
            ("paper/**/*.tex", "paper/.latexmkrc", "paper/.vscode/*.json"),
            ("reports/latex_compatibility.json",),
        ),
        Node(
            "verify-bibliography",
            "paper",
            "verify_bibliography_metadata.py",
            (
                "--project-dir",
                "{project}",
                "--out",
                "{project}/reports/bibliography_verification.json",
            ),
            (),
            (
                "paper/references.bib",
                "reports/bibliography.csv",
                "reports/bibliography_metadata/**/*",
                "reports/source_passages/**/*",
            ),
            ("reports/bibliography_verification.json",),
        ),
        Node(
            "verify-manuscript",
            "paper",
            "verify_manuscript_quality.py",
            (
                "--project-dir",
                "{project}",
                "--fail-on-overfull",
                "--out",
                "{project}/reports/manuscript_quality.json",
            ),
            ("verify-rendered-figures", "generate-paper-artifacts"),
            ("paper/**/*", "reports/figure_manifest.csv"),
            ("reports/manuscript_quality.json",),
        ),
        Node(
            "verify-decision-stability",
            "freeze",
            "verify_decision_stability.py",
            ("--project-dir", "{project}"),
            (),
            ("reports/decision_stability.csv", "reports/conclusion_map.csv"),
            ("reports/decision_stability.json",),
        ),
        Node(
            "verify-figure-contract",
            "freeze",
            "verify_figure_numeric_contract.py",
            ("--project-dir", "{project}"),
            ("verify-rendered-figures",),
            (
                "reports/figure_numeric_contract.csv",
                "reports/figure_manifest.csv",
                "results/verified_values.csv",
            ),
            ("reports/figure_numeric_contract.json",),
        ),
        Node(
            "verify-model-budget",
            "freeze",
            "verify_model_budget.py",
            ("--project-dir", "{project}"),
            (),
            ("reports/model_budget.csv",),
            ("reports/model_budget.json",),
        ),
        Node(
            "verify-model-kernel-evidence",
            "freeze",
            "verify_model_kernel_evidence.py",
            (
                "--project-dir",
                "{project}",
                "--out",
                "{project}/reports/model_kernel_evidence.json",
            ),
            (),
            (
                "reports/model_kernel_usage.csv",
                "code/**/*",
                "results/**/*",
                "reports/*kernel*regression*.json",
            ),
            ("reports/model_kernel_evidence.json",),
        ),
        Node(
            "verify-compute-budget",
            "freeze",
            "verify_compute_budget.py",
            (
                "--project-dir",
                "{project}",
                "--out",
                "{project}/reports/compute_budget_verification.json",
            ),
            ("verify-model-kernel-evidence",),
            (
                "reports/compute_budget.csv",
                "reports/compute_runs.jsonl",
                "results/**/*",
            ),
            ("reports/compute_budget_verification.json",),
        ),
        Node(
            "verify-three-minute-review",
            "freeze",
            "verify_three_minute_review.py",
            ("--project-dir", "{project}"),
            (
                "verify-abstract-structure",
                "verify-answer-density",
                "verify-rendered-figures",
            ),
            (
                "reports/three_minute_review.csv",
                "reports/figure_manifest.csv",
                "results/verified_values.csv",
                "reports/conclusion_map.csv",
            ),
            ("reports/three_minute_review.json",),
        ),
        Node(
            "verify-latex-lock",
            "freeze",
            "verify_latex_dependency_lock.py",
            ("--project-dir", "{project}"),
            ("verify-latex-compatibility",),
            ("paper/**/*",),
            ("reports/latex_dependency_lock.json",),
        ),
        Node(
            "verify-evidence-chain",
            "freeze",
            "verify_evidence_chain.py",
            ("--project-dir", "{project}"),
            (),
            (
                "reports/evidence_chain.csv",
                "reports/claims.csv",
                "results/verified_values.csv",
            ),
            ("reports/evidence_chain_verification.json",),
        ),
        Node(
            "verify-decision-quality",
            "freeze",
            "verify_decision_quality.py",
            ("--project-dir", "{project}"),
            ("verify-evidence-chain", "verify-decision-stability"),
            (
                "reports/model_decision_log.csv",
                "reports/stress_tests.csv",
                "reports/decision_robustness.csv",
                "reports/implementation_readiness.csv",
                "reports/fallback_plan.csv",
                "reports/causal_claims.csv",
            ),
            ("reports/decision_quality.json",),
        ),
        Node(
            "verify-model-reasoning",
            "freeze",
            "verify_model_reasoning_core.py",
            ("--project-dir", "{project}"),
            (),
            (
                "reports/model_decision_log.csv",
                "reports/parameter_registry.csv",
                "reports/independent_routes.csv",
                "reports/result_reconciliation.csv",
                "reports/joint_inference_design.json",
                "results/verified_values.csv",
            ),
            ("reports/model_reasoning_core.json",),
        ),
        Node(
            "verify-modeling-argument",
            "freeze",
            "verify_modeling_argument_quality.py",
            ("--project-dir", "{project}"),
            ("verify-decision-quality", "verify-model-reasoning"),
            (
                "reports/mechanism_audit.json",
                "reports/semantic_audit.csv",
                "reports/validation_design.csv",
                "reports/conclusion_map.csv",
                "reports/innovation_ledger.csv",
            ),
            ("reports/modeling_argument_quality.json",),
        ),
    )
}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def migration_plan(root: Path) -> dict[str, Any]:
    manifest_path = root / "contest_manifest.json"
    if not manifest_path.is_file():
        return {
            "status": "FAIL",
            "errors": ["contest_manifest.json is missing"],
            "changes": [],
        }
    try:
        manifest = _load_json(manifest_path)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        return {"status": "FAIL", "errors": [str(exc)], "changes": []}
    raw_version = manifest.get("project_schema_version", 0)
    if not isinstance(raw_version, int) or raw_version < 0:
        return {
            "status": "FAIL",
            "errors": ["project_schema_version must be a non-negative integer"],
            "changes": [],
        }
    if raw_version > CURRENT_PROJECT_SCHEMA_VERSION:
        return {
            "status": "FAIL",
            "errors": [
                f"project schema {raw_version} is newer than supported "
                f"{CURRENT_PROJECT_SCHEMA_VERSION}"
            ],
            "changes": [],
        }
    additions: tuple[tuple[str, Any], ...] = (
        ("/quality_profile", "standard"),
        ("/workflow", {}),
        ("/workflow/phase", "setup"),
        ("/workflow/optional_tool_policy", "limited_when_unavailable"),
        ("/workflow/generated_dir", "paper/generated"),
    )
    candidate = json.loads(json.dumps(manifest))
    changes: list[dict[str, Any]] = []
    required_files = (
        "reports/parameter_registry.csv",
        "reports/independent_routes.csv",
        "reports/result_reconciliation.csv",
        "reports/joint_inference_design.json",
        "reports/model_kernel_usage.csv",
        "reports/compute_budget.csv",
        "reports/compute_runs.jsonl",
        "reports/prose_style_exemptions.csv",
    )
    if raw_version < CURRENT_PROJECT_SCHEMA_VERSION:
        candidate["project_schema_version"] = CURRENT_PROJECT_SCHEMA_VERSION
        changes.append(
            {
                "op": "add" if "project_schema_version" not in manifest else "replace",
                "path": "/project_schema_version",
                "value": CURRENT_PROJECT_SCHEMA_VERSION,
            }
        )
    for pointer, value in additions:
        parts = pointer.strip("/").split("/")
        target = candidate
        for part in parts[:-1]:
            current = target.get(part)
            if current is None:
                target[part] = {}
            elif not isinstance(current, dict):
                return {
                    "status": "FAIL",
                    "errors": [f"{'/'.join(parts[:-1])} must be an object"],
                    "changes": [],
                }
            target = target[part]
        key = parts[-1]
        if key not in target:
            target[key] = value
            changes.append({"op": "add", "path": pointer, "value": value})
    for relative in required_files:
        if not (root / relative).exists():
            changes.append({"op": "create_file", "path": relative})
    return {
        "status": "PASS",
        "errors": [],
        "old_version": raw_version,
        "new_version": CURRENT_PROJECT_SCHEMA_VERSION,
        "changes": changes,
        "manifest": candidate,
    }


def migrate_project(root: Path, apply: bool, out: Path) -> dict[str, Any]:
    payload = migration_plan(root)
    payload["applied"] = False
    if payload["status"] == "PASS" and apply:
        manifest = payload.pop("manifest")
        templates = {
            "reports/parameter_registry.csv": "subproblem,model_id,parameter,symbol,role,unit,scope,source,bounds,identifiability_status,claim_boundary,status\n",
            "reports/independent_routes.csv": "subproblem,route_id,route_role,principle,data_representation,failure_mode,result_file,result_value,tolerance,comparison_status,limitation,status\n",
            "reports/result_reconciliation.csv": "subproblem,comparison_id,primary_route,comparison_route,primary_value,comparison_value,tolerance,disagreement_material,investigation_step,cause,resolution,claim_action,evidence_file,status\n",
            "reports/joint_inference_design.json": '{\n  "applicable": false,\n  "reason": "migration requires an applicability decision",\n  "subproblems": []\n}\n',
            "reports/model_kernel_usage.csv": "model_id,card_id,kernel_id,used,backend,input_file,input_sha256,output_file,output_sha256,synthetic_regression_report,synthetic_regression_sha256,adaptation_note,status\n",
            "reports/compute_budget.csv": "model_id,selected,primary_run_ids,fallback_run_id,required_scale_count,single_scale_reason,remaining_time_seconds,solver_gap_required,status\n",
            "reports/compute_runs.jsonl": "",
            "reports/prose_style_exemptions.csv": "finding_sha256,rule,source_file,line,reason,reviewer,status\n",
        }
        created: list[str] = []
        for relative, content in templates.items():
            target = root / relative
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
                created.append(relative)
        _write_json(root / "contest_manifest.json", manifest)
        payload["created_files"] = created
        payload["applied"] = True
    else:
        payload.pop("manifest", None)
    _write_json(out, payload)
    return payload


def validate_registry() -> None:
    outputs: dict[str, str] = {}
    for node_id, node in NODE_REGISTRY.items():
        if node.phase not in {"paper", "freeze"}:
            raise ValueError(f"workflow node {node_id!r} has an invalid phase")
        if not (SCRIPT_DIR / node.script).is_file():
            raise ValueError(f"workflow node {node_id!r} script is missing")
        for dependency in node.dependencies:
            if dependency not in NODE_REGISTRY:
                raise ValueError(
                    f"workflow node {node_id!r} has unknown dependency {dependency!r}"
                )
        for output in node.outputs:
            owner = outputs.setdefault(output, node_id)
            if owner != node_id:
                raise ValueError(
                    f"workflow output {output!r} is declared by {owner!r} and {node_id!r}"
                )
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node_id: str) -> None:
        if node_id in visited:
            return
        if node_id in visiting:
            raise ValueError(f"workflow dependency cycle includes {node_id!r}")
        visiting.add(node_id)
        for dependency in NODE_REGISTRY[node_id].dependencies:
            visit(dependency)
        visiting.remove(node_id)
        visited.add(node_id)

    for node_id in NODE_REGISTRY:
        visit(node_id)


def load_profile(name: str, custom_path: Path | None = None) -> dict[str, Any]:
    validate_registry()
    if name == "custom":
        if custom_path is None:
            raise ValueError("custom profile requires --profile-file")
        path = custom_path
    else:
        if custom_path is not None:
            raise ValueError("--profile-file is only valid with --profile custom")
        path = PROFILE_DIR / f"{name}.json"
    payload = _load_json(path)
    if payload.get("name") != name:
        raise ValueError(f"profile name must be {name!r}")
    phases = payload.get("phases")
    if not isinstance(phases, dict):
        raise ValueError("profile phases must be an object")
    for phase, nodes in phases.items():
        if phase not in {"paper", "freeze"} or not isinstance(nodes, list):
            raise ValueError(f"invalid profile phase {phase!r}")
        for node_id in nodes:
            if node_id not in NODE_REGISTRY:
                raise ValueError(f"unknown workflow node {node_id!r}")
            if NODE_REGISTRY[node_id].phase != phase:
                raise ValueError(
                    f"workflow node {node_id!r} belongs to "
                    f"{NODE_REGISTRY[node_id].phase!r}, not {phase!r}"
                )
    return payload


def resolve_nodes(profile: dict[str, Any], phase: str) -> list[str]:
    selected: set[str] = set()

    def include(node_id: str) -> None:
        if node_id in selected:
            return
        node = NODE_REGISTRY[node_id]
        for dependency in node.dependencies:
            include(dependency)
        selected.add(node_id)

    phases = ("paper",) if phase == "paper" else ("paper", "freeze")
    for current in phases:
        for node_id in profile["phases"].get(current, []):
            include(str(node_id))
    visiting: set[str] = set()
    visited: set[str] = set()
    order: list[str] = []

    def visit(node_id: str) -> None:
        if node_id in visited:
            return
        if node_id in visiting:
            raise ValueError(f"workflow dependency cycle includes {node_id}")
        visiting.add(node_id)
        for dependency in NODE_REGISTRY[node_id].dependencies:
            if dependency in selected:
                visit(dependency)
        visiting.remove(node_id)
        visited.add(node_id)
        order.append(node_id)

    for node_id in sorted(selected):
        visit(node_id)
    return order


def _expanded_inputs(root: Path, patterns: tuple[str, ...]) -> list[Path]:
    paths: set[Path] = set()
    for pattern in patterns:
        matches = list(root.glob(pattern))
        if not matches:
            paths.add(root / pattern)
        else:
            paths.update(item for item in matches if item.is_file())
    return sorted(paths, key=lambda item: item.as_posix())


def _digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def node_signature(
    root: Path,
    node: Node,
    profile_name: str,
    dependency_records: list[dict[str, Any]],
) -> str:
    payload: dict[str, Any] = {
        "registry_version": REGISTRY_VERSION,
        "node": node.node_id,
        "profile": profile_name,
        "argv": node.argv,
        "dependencies": [
            {
                "node": item["node"],
                "status": (
                    "PASS"
                    if item["status"] == "SKIPPED"
                    and item.get("reason") == "unchanged passing inputs and outputs"
                    else item["status"]
                ),
                "output_hashes": item.get("output_hashes", {}),
            }
            for item in dependency_records
        ],
        "inputs": [],
    }
    for path in _expanded_inputs(root, node.inputs):
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError:
            relative = str(path)
        payload["inputs"].append(
            {
                "path": relative,
                "sha256": _digest_file(path) if path.is_file() else None,
            }
        )
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _output_hashes(root: Path, node: Node) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for relative in node.outputs:
        path = root / relative
        if path.is_file():
            hashes[relative] = _digest_file(path)
    return hashes


def _read_cache(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"registry_version": REGISTRY_VERSION, "nodes": {}}
    try:
        payload = _load_json(path)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        return {"registry_version": REGISTRY_VERSION, "nodes": {}}
    if payload.get("registry_version") != REGISTRY_VERSION:
        return {"registry_version": REGISTRY_VERSION, "nodes": {}}
    if not isinstance(payload.get("nodes"), dict):
        payload["nodes"] = {}
    return payload


def _cache_hit(
    root: Path, node: Node, cached: dict[str, Any] | None, signature: str
) -> bool:
    if not isinstance(cached, dict):
        return False
    if cached.get("signature") != signature or cached.get("status") != "PASS":
        return False
    return cached.get("output_hashes") == _output_hashes(root, node) and len(
        cached.get("output_hashes") or {}
    ) == len(node.outputs)


def run_workflow(
    root: Path,
    phase: str,
    profile_name: str,
    custom_profile: Path | None,
    force: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    profile = load_profile(profile_name, custom_profile)
    node_ids = resolve_nodes(profile, phase)
    cache_path = root / "reports" / "workflow_cache.json"
    cache = _read_cache(cache_path)
    records: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    for node_id in node_ids:
        node = NODE_REGISTRY[node_id]
        dependencies = [by_id[item] for item in node.dependencies if item in by_id]
        blocked = [
            item["node"]
            for item in dependencies
            if item["status"] == "FAIL"
            or (
                item["status"] == "SKIPPED"
                and item.get("reason") != "unchanged passing inputs and outputs"
            )
        ]
        if blocked:
            record = {
                "node": node_id,
                "phase": node.phase,
                "status": "SKIPPED",
                "reason": f"failed dependencies: {', '.join(blocked)}",
                "returncode": None,
                "output_hashes": {},
            }
            records.append(record)
            by_id[node_id] = record
            continue
        signature = node_signature(root, node, profile_name, dependencies)
        cached = cache["nodes"].get(node_id)
        if not force and _cache_hit(root, node, cached, signature):
            record = {
                "node": node_id,
                "phase": node.phase,
                "status": "SKIPPED",
                "reason": "unchanged passing inputs and outputs",
                "returncode": None,
                "signature": signature,
                "output_hashes": cached["output_hashes"],
            }
            records.append(record)
            by_id[node_id] = record
            continue
        argv = [
            value.format(project=str(root), profile=profile_name)
            for value in node.argv
        ]
        command = [sys.executable, str(SCRIPT_DIR / node.script), *argv]
        if dry_run:
            status, returncode, stdout, stderr = "SKIPPED", None, "", ""
            reason = "dry run"
        elif not (SCRIPT_DIR / node.script).is_file():
            status, returncode, stdout, stderr = (
                "FAIL",
                1,
                "",
                f"missing script: {node.script}",
            )
            reason = "missing script"
        else:
            completed = subprocess.run(
                command,
                cwd=root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            returncode = completed.returncode
            stdout = completed.stdout[-4000:]
            stderr = completed.stderr[-4000:]
            status = {0: "PASS", 2: "LIMITED"}.get(returncode, "FAIL")
            reason = ""
        output_hashes = _output_hashes(root, node)
        if not dry_run and status in {"PASS", "LIMITED"} and len(output_hashes) != len(
            node.outputs
        ):
            status = "FAIL"
            reason = "command did not create every declared output"
        record = {
            "node": node_id,
            "phase": node.phase,
            "status": status,
            "reason": reason,
            "returncode": returncode,
            "command": command,
            "signature": signature,
            "output_hashes": output_hashes,
            "stdout": stdout,
            "stderr": stderr,
        }
        records.append(record)
        by_id[node_id] = record
        if not dry_run:
            cache["nodes"][node_id] = {
                "signature": signature,
                "status": status,
                "output_hashes": output_hashes,
            }
    if not dry_run:
        _write_json(cache_path, cache)
    failed = [item["node"] for item in records if item["status"] == "FAIL"]
    limited = [item["node"] for item in records if item["status"] == "LIMITED"]
    status = "FAIL" if failed else ("LIMITED" if limited else "PASS")
    return {
        "status": status,
        "phase": phase,
        "profile": profile_name,
        "registry_version": REGISTRY_VERSION,
        "dry_run": dry_run,
        "nodes": records,
        "errors": [f"{item} failed" for item in failed],
        "warnings": [f"{item} is LIMITED" for item in limited],
    }


def doctor_project(root: Path, profile_name: str) -> dict[str, Any]:
    tools = {
        name: shutil.which(name)
        for name in ("latexmk", "xelatex", "pdftoppm", "pdftotext")
    }
    modules = {
        name: importlib.util.find_spec(name) is not None
        for name in ("PIL",)
    }
    plan = migration_plan(root)
    missing = [name for name, path in tools.items() if path is None]
    missing.extend(name for name, present in modules.items() if not present)
    errors: list[str] = []
    warnings: list[str] = []
    try:
        load_profile(profile_name)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        errors.append(f"profile/registry error: {exc}")
    if plan["status"] == "FAIL":
        errors.extend(plan["errors"])
    elif plan["changes"]:
        warnings.append("project schema migration is available")
    if profile_name == "strict" and missing:
        errors.append("strict profile missing optional tools: " + ", ".join(missing))
    elif profile_name != "minimal" and missing:
        warnings.append("optional tools unavailable: " + ", ".join(missing))
    status = "FAIL" if errors else ("LIMITED" if warnings else "PASS")
    return {
        "status": status,
        "profile": profile_name,
        "python": sys.version,
        "project_schema_supported": CURRENT_PROJECT_SCHEMA_VERSION,
        "migration_changes": plan.get("changes", []),
        "tools": tools,
        "python_modules": modules,
        "errors": errors,
        "warnings": warnings,
    }


def summarize_run(payload: dict[str, Any]) -> dict[str, Any]:
    counts = {status: 0 for status in sorted(VALID_STATUSES)}
    for item in payload.get("nodes", []):
        status = str(item.get("status") or "").upper()
        if status in counts:
            counts[status] += 1
    return {
        "status": payload.get("status", "FAIL"),
        "phase": payload.get("phase"),
        "profile": payload.get("profile"),
        "counts": counts,
        "errors": payload.get("errors", []),
        "warnings": payload.get("warnings", []),
    }
