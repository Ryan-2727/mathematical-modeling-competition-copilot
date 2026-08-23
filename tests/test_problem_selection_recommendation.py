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
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from contest_orchestration import load_profile, resolve_nodes
from problem_selection_core import (
    CALIBRATION_FIELDS,
    CRITERIA,
    combine_ai_fit,
    dirichlet_summary,
    effective_sample_size,
    scenario_analysis,
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, fields: list[str] | tuple[str, ...], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


class ProblemSelectionRecommendationTests(unittest.TestCase):
    def run_script(self, name: str, *args: str, expect: int = 0) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            [sys.executable, str(SCRIPTS / name), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(completed.returncode, expect, completed.stdout + completed.stderr)
        return completed

    def make_fixture(self, root: Path, calibrated: bool = False) -> None:
        (root / "reports").mkdir(parents=True)
        (root / "results").mkdir()
        (root / "contest_manifest.json").write_text(
            json.dumps({"project_schema_version": 3, "contest": "CUMCM", "year": 2026}),
            encoding="utf-8",
        )
        evidence_files: dict[str, Path] = {}
        for problem in "ABC":
            for suffix, content in (
                ("evidence.txt", f"synthetic evidence {problem}"),
                ("baseline.txt", f"synthetic baseline {problem}"),
                ("closure.md", f"synthetic closure {problem}"),
                ("fallback.md", f"synthetic fallback {problem}"),
            ):
                path = root / "results" / f"{problem.lower()}-{suffix}"
                path.write_text(content, encoding="utf-8")
                evidence_files[f"{problem}-{suffix}"] = path
            figure = root / "results" / f"{problem.lower()}.png"
            figure.write_bytes(f"synthetic figure {problem}".encode())
            evidence_files[f"{problem}-figure"] = figure

        screening_fields = [
            "problem_id", "screening_minutes", "micro_baseline_minutes",
            "preliminary_score", "deep_trial_selected", "elimination_reason",
            "deep_trial_budget_minutes", "deep_trial_elapsed_minutes",
            "task_families", "required_model_families", "attachment_state",
            "semantic_risk", "expected_deliverables", "evidence_locator",
            "evidence_sha256", "early_failure_type", "timing_exception", "status",
        ]
        tag_map = {
            "A": ("statistics;optimization", "statistics;optimization"),
            "B": ("simulation;graph_network", "simulation;graph_network"),
            "C": ("forecasting;statistics", "forecasting;statistics"),
        }
        screening_rows = []
        for problem in "ABC":
            path = evidence_files[f"{problem}-evidence.txt"]
            screening_rows.append(
                {
                    "problem_id": problem, "screening_minutes": 15,
                    "micro_baseline_minutes": 30,
                    "preliminary_score": {"A": 90, "B": 75, "C": 55}[problem],
                    "deep_trial_selected": "yes" if problem in "AB" else "no",
                    "elimination_reason": "not_applicable" if problem in "AB" else "lower preliminary closure evidence",
                    "deep_trial_budget_minutes": 90 if problem in "AB" else 0,
                    "deep_trial_elapsed_minutes": 88 if problem == "A" else 90 if problem == "B" else 0,
                    "task_families": tag_map[problem][0],
                    "required_model_families": tag_map[problem][1],
                    "attachment_state": "parsed", "semantic_risk": "controlled",
                    "expected_deliverables": "quantified answer and validation figure",
                    "evidence_locator": path.relative_to(root).as_posix(),
                    "evidence_sha256": digest(path), "early_failure_type": "none",
                    "timing_exception": "", "status": "verified",
                }
            )
        write_csv(root / "reports" / "problem_screening.csv", screening_fields, screening_rows)

        evidence_fields = [
            "problem_id", "criterion", "rating", "evidence_locator", "evidence_sha256",
            "observation_type", "observation", "status",
        ]
        ratings = {
            "A": [4, 4, 4, 3, 4, 4, 3],
            "B": [3, 3, 3, 3, 3, 3, 3],
            "C": [2, 2, 2, 2, 2, 3, 2],
        }
        evidence_rows = []
        for problem in "ABC":
            path = evidence_files[f"{problem}-evidence.txt"]
            for criterion, rating in zip(CRITERIA, ratings[problem]):
                evidence_rows.append(
                    {
                        "problem_id": problem, "criterion": criterion, "rating": rating,
                        "evidence_locator": path.relative_to(root).as_posix(),
                        "evidence_sha256": digest(path),
                        "observation_type": "strength" if rating >= 3 else "weakness",
                        "observation": f"Synthetic {criterion} observation for {problem}",
                        "status": "verified",
                    }
                )
        write_csv(root / "reports" / "problem_selection_evidence.csv", evidence_fields, evidence_rows)

        audition_fields = [
            "problem_id", "attachment_status", "attachment_evidence",
            "attachment_parse_command", "baseline_command", "baseline_result",
            "baseline_elapsed_hours", "paper_figure", "subproblem_closure_evidence",
            "fallback_route", "fallback_evidence", "subproblem_closure_risk",
            "result_verifiability", "upgrade_headroom", "team_fit",
            "writing_visual_potential", "fatal_risk", "score", "status",
        ]
        audition_rows = []
        for problem, levels in {
            "A": ("low", "high", "high", "high", "high"),
            "B": ("medium", "medium", "medium", "medium", "medium"),
            "C": ("high", "low", "medium", "low", "medium"),
        }.items():
            audition_rows.append(
                {
                    "problem_id": problem, "attachment_status": "verified",
                    "attachment_evidence": evidence_files[f"{problem}-evidence.txt"].relative_to(root).as_posix(),
                    "attachment_parse_command": f"python code/parse_{problem.lower()}.py",
                    "baseline_command": f"python code/baseline_{problem.lower()}.py",
                    "baseline_result": evidence_files[f"{problem}-baseline.txt"].relative_to(root).as_posix(),
                    "baseline_elapsed_hours": 1.5,
                    "paper_figure": evidence_files[f"{problem}-figure"].relative_to(root).as_posix(),
                    "subproblem_closure_evidence": evidence_files[f"{problem}-closure.md"].relative_to(root).as_posix(),
                    "fallback_route": f"simplified {problem} baseline",
                    "fallback_evidence": evidence_files[f"{problem}-fallback.md"].relative_to(root).as_posix(),
                    "subproblem_closure_risk": levels[0], "result_verifiability": levels[1],
                    "upgrade_headroom": levels[2], "team_fit": levels[3],
                    "writing_visual_potential": levels[4], "fatal_risk": "none",
                    "score": 100 if problem == "A" else 50 if problem == "B" else 25,
                    "status": "verified",
                }
            )
        write_csv(root / "reports" / "problem_audition.csv", audition_fields, audition_rows)
        weights = {
            "schema_version": 1, "minimum_selected_win_rate": 0.75,
            "recorded_score_tolerance": 1.0,
            "base_weights": {
                "subproblem_closure_risk": 0.30, "result_verifiability": 0.25,
                "upgrade_headroom": 0.15, "team_fit": 0.20,
                "writing_visual_potential": 0.10,
            },
            "sensitivity_scenarios": [
                {"name": "closure_first", "weights": {"subproblem_closure_risk": 0.45, "result_verifiability": 0.20, "upgrade_headroom": 0.10, "team_fit": 0.15, "writing_visual_potential": 0.10}},
                {"name": "evidence_first", "weights": {"subproblem_closure_risk": 0.20, "result_verifiability": 0.40, "upgrade_headroom": 0.10, "team_fit": 0.20, "writing_visual_potential": 0.10}},
            ],
        }
        (root / "reports" / "problem_audition_weights.json").write_text(json.dumps(weights), encoding="utf-8")
        (root / "reports" / "problem_selection.json").write_text(
            json.dumps({"schema_version": 2, "selected_problem": "", "selection_hour": None, "rationale": "", "selection_override": None, "override": None}),
            encoding="utf-8",
        )
        kernel = root / "reports" / "kernel-regression-stdlib.json"
        kernel.write_text(json.dumps({"schema_version": 1, "status": "PASS", "kernel_count": 5}), encoding="utf-8")
        self.run_script("create_ai_capability_snapshot.py", "--project-dir", str(root))

        write_csv(root / "reports" / "problem_selection_calibration.csv", CALIBRATION_FIELDS, [])
        prior = {
            "schema_version": 1, "status": "pending", "source_url": "",
            "source_snapshot": "", "source_sha256": "", "retrieved_at": None,
            "competition_scope": "CUMCM", "applicable_years": [],
            "applies_to_problem_types": ["A", "B", "C"],
            "population_definition": "synthetic submitted-team cohort",
            "denominator_definition": "all synthetic cases in the declared cohort",
            "outcome_definition": "mutually_exclusive_highest_award",
            "category_counts": {outcome: 0 for outcome in ("national_first", "national_second", "provincial_award", "no_award")},
            "effective_strength": 8, "reviewer_status": "pending",
        }
        if calibrated:
            source = root / "reports" / "public-prior-source.txt"
            source.write_text("Synthetic public statistics fixture", encoding="utf-8")
            prior.update(
                status="verified", source_url="https://example.invalid/synthetic-public-prior",
                source_snapshot="reports/public-prior-source.txt", source_sha256=digest(source),
                retrieved_at="2026-08-23", applicable_years=[2022, 2023, 2024],
                category_counts={"national_first": 10, "national_second": 20, "provincial_award": 40, "no_award": 30},
                reviewer_status="verified",
            )
            outcomes = ["national_first", "national_second", "provincial_award", "no_award"]
            rows = []
            for index in range(15):
                row: dict[str, object] = {
                    "case_id": f"synthetic-{index:02d}", "year": 2022 + index % 3,
                    "task_family_tags": "statistics;optimization;simulation;graph_network;forecasting",
                    "ai_profile_version": "2026.08.23", "composite_score": 70 + index % 10,
                    "selected_problem_type": "ABC"[index % 3], "award_label": outcomes[index % 4],
                    "evidence_sha256": hashlib.sha256(f"case-{index}".encode()).hexdigest(),
                    "status": "verified",
                }
                row.update({f"{criterion}_rating": 3 for criterion in CRITERIA})
                rows.append(row)
            write_csv(root / "reports" / "problem_selection_calibration.csv", CALIBRATION_FIELDS, rows)
        (root / "reports" / "public_award_prior.json").write_text(json.dumps(prior), encoding="utf-8")

    def test_core_scoring_and_probability_are_deterministic(self) -> None:
        self.assertEqual(combine_ai_fit(2, 4), 3.4)
        ratings = {
            "A": {criterion: 4.0 for criterion in CRITERIA},
            "B": {criterion: 2.0 for criterion in CRITERIA},
            "C": {criterion: None for criterion in CRITERIA},
        }
        scores, summary = scenario_analysis(ratings)
        self.assertEqual(scores["base"]["A"], 100.0)
        self.assertEqual(scores["base"]["C"], 0.0)
        self.assertEqual(summary["A"]["scenario_win_rate"], 1.0)
        self.assertAlmostEqual(effective_sample_size([1] * 12), 12.0)
        alpha = {"national_first": 2, "national_second": 3, "provincial_award": 4, "no_award": 5}
        first = dirichlet_summary(alpha, 42, draws=1000)
        second = dirichlet_summary(alpha, 42, draws=1000)
        self.assertEqual(first, second)
        self.assertAlmostEqual(sum(item["mean"] for item in first.values()), 1.0)
        self.assertTrue(all(item["lower_80"] <= item["mean"] <= item["upper_80"] for item in first.values()))

    def test_insufficient_calibration_omits_percentages_but_ranks(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.make_fixture(root)
            self.run_script("recommend_problem_selection.py", "--project-dir", str(root))
            report = json.loads((root / "reports" / "problem_selection_recommendation.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "PASS", report)
            self.assertEqual(report["recommended_problem"], "A")
            self.assertEqual(report["confidence"], "high")
            self.assertEqual(report["probability_calibration"]["status"], "INSUFFICIENT_EVIDENCE")
            self.assertNotIn("%", (root / "reports" / "problem_selection_recommendation.md").read_text(encoding="utf-8"))

    def test_valid_local_calibration_yields_four_outcome_intervals(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.make_fixture(root, calibrated=True)
            self.run_script("recommend_problem_selection.py", "--project-dir", str(root))
            path = root / "reports" / "problem_selection_recommendation.json"
            first = json.loads(path.read_text(encoding="utf-8"))["probability_calibration"]
            self.assertEqual(first["status"], "AVAILABLE", first)
            self.run_script("recommend_problem_selection.py", "--project-dir", str(root))
            second = json.loads(path.read_text(encoding="utf-8"))["probability_calibration"]
            self.assertEqual(first, second)
            for problem in "ABC":
                distribution = first["candidate_summaries"][problem]["distribution"]
                self.assertEqual(set(distribution), {"national_first", "national_second", "provincial_award", "no_award"})
                self.assertAlmostEqual(sum(item["mean"] for item in distribution.values()), 1.0)
                self.assertGreaterEqual(first["candidate_summaries"][problem]["effective_local_sample_size"], 12)

    def test_timing_unfairness_caps_confidence_at_limited(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.make_fixture(root)
            path = root / "reports" / "problem_screening.csv"
            with path.open(encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                fields, rows = list(reader.fieldnames or []), list(reader)
            rows[0]["micro_baseline_minutes"] = "40"
            write_csv(path, fields, rows)
            self.run_script("recommend_problem_selection.py", "--project-dir", str(root), expect=2)
            report = json.loads((root / "reports" / "problem_selection_recommendation.json").read_text(encoding="utf-8"))
            self.assertFalse(report["timing_fair"])
            self.assertEqual(report["confidence"], "LIMITED")
            self.assertTrue(any("20%" in item or "30-minute" in item for item in report["timing_findings"]))

    def test_zero_deep_trial_elapsed_time_cannot_pass_fairness(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.make_fixture(root)
            path = root / "reports" / "problem_screening.csv"
            with path.open(encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                fields, rows = list(reader.fieldnames or []), list(reader)
            rows[0]["deep_trial_elapsed_minutes"] = "0"
            write_csv(path, fields, rows)
            self.run_script("recommend_problem_selection.py", "--project-dir", str(root), expect=2)
            report = json.loads((root / "reports" / "problem_selection_recommendation.json").read_text(encoding="utf-8"))
            self.assertFalse(report["timing_fair"])
            self.assertEqual(report["confidence"], "LIMITED")
            self.assertTrue(any("less than 80%" in item for item in report["timing_findings"]))

    def test_unknown_observations_do_not_satisfy_supported_evidence_minimum(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.make_fixture(root)
            path = root / "reports" / "problem_selection_evidence.csv"
            with path.open(encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                fields, rows = list(reader.fieldnames or []), list(reader)
            for row in rows:
                if row["problem_id"] == "C":
                    row["rating"] = "unknown"
                    row["observation_type"] = "unknown"
            write_csv(path, fields, rows)
            self.run_script("recommend_problem_selection.py", "--project-dir", str(root), expect=2)
            report = json.loads((root / "reports" / "problem_selection_recommendation.json").read_text(encoding="utf-8"))
            self.assertEqual(report["candidates"]["C"]["supported_observation_count"], 0)
            self.assertTrue(any("C has fewer than three" in item for item in report["warnings"]))
            markdown = (root / "reports" / "problem_selection_recommendation.md").read_text(encoding="utf-8")
            self.assertIn("未知项不计入", markdown)

    def test_close_scores_produce_co_leaders_and_fatal_risk_excludes_default(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.make_fixture(root)
            evidence_path = root / "reports" / "problem_selection_evidence.csv"
            with evidence_path.open(encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                fields, rows = list(reader.fieldnames or []), list(reader)
            for row in rows:
                if row["problem_id"] == "A":
                    row["rating"] = "3"
            write_csv(evidence_path, fields, rows)
            self.run_script("recommend_problem_selection.py", "--project-dir", str(root))
            report = json.loads((root / "reports" / "problem_selection_recommendation.json").read_text(encoding="utf-8"))
            self.assertEqual(report["co_leading_problems"], ["A", "B"])
            self.assertIsNone(report["recommended_problem"])

            audition_path = root / "reports" / "problem_audition.csv"
            with audition_path.open(encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                audition_fields, audition_rows = list(reader.fieldnames or []), list(reader)
            audition_rows[0]["fatal_risk"] = "unresolved attachment ambiguity"
            write_csv(audition_path, audition_fields, audition_rows)
            self.run_script("recommend_problem_selection.py", "--project-dir", str(root))
            report = json.loads((root / "reports" / "problem_selection_recommendation.json").read_text(encoding="utf-8"))
            self.assertNotEqual(report.get("recommended_problem"), "A")
            self.assertNotIn("A", report.get("co_leading_problems", []))

    def test_stale_snapshot_suppresses_calibrated_percentages(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.make_fixture(root, calibrated=True)
            (root / "reports" / "kernel-regression-stdlib.json").write_text(
                json.dumps({"schema_version": 1, "status": "PASS", "kernel_count": 4}),
                encoding="utf-8",
            )
            self.run_script("recommend_problem_selection.py", "--project-dir", str(root), expect=2)
            report = json.loads((root / "reports" / "problem_selection_recommendation.json").read_text(encoding="utf-8"))
            self.assertEqual(report["probability_calibration"]["status"], "INSUFFICIENT_EVIDENCE")
            self.assertTrue(any("snapshot" in item.lower() for item in report["probability_calibration"]["failed_gates"]))

    def test_stale_public_prior_suppresses_only_probability_layer(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.make_fixture(root, calibrated=True)
            prior_path = root / "reports" / "public_award_prior.json"
            prior = json.loads(prior_path.read_text(encoding="utf-8"))
            prior["retrieved_at"] = "2020-01-01"
            prior_path.write_text(json.dumps(prior), encoding="utf-8")
            self.run_script("recommend_problem_selection.py", "--project-dir", str(root))
            report = json.loads((root / "reports" / "problem_selection_recommendation.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["recommended_problem"], "A")
            self.assertEqual(report["probability_calibration"]["status"], "INSUFFICIENT_EVIDENCE")
            self.assertTrue(any("stale" in item for item in report["probability_calibration"]["failed_gates"]))

    def test_absolute_evidence_locator_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.make_fixture(root)
            path = root / "reports" / "problem_screening.csv"
            with path.open(encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                fields, rows = list(reader.fieldnames or []), list(reader)
            rows[0]["evidence_locator"] = "C:/private/current-problem.txt"
            write_csv(path, fields, rows)
            self.run_script("recommend_problem_selection.py", "--project-dir", str(root), expect=1)
            report = json.loads((root / "reports" / "problem_selection_recommendation.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "FAIL")
            self.assertTrue(any("unsafe" in item for item in report["errors"]))

    def test_confirmation_hash_and_staleness_bind_the_h6_lock(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.make_fixture(root)
            self.run_script("recommend_problem_selection.py", "--project-dir", str(root))
            self.run_script(
                "record_problem_selection_confirmation.py", "--project-dir", str(root),
                "--selected-problem", "A", "--selection-hour", "5.75",
                "--rationale", "A has the strongest verified closure and scenario stability",
            )
            out = root / "reports" / "problem_audition_verification.json"
            self.run_script("verify_problem_audition.py", "--project-dir", str(root), "--out", str(out))
            (root / "results" / "a-evidence.txt").write_text("changed after confirmation", encoding="utf-8")
            self.run_script(
                "verify_problem_audition.py", "--project-dir", str(root), "--out", str(out), expect=1
            )
            failed = json.loads(out.read_text(encoding="utf-8"))
            self.assertTrue(any("stale" in item for item in failed["errors"]))

    def test_schema3_ai_only_recommendation_is_not_overruled_by_legacy_team_fit(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.make_fixture(root)
            audition_path = root / "reports" / "problem_audition.csv"
            with audition_path.open(encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                fields, rows = list(reader.fieldnames or []), list(reader)
            for row in rows:
                if row["problem_id"] == "A":
                    row.update(
                        subproblem_closure_risk="high", result_verifiability="low",
                        upgrade_headroom="low", team_fit="low",
                        writing_visual_potential="low", score="0",
                    )
                elif row["problem_id"] == "B":
                    row.update(
                        subproblem_closure_risk="low", result_verifiability="high",
                        upgrade_headroom="high", team_fit="high",
                        writing_visual_potential="high", score="100",
                    )
            write_csv(audition_path, fields, rows)
            self.run_script("recommend_problem_selection.py", "--project-dir", str(root))
            recommendation = json.loads(
                (root / "reports" / "problem_selection_recommendation.json").read_text(encoding="utf-8")
            )
            self.assertEqual(recommendation["recommended_problem"], "A")
            self.run_script(
                "record_problem_selection_confirmation.py", "--project-dir", str(root),
                "--selected-problem", "A", "--selection-hour", "5.5",
                "--rationale", "AI-only evidence recommendation",
            )
            out = root / "reports" / "problem_audition_verification.json"
            self.run_script("verify_problem_audition.py", "--project-dir", str(root), "--out", str(out))
            verified = json.loads(out.read_text(encoding="utf-8"))
            self.assertFalse(verified["legacy_weight_ranking_enforced"])
            self.assertEqual(verified["selection_exception_reasons"], [])

    def test_nonrecommended_confirmation_requires_existing_selection_exception(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.make_fixture(root)
            self.run_script("recommend_problem_selection.py", "--project-dir", str(root))
            self.run_script(
                "record_problem_selection_confirmation.py", "--project-dir", str(root),
                "--selected-problem", "B", "--selection-hour", "5.8",
                "--rationale", "User deliberately selects B after reviewing the local report",
            )
            out = root / "reports" / "problem_audition_verification.json"
            self.run_script("verify_problem_audition.py", "--project-dir", str(root), "--out", str(out), expect=1)
            selection_path = root / "reports" / "problem_selection.json"
            selection = json.loads(selection_path.read_text(encoding="utf-8"))
            selection["selection_override"] = {
                "type": "selection_exception", "reason": "documented domain judgment",
                "evidence": "results/b-evidence.txt", "authorized_by": "team",
                "exceptions": ["not_recommended_by_engine", "not_base_winner", "low_scenario_win_rate"],
            }
            selection_path.write_text(json.dumps(selection), encoding="utf-8")
            self.run_script("verify_problem_audition.py", "--project-dir", str(root), "--out", str(out))

    def test_confirmation_cannot_predate_recommendation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.make_fixture(root)
            self.run_script("recommend_problem_selection.py", "--project-dir", str(root))
            self.run_script(
                "record_problem_selection_confirmation.py", "--project-dir", str(root),
                "--selected-problem", "A", "--selection-hour", "5.5",
                "--rationale", "verified synthetic evidence",
            )
            selection_path = root / "reports" / "problem_selection.json"
            selection = json.loads(selection_path.read_text(encoding="utf-8"))
            selection["confirmation"]["recorded_at_utc"] = "2000-01-01T00:00:00+00:00"
            selection_path.write_text(json.dumps(selection), encoding="utf-8")
            out = root / "reports" / "problem_audition_verification.json"
            self.run_script("verify_problem_audition.py", "--project-dir", str(root), "--out", str(out), expect=1)
            failed = json.loads(out.read_text(encoding="utf-8"))
            self.assertTrue(any("before recommendation" in item for item in failed["errors"]))

    def test_standard_and_strict_selection_graphs_are_staged(self) -> None:
        expected = [
            "run-problem-selection-kernel-regression",
            "create-ai-capability-snapshot",
            "recommend-problem-selection",
        ]
        for profile_name in ("standard", "strict"):
            profile = load_profile(profile_name)
            self.assertEqual(resolve_nodes(profile, "selection"), expected)

    def test_standard_selection_graph_runs_end_to_end_on_synthetic_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.make_fixture(root)
            self.run_script(
                "contestctl.py", "run", "--project-dir", str(root),
                "--phase", "selection", "--profile", "standard",
            )
            workflow = json.loads((root / "reports" / "workflow_selection.json").read_text(encoding="utf-8"))
            self.assertEqual(workflow["status"], "PASS", workflow)
            self.assertEqual([item["node"] for item in workflow["nodes"]], [
                "run-problem-selection-kernel-regression",
                "create-ai-capability-snapshot",
                "recommend-problem-selection",
            ])
            recommendation = json.loads(
                (root / "reports" / "problem_selection_recommendation.json").read_text(encoding="utf-8")
            )
            self.assertTrue(recommendation["requires_user_confirmation"])
            self.assertEqual(recommendation["recommended_problem"], "A")
            summary = self.run_script(
                "contestctl.py", "summary", "--project-dir", str(root), "--format", "json"
            )
            self.assertEqual(json.loads(summary.stdout)["phase"], "selection")


if __name__ == "__main__":
    unittest.main()
