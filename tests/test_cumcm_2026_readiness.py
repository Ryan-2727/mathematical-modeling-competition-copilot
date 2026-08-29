from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import lock_contest_rules
from contest_profile import load_contest_profile


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


class Cumcm2026ReadinessTests(unittest.TestCase):
    def test_bundled_profile_is_the_executable_2026_source(self) -> None:
        profile = load_contest_profile("cumcm-2026")
        self.assertEqual(profile["competition_start"], "2026-09-10T18:00:00+08:00")
        self.assertEqual(profile["competition_end"], "2026-09-13T20:00:00+08:00")
        self.assertEqual(profile["registration_deadline"], "2026-09-07T20:00:00+08:00")
        self.assertEqual(profile["hash_deadline"], "2026-09-13T20:00:00+08:00")
        self.assertEqual(profile["upload_open"], "2026-09-13T20:30:00+08:00")
        self.assertEqual(profile["upload_deadline"], "2026-09-14T14:00:00+08:00")
        self.assertEqual(profile["national_similarity_threshold"], 0.25)
        self.assertTrue(profile["live_current_problem_communication_platform_access_forbidden"])
        self.assertEqual(profile["freshness_checkpoints"], lock_contest_rules.CUMCM_2026_CHECKPOINTS)
        self.assertEqual(set(profile["source_urls"]), lock_contest_rules.CUMCM_2026_SOURCE_ROLES)
        self.assertEqual(profile["verified_at"], "2026-08-20")
        self.assertIn("2026年试行", "全国大学生数学建模竞赛人工智能工具使用规定（2026年试行）")
        self.assertIn("fef94648", profile["source_urls"]["ai_policy"])
        self.assertEqual(
            set(profile["source_variants"]["ai_policy"]),
            {"locator", "page", "attachment"},
        )
        rules_text = (ROOT / "references" / "embedded" / "cumcm-2026-rules.md").read_text(encoding="utf-8")
        profiles_text = (ROOT / "references" / "embedded" / "executable-contest-profiles.md").read_text(encoding="utf-8")
        for value in profile["source_urls"].values():
            self.assertIn(value, profiles_text)
        self.assertIn("2026-09-10 18:00", rules_text)
        self.assertIn("2026-09-13 20:00", rules_text)
        self.assertIn("2026-09-07 20:00", rules_text)
        self.assertIn("assets/contest-profiles/cumcm-2026.json", rules_text)
        profile["competition_start"] = "changed"
        self.assertEqual(
            load_contest_profile("cumcm-2026")["competition_start"],
            "2026-09-10T18:00:00+08:00",
        )

    def run_script(
        self, name: str, *args: str, expect: int = 0
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

    def rules_payload(self, root: Path, checked_at: str) -> dict[str, object]:
        profile = load_contest_profile("cumcm-2026")
        sources = []
        for role, variants in profile["source_variants"].items():
            for kind, url in variants.items():
                path = root / "rules" / f"{role}-{kind}.snapshot"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(f"{role}/{kind}", encoding="utf-8")
                sources.append(
                    {
                        "role": role,
                        "kind": kind,
                        "url": url,
                        "snapshot": path.relative_to(root).as_posix(),
                        "sha256": sha256(path),
                    }
                )
        return {
            "schema_version": 2,
            "contest": "CUMCM",
            "year": 2026,
            "profile": "cumcm-2026",
            "created_at_utc": checked_at,
            "valid_through": "2026-09-14",
            "sources": sources,
            "freshness_checkpoints": ["2026-08-11", "2026-09-03", "2026-09-09"],
            "rules": {
                "paper_format": "PDF or Word",
                "paper_size_limit_mb": "20",
                "support_archive": "ZIP or RAR",
                "main_text_page_limit": "30",
                "ai_policy": "two-branch declaration",
                "anonymity": "required",
                "competition_start": "2026-09-10T18:00:00+08:00",
                "competition_end": "2026-09-13T20:00:00+08:00",
                "registration_deadline": "2026-09-07T20:00:00+08:00",
                "hash_deadline": "2026-09-13T20:00:00+08:00",
                "upload_open": "2026-09-13T20:30:00+08:00",
                "upload_deadline": "2026-09-14T14:00:00+08:00",
                "timezone": "Asia/Shanghai",
                "submission_channel": "CNKI competition management system",
            },
        }

    def test_cumcm_2026_initialization_scaffolds_74h_readiness_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "project"
            self.run_script(
                "init_contest.py",
                "--project-dir", str(root),
                "--contest", "CUMCM",
                "--year", "2026",
                "--mode", "training",
            )
            manifest = json.loads((root / "contest_manifest.json").read_text(encoding="utf-8"))
            self.assertIsNone(manifest["ai_mode"])
            self.assertEqual(manifest["contest_duration_hours"], 74)
            for relative in (
                "reports/problem_audition.csv",
                "reports/problem_audition_weights.json",
                "reports/problem_selection.json",
                "reports/problem_screening.csv",
                "reports/problem_selection_evidence.csv",
                "reports/ai_capability_snapshot.json",
                "reports/problem_selection_calibration.csv",
                "reports/public_award_prior.json",
                "reports/problem_selection_recommendation.json",
                "reports/problem_selection_recommendation.md",
                "reports/training_runs.csv",
                "reports/training_defects.csv",
                "reports/training_roles.csv",
                "reports/online_actions.csv",
                "reports/submission_md5_lock.json",
                "reports/similarity_risk.json",
            ):
                self.assertTrue((root / relative).is_file(), relative)
            with (root / "reports" / "problem_screening.csv").open(
                encoding="utf-8", newline=""
            ) as handle:
                self.assertEqual(
                    [row["problem_id"] for row in csv.DictReader(handle)],
                    ["A", "B", "C"],
                )
            milestones = (root / "reports" / "milestones.csv").read_text(encoding="utf-8")
            self.assertIn("selection-lock,6", milestones)
            self.assertIn("hash-lock,74", milestones)
            self.assertIn("upload-open,74.5", milestones)
            self.assertIn("receipt-lock,92", milestones)

    def test_live_initialization_forces_ai_used_and_records_runtime_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "project"
            self.run_script(
                "init_contest.py",
                "--project-dir", str(root),
                "--contest", "CUMCM",
                "--year", "2026",
                "--mode", "live",
                expect=2,
            )
            self.run_script(
                "init_contest.py",
                "--project-dir", str(root),
                "--contest", "CUMCM",
                "--year", "2026",
                "--mode", "live",
                "--ai-tool", "OpenAI Codex",
                "--ai-version", "runtime-recorded-version",
                "--ai-runtime-boundary", "external_service",
            )
            manifest = json.loads(
                (root / "contest_manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["ai_mode"], "used")
            self.assertEqual(manifest["contest_material_ai_access"], "forbidden")
            self.assertEqual(
                manifest["submission_schedule"]["upload_open"],
                "2026-09-13T20:30:00+08:00",
            )
            main_tex = (root / "paper" / "main.tex").read_text(encoding="utf-8")
            self.assertIn(r"\cumcmaiusedtrue", main_tex)
            self.assertNotIn(r"\cumcmaiusedfalse", main_tex)

    def test_rule_lock_enforces_2026_schedule_roles_and_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            current = self.rules_payload(root, "2026-09-09T10:00:00+08:00")
            report = lock_contest_rules.validate_lock(
                root, current, as_of_date=date(2026, 9, 10), mode="live"
            )
            self.assertEqual(report["status"], "PASS", report)
            self.assertEqual(report["latest_due_checkpoint"], "2026-09-09")

            stale = self.rules_payload(root, "2026-08-12T10:00:00+08:00")
            report = lock_contest_rules.validate_lock(
                root, stale, as_of_date=date(2026, 9, 4), mode="precontest"
            )
            self.assertEqual(report["status"], "FAIL")
            self.assertTrue(any("freshness checkpoint" in item for item in report["errors"]))

            missing_role = self.rules_payload(root, "2026-09-09T10:00:00+08:00")
            missing_role["sources"] = missing_role["sources"][:-1]
            report = lock_contest_rules.validate_lock(
                root, missing_role, as_of_date=date(2026, 9, 10), mode="live"
            )
            self.assertEqual(report["status"], "FAIL")
            self.assertTrue(any("source role" in item for item in report["errors"]))

    def test_rule_lock_accepts_noncanonical_windows_project_root(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "nested" / ".." / "project"
            current = self.rules_payload(root, "2026-09-09T10:00:00+08:00")
            report = lock_contest_rules.validate_lock(
                root, current, as_of_date=date(2026, 9, 10), mode="live"
            )
            self.assertEqual(report["status"], "PASS", report)

    def test_rule_lock_uses_effective_date_for_expiration(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            current = self.rules_payload(root, "2026-09-09T10:00:00+08:00")
            report = lock_contest_rules.validate_lock(
                root, current, as_of_date=date(2026, 9, 15), mode="live"
            )
            self.assertEqual(report["status"], "FAIL", report)
            self.assertTrue(any("expired" in item for item in report["errors"]))

    def test_problem_audition_requires_executable_evidence_and_h6_lock(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "results").mkdir()
            (root / "results" / "a.txt").write_text("baseline A", encoding="utf-8")
            (root / "results" / "b.txt").write_text("baseline B", encoding="utf-8")
            for name in ("a.png", "b.png"):
                (root / "results" / name).write_bytes(b"figure")
            for name in ("a-closure.md", "b-closure.md", "a-fallback.md", "b-fallback.md"):
                (root / "results" / name).write_text(name, encoding="utf-8")
            fields = [
                "problem_id", "attachment_status", "attachment_evidence",
                "attachment_parse_command", "baseline_command", "baseline_result",
                "baseline_elapsed_hours", "paper_figure", "subproblem_closure_evidence",
                "fallback_route", "fallback_evidence", "subproblem_closure_risk",
                "result_verifiability", "upgrade_headroom", "team_fit",
                "writing_visual_potential", "fatal_risk", "score", "status",
            ]
            rows = []
            for problem, score in (("A", 100), ("B", 57.5)):
                rows.append(
                    {
                        "problem_id": problem,
                        "attachment_status": "verified",
                        "attachment_evidence": f"results/{problem.lower()}.txt",
                        "attachment_parse_command": f"python code/parse_{problem.lower()}.py",
                        "baseline_command": f"python code/{problem.lower()}.py",
                        "baseline_result": f"results/{problem.lower()}.txt",
                        "baseline_elapsed_hours": 1.5 if problem == "A" else 1.8,
                        "paper_figure": f"results/{problem.lower()}.png",
                        "subproblem_closure_evidence": f"results/{problem.lower()}-closure.md",
                        "fallback_route": "simplified baseline",
                        "fallback_evidence": f"results/{problem.lower()}-fallback.md",
                        "subproblem_closure_risk": "low" if problem == "A" else "medium",
                        "result_verifiability": "high" if problem == "A" else "medium",
                        "upgrade_headroom": "high",
                        "team_fit": "high" if problem == "A" else "medium",
                        "writing_visual_potential": "high",
                        "fatal_risk": "none",
                        "score": score,
                        "status": "verified",
                    }
                )
            write_csv(root / "reports" / "problem_audition.csv", fields, rows)
            weights = {
                "schema_version": 1,
                "minimum_selected_win_rate": 0.75,
                "recorded_score_tolerance": 1.0,
                "base_weights": {
                    "subproblem_closure_risk": 0.30,
                    "result_verifiability": 0.25,
                    "upgrade_headroom": 0.15,
                    "team_fit": 0.20,
                    "writing_visual_potential": 0.10,
                },
                "sensitivity_scenarios": [
                    {"name": "closure_first", "weights": {"subproblem_closure_risk": 0.45, "result_verifiability": 0.20, "upgrade_headroom": 0.10, "team_fit": 0.15, "writing_visual_potential": 0.10}},
                    {"name": "evidence_first", "weights": {"subproblem_closure_risk": 0.20, "result_verifiability": 0.40, "upgrade_headroom": 0.10, "team_fit": 0.20, "writing_visual_potential": 0.10}},
                ],
            }
            (root / "reports" / "problem_audition_weights.json").write_text(
                json.dumps(weights), encoding="utf-8"
            )
            selection = {
                "selected_problem": "A",
                "selection_hour": 5.5,
                "rationale": "best verified baseline and closure risk",
                "override": None,
            }
            (root / "reports" / "problem_selection.json").write_text(
                json.dumps(selection), encoding="utf-8"
            )
            out = root / "reports" / "problem_audition_verification.json"
            self.run_script(
                "verify_problem_audition.py", "--project-dir", str(root), "--out", str(out)
            )
            stable = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(stable["status"], "PASS")
            self.assertEqual(stable["base_winners"], ["A"])
            self.assertEqual(stable["selected_win_rate"], 1.0)
            self.assertEqual(stable["selection_confidence"], "high")

            selection["selected_problem"] = "B"
            selection["rationale"] = "team deliberately accepts lower closure stability"
            (root / "reports" / "problem_selection.json").write_text(
                json.dumps(selection), encoding="utf-8"
            )
            self.run_script(
                "verify_problem_audition.py", "--project-dir", str(root), "--out", str(out), expect=1
            )
            selection["selection_override"] = {
                "type": "selection_exception",
                "reason": "specialized domain experience offsets the scored risk",
                "evidence": "results/b.txt",
                "authorized_by": "team",
                "exceptions": ["not_base_winner", "low_scenario_win_rate"],
            }
            (root / "reports" / "problem_selection.json").write_text(
                json.dumps(selection), encoding="utf-8"
            )
            self.run_script(
                "verify_problem_audition.py", "--project-dir", str(root), "--out", str(out)
            )

            selection["selected_problem"] = "A"
            selection["selection_override"] = None
            selection["selection_hour"] = 6.5
            (root / "reports" / "problem_selection.json").write_text(
                json.dumps(selection), encoding="utf-8"
            )
            self.run_script(
                "verify_problem_audition.py", "--project-dir", str(root), "--out", str(out), expect=1
            )
            selection["override"] = {
                "type": "catastrophic_infeasibility",
                "failed_problem": "B",
                "reason": "attachment cannot be decoded locally",
                "evidence": "results/b.txt",
                "authorized_by": "team",
            }
            (root / "reports" / "problem_selection.json").write_text(
                json.dumps(selection), encoding="utf-8"
            )
            self.run_script(
                "verify_problem_audition.py", "--project-dir", str(root), "--out", str(out)
            )

    def test_training_readiness_distinguishes_partial_and_full_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            run_fields = [
                "run_id", "rehearsal_hours", "selection_lock_hour",
                "first_verified_result_hour", "all_subproblem_results_hour",
                "full_draft_hour", "strict_freeze_hour", "submission_rehearsal",
                "unresolved_vetoes", "status",
            ]
            short_run = {
                "run_id": "r1", "rehearsal_hours": 24, "selection_lock_hour": 6,
                "first_verified_result_hour": 10, "all_subproblem_results_hour": 22,
                "full_draft_hour": "", "strict_freeze_hour": "",
                "submission_rehearsal": "no", "unresolved_vetoes": 0,
                "status": "complete",
            }
            write_csv(root / "reports" / "training_runs.csv", run_fields, [short_run])
            defect_fields = ["run_id", "defect_class", "severity", "evidence", "resolution_status"]
            write_csv(root / "reports" / "training_defects.csv", defect_fields, [])
            role_fields = [
                "run_id", "role", "owner", "planned_complete_hour",
                "actual_complete_hour", "handoff_evidence", "backup_owner", "status",
            ]
            write_csv(root / "reports" / "training_roles.csv", role_fields, [])
            out = root / "reports" / "training_readiness.json"
            self.run_script(
                "score_training_readiness.py", "--project-dir", str(root), "--out", str(out), expect=2
            )
            partial = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(partial["status"], "LIMITED")
            self.assertEqual(partial["readiness_state"], "partial")

            full_run = {
                "run_id": "r2", "rehearsal_hours": 74, "selection_lock_hour": 5.5,
                "first_verified_result_hour": 11, "all_subproblem_results_hour": 23.5,
                "full_draft_hour": 62, "strict_freeze_hour": 69,
                "submission_rehearsal": "yes", "unresolved_vetoes": 0,
                "status": "complete",
            }
            write_csv(root / "reports" / "training_runs.csv", run_fields, [short_run, full_run])
            write_csv(
                root / "reports" / "training_roles.csv",
                role_fields,
                [
                    {"run_id": "r2", "role": role, "owner": f"owner-{role}", "planned_complete_hour": planned, "actual_complete_hour": actual, "handoff_evidence": f"reports/r2-{role}.md", "backup_owner": f"backup-{role}", "status": "complete"}
                    for role, planned, actual in (
                        ("selection", 6, 5.5), ("modeling", 42, 41),
                        ("paper", 64, 62), ("submission", 72, 71),
                    )
                ],
            )
            write_csv(
                root / "reports" / "training_defects.csv",
                defect_fields,
                [
                    {"run_id": "r1", "defect_class": "late_selection", "severity": "major", "evidence": "reports/r1.json", "resolution_status": "resolved"},
                    {"run_id": "r2", "defect_class": "late_selection", "severity": "minor", "evidence": "reports/r2.json", "resolution_status": "resolved"},
                ],
            )
            self.run_script(
                "score_training_readiness.py", "--project-dir", str(root), "--out", str(out), expect=2
            )
            provisional = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(provisional["readiness_state"], "provisional")
            self.assertEqual(provisional["consecutive_full_passes"], 1)

            second_full_run = {
                "run_id": "r3", "rehearsal_hours": 74, "selection_lock_hour": 5,
                "first_verified_result_hour": 10, "all_subproblem_results_hour": 22.5,
                "full_draft_hour": 60, "strict_freeze_hour": 68,
                "submission_rehearsal": "yes", "unresolved_vetoes": 0,
                "status": "complete",
            }
            write_csv(
                root / "reports" / "training_runs.csv",
                run_fields,
                [short_run, full_run, second_full_run],
            )
            write_csv(
                root / "reports" / "training_roles.csv",
                role_fields,
                [
                    {"run_id": run_id, "role": role, "owner": f"owner-{role}", "planned_complete_hour": planned, "actual_complete_hour": actual, "handoff_evidence": f"reports/{run_id}-{role}.md", "backup_owner": f"backup-{role}", "status": "complete"}
                    for run_id, actuals in (
                        ("r2", {"selection": 5.5, "modeling": 41, "paper": 62, "submission": 71}),
                        ("r3", {"selection": 5, "modeling": 40, "paper": 60, "submission": 70}),
                    )
                    for role, planned in (("selection", 6), ("modeling", 42), ("paper", 64), ("submission", 72))
                    for actual in (actuals[role],)
                ],
            )
            write_csv(
                root / "reports" / "training_defects.csv",
                defect_fields,
                [
                    {"run_id": "r1", "defect_class": "late_selection", "severity": "major", "evidence": "reports/r1.json", "resolution_status": "resolved"},
                    {"run_id": "r2", "defect_class": "late_selection", "severity": "major", "evidence": "reports/r2.json", "resolution_status": "open"},
                    {"run_id": "r3", "defect_class": "late_selection", "severity": "minor", "evidence": "reports/r3.json", "resolution_status": "resolved"},
                ],
            )
            self.run_script(
                "score_training_readiness.py", "--project-dir", str(root), "--out", str(out)
            )
            ready = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(ready["status"], "PASS", ready)
            self.assertEqual(ready["readiness_state"], "ready")
            self.assertEqual(ready["consecutive_full_passes"], 2)
            self.assertEqual(ready["repeated_defects"]["late_selection"], 3)
            self.assertEqual(ready["defect_recurrence_counts"]["late_selection"], 2)
            self.assertEqual(ready["reopened_after_resolution"]["late_selection"], ["r2"])
            selection_stats = ready["milestone_statistics"]["selection_lock_hour"]
            self.assertEqual(selection_stats["worst"], 6.0)
            self.assertEqual(selection_stats["p90_nearest_rank"], 6.0)
            self.assertEqual(selection_stats["trend"], "improving")
            self.assertEqual(
                ready["full_rehearsal_role_coverage"]["r3"],
                ["modeling", "paper", "selection", "submission"],
            )
            self.assertLess(ready["owner_bottlenecks"]["owner-paper"]["mean_delay_hours"], 0)

            blocked_roles = [
                {"run_id": run_id, "role": role, "owner": f"owner-{role}", "planned_complete_hour": planned, "actual_complete_hour": actual, "handoff_evidence": f"reports/{run_id}-{role}.md", "backup_owner": f"backup-{role}", "status": "blocked" if run_id == "r3" and role == "submission" else "complete"}
                for run_id, actuals in (
                    ("r2", {"selection": 5.5, "modeling": 41, "paper": 62, "submission": 71}),
                    ("r3", {"selection": 5, "modeling": 40, "paper": 60, "submission": 70}),
                )
                for role, planned in (("selection", 6), ("modeling", 42), ("paper", 64), ("submission", 72))
                for actual in (actuals[role],)
            ]
            write_csv(root / "reports" / "training_roles.csv", role_fields, blocked_roles)
            self.run_script(
                "score_training_readiness.py", "--project-dir", str(root), "--out", str(out), expect=1
            )
            blocked = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(blocked["readiness_state"], "not_ready")
            self.assertEqual(blocked["blocked_role_counts"]["submission"], 1)

    def test_live_online_actions_never_upload_and_pause_on_ambiguity(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            fields = [
                "action_id", "mode", "action_type", "purpose", "destination",
                "contains_current_contest_material", "current_problem_related",
                "destination_category", "privacy_ambiguity", "user_decision",
                "classification_evidence", "evidence", "status",
            ]
            safe_search = {
                "action_id": "n1", "mode": "live", "action_type": "search",
                "purpose": "official rule check", "destination": "www.mcm.edu.cn",
                "contains_current_contest_material": "no", "current_problem_related": "no",
                "destination_category": "official", "privacy_ambiguity": "no",
                "user_decision": "not_required", "evidence": "rules.lock.json",
                "classification_evidence": "official CUMCM domain",
                "status": "declared",
            }
            path = root / "reports" / "online_actions.csv"
            out = root / "reports" / "online_actions_verification.json"
            write_csv(path, fields, [safe_search])
            self.run_script(
                "verify_online_actions.py", "--project-dir", str(root), "--out", str(out)
            )

            ambiguous = dict(safe_search, action_id="n2", privacy_ambiguity="yes", user_decision="pending")
            write_csv(path, fields, [safe_search, ambiguous])
            self.run_script(
                "verify_online_actions.py", "--project-dir", str(root), "--out", str(out), expect=1
            )

            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertTrue(any("ask the user" in item for item in payload["errors"]))

            ambiguous["user_decision"] = "approved"
            write_csv(path, fields, [safe_search, ambiguous])
            self.run_script(
                "verify_online_actions.py", "--project-dir", str(root), "--out", str(out)
            )

            forbidden = dict(
                safe_search,
                action_id="n3",
                action_type="upload",
                contains_current_contest_material="yes",
                privacy_ambiguity="no",
                user_decision="approved",
            )
            write_csv(path, fields, [forbidden])
            self.run_script(
                "verify_online_actions.py", "--project-dir", str(root), "--out", str(out), expect=1
            )

    def test_targeted_bc_model_library_is_complete_and_machine_validated(self) -> None:
        library = ROOT / "assets" / "model-library" / "cumcm-bc-model-cards.json"
        payload = json.loads(library.read_text(encoding="utf-8"))
        self.assertEqual(len(payload["required_archetypes"]), 9)
        self.assertEqual(
            set(payload["required_archetypes"]),
            {card["id"] for card in payload["cards"]},
        )
        self.assertEqual(
            {fit for card in payload["cards"] for fit in card["contest_fit"]},
            {"B", "C"},
        )
        self.run_script("verify_model_library.py")


if __name__ == "__main__":
    unittest.main()
