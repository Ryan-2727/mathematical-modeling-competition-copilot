from __future__ import annotations

import base64
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


class OrchestrationAndPaperAssuranceTests(unittest.TestCase):
    def run_script(
        self, name: str, *args: str, expect: int | set[int] = 0
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / name), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        expected = expect if isinstance(expect, set) else {expect}
        self.assertIn(result.returncode, expected, result.stdout + result.stderr)
        return result

    @staticmethod
    def digest(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def init_project(
        self, root: Path, contest: str = "CUMCM", year: str = "2026"
    ) -> None:
        self.run_script(
            "init_contest.py",
            "--project-dir",
            str(root),
            "--contest",
            contest,
            "--year",
            year,
            "--mode",
            "training",
        )

    def create_passing_minimal_project(
        self, root: Path, contest: str = "CUMCM", year: str = "2026"
    ) -> None:
        self.init_project(root, contest, year)
        source = root / "results" / "source.csv"
        source.write_text("metric,value\nobjective,12.5\n", encoding="utf-8")
        verified = root / "results" / "verified_values.csv"
        with verified.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "key",
                    "value",
                    "value_type",
                    "unit",
                    "source_file",
                    "source_sha256",
                    "source_locator",
                    "source_kind",
                    "justification",
                ]
            )
            writer.writerow(
                [
                    "objective",
                    "12.5",
                    "number",
                    "kg",
                    "results/source.csv",
                    self.digest(source),
                    "row 2",
                    "computed",
                    "reproduced",
                ]
            )
        (root / "reports" / "conclusion_map.csv").write_text(
            "subproblem,question,answer_or_recommendation,decisive_value_key,"
            "method_rationale_location,validation_location,limitation_location,"
            "figure_or_table,paper_location,status\n"
            "Q1,What route?,Use route A,objective,sec:model,sec:validation,"
            "sec:limitations,tab:results,sec:conclusion,verified\n",
            encoding="utf-8",
        )
        (root / "reports" / "model_decision_log.csv").write_text(
            "subproblem,model_level,parent_model,baseline,candidate,added_mechanism,"
            "mechanism_fit,assumptions,new_parameters,expected_diagnostic_signature,"
            "failure_test,validation_cost,identifiability_status,selected,selection_evidence,status\n"
            "Q1,C1,mean,mean,robust optimization,resource uncertainty,fit,documented,"
            "uncertainty radius,worst-case feasibility,stress test,low,PASS,true,"
            "results/source.csv,verified\n",
            encoding="utf-8",
        )
        (root / "reports" / "parameter_registry.csv").write_text(
            "subproblem,model_id,parameter,symbol,role,unit,scope,source,bounds,"
            "identifiability_status,claim_boundary,status\n"
            "Q1,robust optimization,uncertainty radius,rho,shared,kg,all scenarios,"
            "data,0..10,PASS,supported,verified\n",
            encoding="utf-8",
        )
        (root / "reports" / "independent_routes.csv").write_text(
            "subproblem,route_id,route_role,principle,data_representation,failure_mode,"
            "result_file,result_value,tolerance,comparison_status,limitation,status\n"
            "Q1,opt,primary,robust optimization,scenario matrix,solver convergence,"
            "results/source.csv,12.5,0.1,agree,none,verified\n"
            "Q1,enum,independent_check,enumeration,small-case states,state truncation,"
            "results/source.csv,12.5,0.1,agree,small case only,verified\n",
            encoding="utf-8",
        )
        (root / "reports" / "result_reconciliation.csv").write_text(
            "subproblem,comparison_id,primary_route,comparison_route,primary_value,"
            "comparison_value,tolerance,disagreement_material,investigation_step,cause,"
            "resolution,claim_action,evidence_file,status\n"
            "Q1,R1,opt,enum,12.5,12.5,0.1,false,not_applicable,within tolerance,"
            "retain primary,admit,results/source.csv,verified\n",
            encoding="utf-8",
        )
        (root / "reports" / "joint_inference_design.json").write_text(
            json.dumps({"applicable": False, "reason": "one scenario system", "subproblems": []}),
            encoding="utf-8",
        )
        (root / "reports" / "stress_tests.csv").write_text(
            "claim_id,subproblem,stress_type,change,acceptance_criterion,"
            "result_file,outcome,verdict,status\n"
            "C1,Q1,parameter,+10%,stable,results/source.csv,stable,pass,verified\n",
            encoding="utf-8",
        )
        (root / "reports" / "figure_manifest.csv").write_text(
            "figure,label,source_data,caption_insight,status\n",
            encoding="utf-8",
        )
        model = root / "paper" / "sections" / "model.tex"
        model.write_text(
            "We define $x$ as the decision variable with unit kg.\n",
            encoding="utf-8",
        )
        (root / "reports" / "notation_registry.csv").write_text(
            "symbol,canonical_tex,meaning,kind,unit,first_definition,code_names,"
            "figure_labels,appendix_location,equation_ids,status\n"
            "x,x,decision variable,scalar,kg,paper/sections/model.tex#L1,"
            "x_value,,,eq:balance,verified\n",
            encoding="utf-8",
        )
        (root / "reports" / "equation_dimensions.csv").write_text(
            "equation_id,left_dimension,right_dimension,notation_symbols,evidence,status\n"
            "eq:balance,kg,kg,x,paper/sections/model.tex#L1,verified\n",
            encoding="utf-8",
        )
        (root / "reports" / "decision_stability.csv").write_text(
            "decision_id,subproblem,baseline_recommendation,perturbation_id,"
            "perturbation,perturbed_recommendation,recommendation_changed,"
            "materiality,conditional_conclusion,limitation_location,result_file,"
            "paper_location,status\n"
            "D1,Q1,route A,P1,demand +10%,route A,false,not_material,not_applicable,"
            "sec:limitations,results/source.csv,sec:conclusion,verified\n",
            encoding="utf-8",
        )
        (root / "reports" / "model_budget.csv").write_text(
            "subproblem,route_name,route_type,selected,estimated_hours,risk_level,"
            "validation_hours,fallback_route,expected_value,deadline_hours,status\n"
            "Q1,baseline,baseline,true,2,low,1,fallback,complete answer,10,verified\n"
            "Q1,fallback,fallback,false,1,low,1,baseline,complete answer,10,verified\n",
            encoding="utf-8",
        )

    def test_initializer_and_additive_idempotent_migration(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "project"
            self.init_project(root)
            manifest_path = root / "contest_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["project_schema_version"], 2)
            self.assertEqual(manifest["quality_profile"], "standard")
            for name in (
                "rendered_figure_manifest.csv",
                "notation_registry.csv",
                "equation_dimensions.csv",
            ):
                self.assertTrue((root / "reports" / name).is_file())
            (root / "reports" / "parameter_registry.csv").unlink()
            legacy = {"contest": "CUMCM", "unknown_evidence": {"keep": True}}
            manifest_path.write_text(json.dumps(legacy), encoding="utf-8")
            self.run_script(
                "contestctl.py",
                "migrate",
                "--project-dir",
                str(root),
            )
            self.assertEqual(
                json.loads(manifest_path.read_text(encoding="utf-8")), legacy
            )
            preview = json.loads(
                (root / "reports" / "project_migration.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertFalse(preview["applied"])
            self.assertTrue(preview["changes"])
            self.assertTrue(any(item["op"] == "create_file" for item in preview["changes"]))
            self.run_script(
                "contestctl.py",
                "migrate",
                "--project-dir",
                str(root),
                "--apply",
            )
            migrated = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertTrue(migrated["unknown_evidence"]["keep"])
            self.assertEqual(migrated["project_schema_version"], 2)
            for name in (
                "parameter_registry.csv",
                "independent_routes.csv",
                "result_reconciliation.csv",
                "joint_inference_design.json",
            ):
                self.assertTrue((root / "reports" / name).is_file())
            self.run_script(
                "contestctl.py",
                "migrate",
                "--project-dir",
                str(root),
            )
            final = json.loads(
                (root / "reports" / "project_migration.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(final["changes"], [])
            self.init_project(root)
            self.assertTrue(
                json.loads(manifest_path.read_text(encoding="utf-8"))[
                    "unknown_evidence"
                ]["keep"]
            )

    def test_minimal_workflow_caches_only_unchanged_passing_nodes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "project"
            self.create_passing_minimal_project(root)
            command = (
                "contestctl.py",
                "run",
                "--project-dir",
                str(root),
                "--phase",
                "paper",
                "--profile",
                "minimal",
            )
            self.run_script(*command)
            first = json.loads(
                (root / "reports" / "workflow_paper.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertTrue(all(item["status"] == "PASS" for item in first["nodes"]))
            self.assertTrue((root / "paper/generated/core_results.tex").is_file())
            self.run_script(*command)
            second = json.loads(
                (root / "reports" / "workflow_paper.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertTrue(
                all(item["status"] == "SKIPPED" for item in second["nodes"])
            )
            if shutil.which("xelatex"):
                smoke = root / "paper" / "generated_artifacts_smoke.tex"
                smoke.write_text(
                    "\\documentclass{article}\n"
                    "\\usepackage{booktabs}\n"
                    "\\begin{document}\n"
                    "\\input{generated/core_results.tex}\n"
                    "\\input{generated/model_comparison.tex}\n"
                    "\\input{generated/robustness.tex}\n"
                    "\\input{generated/conclusion_snippets.tex}\n"
                    "\\input{generated/figure_notes.tex}\n"
                    "\\input{generated/model_reasoning.tex}\n"
                    "\\input{generated/parameter_roles.tex}\n"
                    "\\input{generated/route_reconciliation.tex}\n"
                    "\\end{document}\n",
                    encoding="utf-8",
                )
                compiled = subprocess.run(
                    [
                        shutil.which("xelatex") or "xelatex",
                        "-interaction=nonstopmode",
                        "-halt-on-error",
                        smoke.name,
                    ],
                    cwd=smoke.parent,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                self.assertEqual(
                    compiled.returncode, 0, compiled.stdout + compiled.stderr
                )
            (root / "results" / "source.csv").write_text(
                "metric,value\nobjective,99\n", encoding="utf-8"
            )
            self.run_script(*command, expect=1)
            third = json.loads(
                (root / "reports" / "workflow_paper.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(third["status"], "FAIL")

    def test_doctor_dry_run_custom_profile_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "project"
            self.init_project(root)
            manifest_path = root / "contest_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["quality_profile"] = "minimal"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            self.run_script(
                "contestctl.py",
                "doctor",
                "--project-dir",
                str(root),
            )
            custom = root / "custom.json"
            custom.write_text(
                json.dumps(
                    {
                        "name": "custom",
                        "phases": {
                            "paper": ["generate-paper-artifacts"],
                            "freeze": [],
                        },
                    }
                ),
                encoding="utf-8",
            )
            self.run_script(
                "contestctl.py",
                "run",
                "--project-dir",
                str(root),
                "--phase",
                "paper",
                "--profile",
                "custom",
                "--profile-file",
                str(custom),
                "--dry-run",
            )
            summary = self.run_script(
                "contestctl.py",
                "summary",
                "--project-dir",
                str(root),
                "--format",
                "json",
            )
            payload = json.loads(summary.stdout)
            self.assertEqual(payload["status"], "PASS")
            self.assertEqual(payload["counts"]["SKIPPED"], 1)
            custom.write_text(
                '{"name":"custom","phases":{"paper":["unknown"],"freeze":[]}}\n',
                encoding="utf-8",
            )
            self.run_script(
                "contestctl.py",
                "run",
                "--project-dir",
                str(root),
                "--phase",
                "paper",
                "--profile",
                "custom",
                "--profile-file",
                str(custom),
                expect=1,
            )

    def test_profile_tool_policy_is_deterministic(self) -> None:
        if str(SCRIPTS) not in sys.path:
            sys.path.insert(0, str(SCRIPTS))
        import contest_orchestration

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "project"
            self.init_project(root)
            with (
                mock.patch.object(
                    contest_orchestration.shutil, "which", return_value=None
                ),
                mock.patch.object(
                    contest_orchestration.importlib.util,
                    "find_spec",
                    return_value=None,
                ),
            ):
                self.assertEqual(
                    contest_orchestration.doctor_project(root, "minimal")["status"],
                    "PASS",
                )
                self.assertEqual(
                    contest_orchestration.doctor_project(root, "standard")["status"],
                    "LIMITED",
                )
                self.assertEqual(
                    contest_orchestration.doctor_project(root, "strict")["status"],
                    "FAIL",
                )

    def test_notation_conflicts_and_dimension_mismatch_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "project"
            self.create_passing_minimal_project(root)
            self.run_script(
                "verify_notation_registry.py", "--project-dir", str(root)
            )
            registry = root / "reports" / "notation_registry.csv"
            registry.write_text(
                registry.read_text(encoding="utf-8")
                + "x,x,other meaning,scalar,kg,paper/sections/model.tex#L1,"
                "other_name,,,eq:balance,verified\n",
                encoding="utf-8",
            )
            self.run_script(
                "verify_notation_registry.py",
                "--project-dir",
                str(root),
                expect=1,
            )
            registry.write_text(
                registry.read_text(encoding="utf-8").splitlines()[0]
                + "\n"
                + registry.read_text(encoding="utf-8").splitlines()[1]
                + "\n",
                encoding="utf-8",
            )
            dimensions = root / "reports" / "equation_dimensions.csv"
            dimensions.write_text(
                dimensions.read_text(encoding="utf-8").replace(
                    "eq:balance,kg,kg", "eq:balance,kg,s"
                ),
                encoding="utf-8",
            )
            self.run_script(
                "verify_notation_registry.py",
                "--project-dir",
                str(root),
                expect=1,
            )

    def test_rendered_figure_contract_binds_hashes_and_human_review(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "reports").mkdir()
            (root / "figures").mkdir()
            (root / "results").mkdir()
            figure = root / "figures" / "result.png"
            source = root / "results" / "result.csv"
            figure.write_bytes(PNG_1X1)
            source.write_text("x,y\n1,2\n", encoding="utf-8")
            header = (
                "figure,figure_sha256,source_data,source_sha256,"
                "generator_command_id,insertion_width_cm,insertion_height_cm,"
                "min_text_pt,min_line_pt,clipping_check,overlap_check,"
                "axis_crowding_check,panel_order,panel_spacing,visual_hierarchy,"
                "grayscale_check,colorblind_check,supported_conclusion,"
                "evidence_location,paper_page,status\n"
            )
            row = (
                f"figures/result.png,{self.digest(figure)},results/result.csv,"
                f"{self.digest(source)},plot-results-v1,0.01,0.01,8,0.6,"
                "verified,verified,verified,single,verified,verified,verified,"
                "verified,C1,reports/claims.csv#C1,3,verified\n"
            )
            manifest = root / "reports" / "rendered_figure_manifest.csv"
            manifest.write_text(header + row, encoding="utf-8")
            self.run_script(
                "verify_rendered_figures.py",
                "--project-dir",
                str(root),
                "--profile",
                "minimal",
            )
            if str(SCRIPTS) not in sys.path:
                sys.path.insert(0, str(SCRIPTS))
            import verify_rendered_figures

            with (
                mock.patch.object(
                    verify_rendered_figures.shutil, "which", return_value=None
                ),
                mock.patch.dict(sys.modules, {"PIL": None}),
            ):
                self.assertEqual(
                    verify_rendered_figures.verify(root.resolve(), "standard")[
                        "status"
                    ],
                    "LIMITED",
                )
                self.assertEqual(
                    verify_rendered_figures.verify(root.resolve(), "strict")["status"],
                    "FAIL",
                )
            manifest.write_text(
                (header + row).replace(self.digest(figure), "0" * 64, 1),
                encoding="utf-8",
            )
            self.run_script(
                "verify_rendered_figures.py",
                "--project-dir",
                str(root),
                "--profile",
                "minimal",
                expect=1,
            )

    def test_cumcm_and_mcm_style_projects_reach_minimal_freeze(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            for folder, contest, year in (
                ("cumcm-e2e", "CUMCM", "2026"),
                ("mcm-e2e", "MCM/ICM", "2027"),
            ):
                root = Path(raw) / folder
                self.create_passing_minimal_project(root, contest, year)
                self.run_script(
                    "contestctl.py",
                    "run",
                    "--project-dir",
                    str(root),
                    "--phase",
                    "freeze",
                    "--profile",
                    "minimal",
                )
                payload = json.loads(
                    (root / "reports" / "workflow_freeze.json").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual(payload["status"], "PASS")
                self.assertTrue(
                    all(item["status"] == "PASS" for item in payload["nodes"])
                )
                expected_template = (
                    "mcm-icm" if contest == "MCM/ICM" else "cumcm"
                )
                manifest = json.loads(
                    (root / "contest_manifest.json").read_text(encoding="utf-8")
                )
                self.assertEqual(manifest["latex_template"], expected_template)


if __name__ == "__main__":
    unittest.main()
