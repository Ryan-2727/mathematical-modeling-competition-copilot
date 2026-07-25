from __future__ import annotations

import copy
import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
DIMENSIONS = (
    "correctness_evidence",
    "validation",
    "reproducibility",
    "writing",
    "visual_communication",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class QualityEvidenceTests(unittest.TestCase):
    def run_script(
        self,
        name: str,
        *args: str,
        expect: int = 0,
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / name), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(result.returncode, expect, result.stdout + result.stderr)
        return result

    def create_value_project(self, root: Path) -> tuple[Path, Path]:
        (root / "results").mkdir(parents=True)
        (root / "paper" / "sections").mkdir(parents=True)
        source = root / "results" / "metrics.json"
        source.write_text(
            json.dumps(
                {
                    "metrics": {
                        "rmse": 0.125,
                        "selected_count": 12,
                        "converged": True,
                        "scenario": "robust",
                    }
                }
            )
            + "\n",
            encoding="utf-8",
        )
        registry = root / "results" / "verified_values.csv"
        fields = [
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
        rows = [
            ("rmse", "0.125", "number", "dimensionless", "/metrics/rmse"),
            ("selected_count", "12", "integer", "items", "/metrics/selected_count"),
            ("converged", "true", "boolean", "dimensionless", "/metrics/converged"),
            ("scenario", "robust", "string", "dimensionless", "/metrics/scenario"),
        ]
        with registry.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for key, value, value_type, unit, locator in rows:
                writer.writerow(
                    {
                        "key": key,
                        "value": value,
                        "value_type": value_type,
                        "unit": unit,
                        "source_file": "results/metrics.json",
                        "source_sha256": sha256(source),
                        "source_locator": locator,
                        "source_kind": "computed",
                        "justification": "",
                    }
                )
        (root / "paper" / "main.tex").write_text(
            "\\documentclass{article}\n"
            "\\input{generated/results}\n"
            "\\begin{document}\n"
            "\\input{sections/results}\n"
            "\\end{document}\n",
            encoding="utf-8",
        )
        body = root / "paper" / "sections" / "results.tex"
        body.write_text(
            "RMSE: \\VerifiedValue{rmse}. "
            "Count: \\VerifiedValueWithUnit{selected_count}. "
            "Converged: \\VerifiedValue{converged}. "
            "Scenario: \\VerifiedValue{scenario}.\n",
            encoding="utf-8",
        )
        return source, body

    def test_verified_values_generate_and_detect_stale_or_unused_data(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source, body = self.create_value_project(root)
            report = root / "reports" / "verified_values.json"
            self.run_script("generate_verified_values.py", "--project-dir", str(root))
            generated = root / "paper" / "generated" / "results.tex"
            self.assertIn("registry-sha256:", generated.read_text(encoding="utf-8"))
            self.run_script(
                "verify_verified_values.py",
                "--project-dir",
                str(root),
                "--out",
                str(report),
            )
            passed = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(passed["status"], "PASS")
            self.assertEqual(passed["counts"]["used_values"], 4)
            self.assertIn("not mathematical correctness", passed["scope"])

            original_source = source.read_text(encoding="utf-8")
            source.write_text(original_source.replace("0.125", "0.25"), encoding="utf-8")
            self.run_script(
                "verify_verified_values.py",
                "--project-dir",
                str(root),
                "--out",
                str(report),
                expect=1,
            )
            stale_source = json.loads(report.read_text(encoding="utf-8"))
            self.assertTrue(
                any("source SHA-256 mismatch" in error for error in stale_source["errors"])
            )

            source.write_text(original_source, encoding="utf-8")
            generated.write_text(
                generated.read_text(encoding="utf-8") + "% manual edit\n",
                encoding="utf-8",
            )
            self.run_script(
                "verify_verified_values.py",
                "--project-dir",
                str(root),
                "--out",
                str(report),
                expect=1,
            )
            stale_tex = json.loads(report.read_text(encoding="utf-8"))
            self.assertTrue(any("stale or manually modified" in error for error in stale_tex["errors"]))

            self.run_script("generate_verified_values.py", "--project-dir", str(root))
            body.write_text(
                body.read_text(encoding="utf-8").replace(
                    "Scenario: \\VerifiedValue{scenario}.", "Scenario omitted."
                ),
                encoding="utf-8",
            )
            self.run_script(
                "verify_verified_values.py",
                "--project-dir",
                str(root),
                "--out",
                str(report),
                expect=1,
            )
            unused = json.loads(report.read_text(encoding="utf-8"))
            self.assertTrue(
                any("not actually used" in error and "scenario" in error for error in unused["errors"])
            )

    def test_verified_values_reject_duplicate_key_type_and_unit_errors(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source, _ = self.create_value_project(root)
            registry = root / "results" / "verified_values.csv"
            fields = [
                "key",
                "value",
                "value_type",
                "unit",
                "source_file",
                "source_sha256",
                "source_locator",
            ]
            rows = [
                {
                    "key": "bad key",
                    "value": "not-a-number",
                    "value_type": "number",
                    "unit": "",
                    "source_file": "results/metrics.json",
                    "source_sha256": sha256(source),
                    "source_locator": "/metrics/rmse",
                },
                {
                    "key": "duplicate_key",
                    "value": "0.125",
                    "value_type": "number",
                    "unit": "dimensionless",
                    "source_file": "results/metrics.json",
                    "source_sha256": sha256(source),
                    "source_locator": "/metrics/rmse",
                },
                {
                    "key": "duplicate_key",
                    "value": "0.125",
                    "value_type": "number",
                    "unit": "dimensionless",
                    "source_file": "results/metrics.json",
                    "source_sha256": sha256(source),
                    "source_locator": "/metrics/rmse",
                },
            ]
            with registry.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
            result = self.run_script(
                "generate_verified_values.py",
                "--project-dir",
                str(root),
                expect=1,
            )
            self.assertIn("duplicate key", result.stdout)
            self.assertIn("invalid key", result.stdout)
            self.assertIn("invalid numeric value", result.stdout)
            self.assertIn("unit must not be empty", result.stdout)

    @staticmethod
    def model_fixtures() -> tuple[list[dict[str, object]], dict[str, dict[str, object]]]:
        evidence = {
            "regression_forecast": {
                "split_ordered": True,
                "leakage_checked": True,
                "residual_diagnostics": True,
                "baseline_name": "seasonal naive",
                "holdout_size": 30,
                "metric_direction": "lower",
                "model_metric": 0.8,
                "baseline_metric": 1.0,
            },
            "classification": {
                "class_counts": {"negative": 50, "positive": 40},
                "confusion_matrix": [[45, 5], [4, 36]],
                "calibration_checked": True,
                "threshold_selected": False,
                "macro_f1": 0.9,
                "minority_recall": 0.85,
            },
            "optimization": {
                "feasible": True,
                "constraint_audit": True,
                "solver_status": "optimal",
                "objective_direction": "maximize",
                "objective_value": 120,
                "baseline_objective": 100,
                "relative_gap": 0.001,
            },
            "simulation_stochastic": {
                "convergence_checked": True,
                "seeds": [11, 22, 33],
                "replications": 100,
                "estimate": 10,
                "ci_lower": 9.2,
                "ci_upper": 10.8,
            },
            "network_ranking": {
                "connected_or_consistent": True,
                "normalized": True,
                "perturbation_checked": True,
                "weight_sensitivity_checked": True,
                "score_sum": 1.0,
                "rank_instability": 0.1,
            },
            "mechanism_dynamics": {
                "units_checked": True,
                "initial_conditions_checked": True,
                "boundary_conditions_checked": True,
                "limiting_cases_checked": True,
                "numerical_stability_checked": True,
                "time_step_refinement_error": 0.01,
            },
            "causal_econometric": {
                "identification_strategy": "difference in differences",
                "identification_assumptions_checked": True,
                "overlap_or_support_checked": True,
                "falsification_checked": True,
                "robust_inference_checked": True,
                "sample_size": 500,
                "effect_estimate": 0.2,
                "standard_error": 0.03,
                "relative_sensitivity_shift": 0.05,
            },
            "unsupervised": {
                "scaling_checked": True,
                "cluster_or_component_choice_justified": True,
                "stability_checked": True,
                "baseline_compared": True,
                "sample_size": 300,
                "stability_score": 0.9,
                "quality_score": 0.65,
            },
            "queueing_reliability": {
                "analysis_type": "queueing",
                "flow_or_probability_balance_checked": True,
                "stationarity_or_horizon_justified": True,
                "analytic_or_simulation_crosscheck": True,
                "transient_or_warmup_checked": True,
                "maximum_utilization": 0.8,
                "crosscheck_relative_error": 0.02,
            },
            "spatial_spatiotemporal": {
                "crs_checked": True,
                "spatial_leakage_checked": True,
                "spatial_holdout_checked": True,
                "residual_spatial_dependence_checked": True,
                "holdout_regions": 8,
                "model_metric": 0.7,
                "baseline_metric": 1.0,
                "metric_direction": "lower",
            },
            "multiobjective_dynamic_optimization": {
                "feasible": True,
                "constraint_audit": True,
                "pareto_or_recursion_checked": True,
                "baseline_compared": True,
                "solution_stability_checked": True,
                "tradeoff_or_state_interpretation": "cost-risk Pareto frontier",
                "relative_gap": 0.01,
                "solution_instability": 0.05,
            },
        }
        thresholds = {
            "regression_forecast": {
                "minimum_holdout_size": 20,
                "minimum_relative_improvement": 0.1,
            },
            "classification": {
                "minimum_class_count": 20,
                "minimum_macro_f1": 0.8,
                "minimum_minority_recall": 0.75,
            },
            "optimization": {
                "maximum_relative_gap": 0.01,
                "minimum_relative_improvement": 0.05,
            },
            "simulation_stochastic": {
                "minimum_replications": 30,
                "minimum_unique_seeds": 2,
                "maximum_relative_ci_width": 0.25,
            },
            "network_ranking": {
                "normalization_target": 1,
                "normalization_tolerance": 0.000001,
                "maximum_rank_instability": 0.2,
            },
            "mechanism_dynamics": {
                "maximum_time_step_refinement_error": 0.05,
            },
            "causal_econometric": {
                "minimum_sample_size": 100,
                "maximum_relative_sensitivity_shift": 0.1,
            },
            "unsupervised": {
                "minimum_sample_size": 100,
                "minimum_stability_score": 0.8,
                "minimum_quality_score": 0.5,
            },
            "queueing_reliability": {
                "maximum_utilization": 0.9,
                "maximum_crosscheck_relative_error": 0.05,
            },
            "spatial_spatiotemporal": {
                "minimum_holdout_regions": 5,
                "minimum_relative_improvement": 0.1,
            },
            "multiobjective_dynamic_optimization": {
                "maximum_relative_gap": 0.05,
                "maximum_solution_instability": 0.1,
            },
        }
        models = [
            {
                "id": f"{family}-model",
                "family": family,
                "evidence_file": f"results/{family}.json",
                "thresholds": thresholds[family],
            }
            for family in evidence
        ]
        return models, evidence

    def test_all_model_family_adapters_pass_and_fail_on_decisive_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "results").mkdir()
            (root / "reports").mkdir()
            models, evidence = self.model_fixtures()
            for family, payload in evidence.items():
                (root / "results" / f"{family}.json").write_text(
                    json.dumps(payload) + "\n", encoding="utf-8"
                )
            manifest = root / "reports" / "model_validation.json"
            manifest.write_text(json.dumps({"models": models}) + "\n", encoding="utf-8")
            report = root / "reports" / "model_validation_report.json"
            self.run_script(
                "verify_model_validation.py",
                "--project-dir",
                str(root),
                "--out",
                str(report),
            )
            passed = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(passed["status"], "PASS")
            self.assertEqual(passed["counts"]["families"], 11)
            self.assertIn("does not prove mathematical correctness", passed["scope"])

            failures = {
                "regression_forecast": ("split_ordered", False),
                "classification": ("macro_f1", 0.1),
                "optimization": ("feasible", False),
                "simulation_stochastic": ("replications", 2),
                "network_ranking": ("rank_instability", 0.9),
                "mechanism_dynamics": ("units_checked", False),
                "causal_econometric": ("falsification_checked", False),
                "unsupervised": ("stability_score", 0.1),
                "queueing_reliability": ("maximum_utilization", 1.2),
                "spatial_spatiotemporal": ("spatial_leakage_checked", False),
                "multiobjective_dynamic_optimization": ("relative_gap", 0.5),
            }
            for family, (field, bad_value) in failures.items():
                with self.subTest(family=family):
                    path = root / "results" / f"{family}.json"
                    bad_evidence = copy.deepcopy(evidence[family])
                    bad_evidence[field] = bad_value
                    path.write_text(json.dumps(bad_evidence) + "\n", encoding="utf-8")
                    self.run_script(
                        "verify_model_validation.py",
                        "--project-dir",
                        str(root),
                        "--out",
                        str(report),
                        expect=1,
                    )
                    failed = json.loads(report.read_text(encoding="utf-8"))
                    family_report = next(
                        item for item in failed["models"] if item["family"] == family
                    )
                    self.assertEqual(family_report["status"], "FAIL")
                    self.assertTrue(family_report["errors"])
                    path.write_text(
                        json.dumps(evidence[family]) + "\n", encoding="utf-8"
                    )

    def test_model_validation_accepts_csv_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "results").mkdir()
            (root / "reports").mkdir()
            models, evidence = self.model_fixtures()
            family = "regression_forecast"
            evidence_path = root / "results" / f"{family}.json"
            evidence_path.write_text(json.dumps(evidence[family]) + "\n", encoding="utf-8")
            manifest = root / "reports" / "model_validation.csv"
            with manifest.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["id", "family", "evidence_file", "thresholds_json"],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "id": "forecast-csv",
                        "family": family,
                        "evidence_file": f"results/{family}.json",
                        "thresholds_json": json.dumps(models[0]["thresholds"]),
                    }
                )
            self.run_script(
                "verify_model_validation.py",
                "--project-dir",
                str(root),
                "--manifest",
                str(manifest),
                "--out",
                str(root / "reports" / "csv-report.json"),
            )

    def test_queueing_reliability_accepts_reliability_branch(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "reports").mkdir()
            manifest = {
                "models": [
                    {
                        "id": "reliability-model",
                        "family": "queueing_reliability",
                        "thresholds": {
                            "minimum_system_reliability": 0.9,
                            "maximum_crosscheck_relative_error": 0.05,
                        },
                        "evidence": {
                            "analysis_type": "reliability",
                            "flow_or_probability_balance_checked": True,
                            "stationarity_or_horizon_justified": True,
                            "analytic_or_simulation_crosscheck": True,
                            "transient_or_warmup_checked": True,
                            "component_monotonicity_checked": True,
                            "system_reliability": 0.97,
                            "crosscheck_relative_error": 0.01,
                        },
                    }
                ]
            }
            (root / "reports" / "model_validation.json").write_text(
                json.dumps(manifest) + "\n", encoding="utf-8"
            )
            self.run_script(
                "verify_model_validation.py",
                "--project-dir",
                str(root),
                "--out",
                str(root / "reports" / "model_validation_report.json"),
            )

    def test_queueing_accepts_explicit_finite_horizon_overload(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "reports").mkdir()
            manifest = {
                "models": [{
                    "id": "finite-horizon-queue",
                    "family": "queueing_reliability",
                    "thresholds": {
                        "maximum_crosscheck_relative_error": 0.05,
                    },
                    "evidence": {
                        "analysis_type": "queueing",
                        "flow_or_probability_balance_checked": True,
                        "stationarity_or_horizon_justified": True,
                        "analytic_or_simulation_crosscheck": True,
                        "transient_or_warmup_checked": True,
                        "finite_horizon_only": True,
                        "finite_horizon_capacity_checked": True,
                        "maximum_utilization": 1.2,
                        "crosscheck_relative_error": 0.01,
                    },
                }]
            }
            (root / "reports" / "model_validation.json").write_text(
                json.dumps(manifest) + "\n", encoding="utf-8"
            )
            self.run_script(
                "verify_model_validation.py",
                "--project-dir",
                str(root),
                "--out",
                str(root / "reports" / "model_validation_report.json"),
            )

    @staticmethod
    def benchmark_manifest() -> dict[str, object]:
        rubric = {
            dimension: {
                "weight": 0.2,
                "criterion": f"Artifact-backed {dimension.replace('_', ' ')} evidence.",
            }
            for dimension in DIMENSIONS
        }
        return {
            "schema_version": 1,
            "description": "Synthetic private-test fixture.",
            "cases": [
                {
                    "id": "synthetic-prediction",
                    "enabled": True,
                    "problem_family": "prediction",
                    "allowed_inputs": ["inputs/synthetic.csv"],
                    "required_subproblems": ["Q1"],
                    "expected_artifacts": [
                        {"class": "analysis_report", "path": "artifacts/analysis.md"}
                    ],
                    "command": [sys.executable, "-c", "print('external runner')"],
                    "runtime_budget_seconds": 10,
                    "result_file": "benchmark-results/current.json",
                    "rubric": rubric,
                    "baseline_scores": {dimension: 4.0 for dimension in DIMENSIONS},
                    "regression_tolerance": {
                        **{dimension: 0.1 for dimension in DIMENSIONS},
                        "overall": 0.1,
                    },
                }
            ],
        }

    def test_benchmark_blocks_regression_without_updating_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            for directory in ("inputs", "artifacts", "evidence", "benchmark-results", "reports"):
                (root / directory).mkdir()
            (root / "inputs" / "synthetic.csv").write_text("x,y\n1,2\n", encoding="utf-8")
            (root / "artifacts" / "analysis.md").write_text(
                "Synthetic analysis only.\n", encoding="utf-8"
            )
            (root / "evidence" / "score.md").write_text(
                "Blinded rubric evidence.\n", encoding="utf-8"
            )
            result_path = root / "benchmark-results" / "current.json"

            def write_result(score: float) -> None:
                result_path.write_text(
                    json.dumps(
                        {
                            "case_id": "synthetic-prediction",
                            "scores": {
                                dimension: {
                                    "score": score,
                                    "evidence": ["evidence/score.md"],
                                }
                                for dimension in DIMENSIONS
                            },
                            "artifacts": [
                                {
                                    "class": "analysis_report",
                                    "path": "artifacts/analysis.md",
                                }
                            ],
                        }
                    )
                    + "\n",
                    encoding="utf-8",
                )

            manifest_path = root / "benchmark.json"
            manifest_path.write_text(
                json.dumps(self.benchmark_manifest(), indent=2) + "\n",
                encoding="utf-8",
            )
            original_manifest_hash = sha256(manifest_path)
            report = root / "reports" / "benchmark.json"
            write_result(4.1)
            self.run_script(
                "run_benchmark_regression.py",
                "--project-dir",
                str(root),
                "--manifest",
                str(manifest_path),
                "--out",
                str(report),
                "--execute",
            )
            passed = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(passed["status"], "PASS")
            self.assertEqual(passed["cases"][0]["execution"]["returncode"], 0)
            self.assertFalse(passed["baseline_updated"])
            self.assertEqual(sha256(manifest_path), original_manifest_hash)

            write_result(3.0)
            self.run_script(
                "run_benchmark_regression.py",
                "--project-dir",
                str(root),
                "--manifest",
                str(manifest_path),
                "--out",
                str(report),
                expect=1,
            )
            failed = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(failed["status"], "FAIL")
            self.assertTrue(any("regressed" in error for error in failed["errors"]))
            self.assertFalse(failed["baseline_updated"])
            self.assertEqual(sha256(manifest_path), original_manifest_hash)

    def test_publishable_benchmark_example_contains_no_problem_or_answer(self) -> None:
        schema = json.loads(
            (ROOT / "evals" / "quality-benchmark-schema.json").read_text(encoding="utf-8")
        )
        example = json.loads(
            (ROOT / "evals" / "quality-benchmark-example.json").read_text(encoding="utf-8")
        )
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(example["schema_version"], 1)
        self.assertFalse(example["cases"][0]["enabled"])
        lowered = json.dumps(example).lower()
        for forbidden in (
            "problem_statement",
            "expected_answer",
            "paired_paper",
            "hidden_solution",
        ):
            self.assertNotIn(f'"{forbidden}"', lowered)
        self.assertIn("no contest statement", example["description"].lower())
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            manifest = root / "quality-benchmark-example.json"
            manifest.write_text(json.dumps(example) + "\n", encoding="utf-8")
            report = root / "example-report.json"
            self.run_script(
                "run_benchmark_regression.py",
                "--project-dir",
                str(root),
                "--manifest",
                str(manifest),
                "--out",
                str(report),
                expect=2,
            )
            self.assertEqual(
                json.loads(report.read_text(encoding="utf-8"))["status"], "LIMITED"
            )


if __name__ == "__main__":
    unittest.main()
