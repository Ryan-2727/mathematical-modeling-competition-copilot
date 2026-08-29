from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_paper_reasoning_narrative.py"
COMPLETE = "verified"

MAP_FIELDS = [
    "subproblem",
    "paper_location",
    "modeling_path",
    "modeling_path_evidence",
    "modeling_path_evidence_sha256",
    "model_choice_required",
    "model_choice_location",
    "parameter_location",
    "failed_route_required",
    "failed_route_location",
    "boundary_required",
    "boundary_location",
    "human_reviewer",
    "status",
]
PARAMETER_FIELDS = [
    "subproblem",
    "model_id",
    "parameter",
    "symbol",
    "role",
    "unit",
    "scope",
    "source",
    "bounds",
    "identifiability_status",
    "claim_boundary",
    "status",
    "claim_sensitive",
    "source_class",
    "source_locator",
    "source_sha256",
    "citation_key",
    "calibration_command",
    "sensitivity_evidence",
    "paper_location",
]
SIMPLIFICATION_FIELDS = [
    "subproblem",
    "primary_route",
    "failure_diagnostic",
    "decision_state",
    "retained_core_factors",
    "removed_noncritical_factors",
    "simplified_route",
    "user_authorization",
    "original_model_treatment",
    "result_file",
    "paper_location",
    "status",
]
FALLBACK_FIELDS = [
    "subproblem",
    "model_family",
    "failure_mode",
    "trigger",
    "primary_route",
    "fallback_route",
    "boundary_statement",
    "result_file",
    "paper_location",
    "status",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class PaperReasoningNarrativeTests(unittest.TestCase):
    def run_audit(self, root: Path, expect: int = 0) -> dict:
        out = root / "reports" / "paper_reasoning_narrative.json"
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--project-dir",
                str(root),
                "--out",
                str(out),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(result.returncode, expect, result.stdout + result.stderr)
        return json.loads(out.read_text(encoding="utf-8"))

    def scaffold(self, root: Path) -> None:
        reports = root / "reports"
        results = root / "results"
        paper = root / "paper" / "sections"
        data = root / "data" / "processed"
        for directory in (reports, results, paper, data):
            directory.mkdir(parents=True, exist_ok=True)

        (paper / "model.tex").write_text(
            "车辆容量与时间窗决定了可行域。线性基线在高需求场景下出现违约，"
            "因此采用经过压力测试的鲁棒模型，比较结果见表~\\ref{tab:model}.\n",
            encoding="utf-8",
        )
        (paper / "conclusion.tex").write_text(
            "当需求扰动保持在测试区间内时，推荐路径保持可行。\n",
            encoding="utf-8",
        )
        trace = reports / "traceability.md"
        trace.write_text("Q1: data -> baseline -> robust model -> result\n", encoding="utf-8")
        comparison = results / "model-comparison.json"
        comparison.write_text('{"baseline": 14.2, "candidate": 11.8}\n', encoding="utf-8")
        calibration = data / "calibration.csv"
        calibration.write_text("radius\n0.15\n", encoding="utf-8")
        sensitivity = results / "sensitivity.json"
        sensitivity.write_text('{"stable": true}\n', encoding="utf-8")

        write_csv(
            reports / "model_decision_log.csv",
            (
                "subproblem,model_level,parent_model,baseline,candidate,added_mechanism,"
                "mechanism_fit,assumptions,new_parameters,expected_diagnostic_signature,"
                "failure_test,validation_cost,identifiability_status,selected,"
                "selection_evidence,status"
            ).split(","),
            [
                {
                    "subproblem": "Q1",
                    "model_level": "C0",
                    "parent_model": "none",
                    "baseline": "linear",
                    "candidate": "linear",
                    "added_mechanism": "none",
                    "mechanism_fit": "reference",
                    "assumptions": "fixed demand",
                    "new_parameters": "none",
                    "expected_diagnostic_signature": "reference",
                    "failure_test": "constraint violation",
                    "validation_cost": "low",
                    "identifiability_status": "PASS",
                    "selected": "false",
                    "selection_evidence": "results/model-comparison.json",
                    "status": COMPLETE,
                },
                {
                    "subproblem": "Q1",
                    "model_level": "C2",
                    "parent_model": "linear",
                    "baseline": "linear",
                    "candidate": "robust",
                    "added_mechanism": "demand uncertainty",
                    "mechanism_fit": "stress violations",
                    "assumptions": "bounded demand",
                    "new_parameters": "radius",
                    "expected_diagnostic_signature": "feasibility improves",
                    "failure_test": "no feasibility gain",
                    "validation_cost": "medium",
                    "identifiability_status": "PASS",
                    "selected": "true",
                    "selection_evidence": "results/model-comparison.json",
                    "status": COMPLETE,
                },
            ],
        )
        write_csv(
            reports / "parameter_registry.csv",
            PARAMETER_FIELDS,
            [
                {
                    "subproblem": "Q1",
                    "model_id": "robust",
                    "parameter": "uncertainty radius",
                    "symbol": "rho",
                    "role": "fixed",
                    "unit": "1",
                    "scope": "all scenarios",
                    "source": "calibrated from held-out scenarios",
                    "bounds": "0..0.3",
                    "identifiability_status": "PASS",
                    "claim_boundary": "tested range only",
                    "status": COMPLETE,
                    "claim_sensitive": "true",
                    "source_class": "data_calibrated",
                    "source_locator": "data/processed/calibration.csv",
                    "source_sha256": digest(calibration),
                    "citation_key": "",
                    "calibration_command": "python code/calibrate.py",
                    "sensitivity_evidence": "results/sensitivity.json",
                    "paper_location": "paper/sections/model.tex#parameter-source",
                }
            ],
        )
        write_csv(reports / "model_simplification_log.csv", SIMPLIFICATION_FIELDS, [])
        write_csv(reports / "fallback_plan.csv", FALLBACK_FIELDS, [])
        write_csv(
            reports / "bibliography.csv",
            ["citation_key", "source_locator", "status"],
            [],
        )
        write_csv(
            reports / "paper_reasoning_map.csv",
            MAP_FIELDS,
            [
                {
                    "subproblem": "Q1",
                    "paper_location": "paper/sections/model.tex#q1",
                    "modeling_path": "容量约束 -> 线性基线 -> 鲁棒候选 -> 压力测试 -> 路径建议",
                    "modeling_path_evidence": "reports/traceability.md",
                    "modeling_path_evidence_sha256": digest(trace),
                    "model_choice_required": "true",
                    "model_choice_location": "paper/sections/model.tex#model-choice",
                    "parameter_location": "paper/sections/model.tex#parameter-source",
                    "failed_route_required": "false",
                    "failed_route_location": "",
                    "boundary_required": "false",
                    "boundary_location": "",
                    "human_reviewer": "team-member-2",
                    "status": COMPLETE,
                }
            ],
        )

    def test_natural_prose_passes_without_fixed_visible_headings(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.scaffold(root)
            report = self.run_audit(root)
            self.assertEqual(report["status"], "PASS", report)
            self.assertTrue(report["subproblems"][0]["model_choice_triggered"])
            self.assertFalse(report["subproblems"][0]["failed_route_triggered"])

    def test_model_choice_and_human_review_are_not_generic_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.scaffold(root)
            path = root / "reports" / "paper_reasoning_map.csv"
            rows = read_rows(path)
            rows[0]["model_choice_location"] = ""
            rows[0]["human_reviewer"] = "ChatGPT"
            write_csv(path, MAP_FIELDS, rows)
            report = self.run_audit(root, expect=1)
            joined = " ".join(report["errors"])
            self.assertIn("model choice", joined)
            self.assertIn("human reviewer", joined)

    def test_all_parameter_source_classes_are_bound_to_real_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.scaffold(root)
            reports = root / "reports"
            results = root / "results"
            passage = reports / "source-passages" / "ref-threshold.txt"
            passage.parent.mkdir()
            passage.write_text("The recommended threshold is 0.20.", encoding="utf-8")
            assumption = reports / "assumption-note.md"
            assumption.write_text("Expert operating assumption.", encoding="utf-8")
            rules = root / "rules.lock.json"
            rules.write_text('{"threshold": 0.25}\n', encoding="utf-8")
            sensitivity = results / "sensitivity.json"
            base = read_rows(reports / "parameter_registry.csv")[0]

            def row(name: str, source_class: str, locator: Path, **updates: str) -> dict[str, str]:
                item = dict(base)
                item.update(
                    parameter=name,
                    source_class=source_class,
                    source_locator=locator.relative_to(root).as_posix(),
                    source_sha256=digest(locator),
                    calibration_command="",
                    sensitivity_evidence="",
                    citation_key="",
                )
                item.update(updates)
                return item

            rows = [
                row("literature threshold", "literature", passage, citation_key="ref_threshold"),
                base,
                row(
                    "expert threshold",
                    "assumption",
                    assumption,
                    sensitivity_evidence=sensitivity.relative_to(root).as_posix(),
                ),
                row("official threshold", "official", rules),
            ]
            write_csv(reports / "parameter_registry.csv", PARAMETER_FIELDS, rows)
            write_csv(
                reports / "bibliography.csv",
                ["citation_key", "source_locator", "status"],
                [
                    {
                        "citation_key": "ref_threshold",
                        "source_locator": passage.relative_to(root).as_posix(),
                        "status": COMPLETE,
                    }
                ],
            )
            self.assertEqual(self.run_audit(root)["status"], "PASS")

            rows[0]["citation_key"] = "missing_reference"
            rows[1]["calibration_command"] = ""
            rows[2]["sensitivity_evidence"] = ""
            rows[3]["source_sha256"] = "0" * 64
            write_csv(reports / "parameter_registry.csv", PARAMETER_FIELDS, rows)
            report = self.run_audit(root, expect=1)
            joined = " ".join(report["errors"])
            self.assertIn("citation", joined)
            self.assertIn("calibration command", joined)
            self.assertIn("sensitivity evidence", joined)
            self.assertIn("SHA-256", joined)

    def test_failed_route_is_required_only_when_execution_evidence_exists(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.scaffold(root)
            self.assertEqual(self.run_audit(root)["status"], "PASS")
            reports = root / "reports"
            write_csv(
                reports / "model_simplification_log.csv",
                SIMPLIFICATION_FIELDS,
                [
                    {
                        "subproblem": "Q1",
                        "primary_route": "nonlinear robust model",
                        "failure_diagnostic": "solver timed out after 600 seconds",
                        "decision_state": "failed",
                        "retained_core_factors": "capacity and time windows",
                        "removed_noncritical_factors": "second-order interaction",
                        "simplified_route": "linear robust model",
                        "user_authorization": "confirmed",
                        "original_model_treatment": "model optimization",
                        "result_file": "results/failed-run.json",
                        "paper_location": "paper/sections/model.tex#failed-route",
                        "status": COMPLETE,
                    }
                ],
            )
            missing = self.run_audit(root, expect=1)
            self.assertTrue(any("failed route" in item for item in missing["errors"]))

            failed = root / "results" / "failed-run.json"
            failed.write_text('{"status": "timeout"}\n', encoding="utf-8")
            map_path = reports / "paper_reasoning_map.csv"
            rows = read_rows(map_path)
            rows[0]["failed_route_required"] = "true"
            rows[0]["failed_route_location"] = "paper/sections/model.tex#failed-route"
            write_csv(map_path, MAP_FIELDS, rows)
            self.assertEqual(self.run_audit(root)["status"], "PASS")

    def test_conditional_identifiability_triggers_boundary_narrative(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.scaffold(root)
            reports = root / "reports"
            parameters = read_rows(reports / "parameter_registry.csv")
            parameters[0]["identifiability_status"] = "CONDITIONAL"
            write_csv(reports / "parameter_registry.csv", PARAMETER_FIELDS, parameters)
            report = self.run_audit(root, expect=1)
            self.assertTrue(any("boundary" in item for item in report["errors"]))

            map_path = reports / "paper_reasoning_map.csv"
            rows = read_rows(map_path)
            rows[0]["boundary_required"] = "true"
            rows[0]["boundary_location"] = "paper/sections/conclusion.tex#applicability"
            write_csv(map_path, MAP_FIELDS, rows)
            self.assertEqual(self.run_audit(root)["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
