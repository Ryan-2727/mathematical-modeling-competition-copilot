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
        self.assertEqual(profile["freshness_checkpoints"], lock_contest_rules.CUMCM_2026_CHECKPOINTS)
        self.assertEqual(set(profile["source_urls"]), lock_contest_rules.CUMCM_2026_SOURCE_ROLES)
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
        source_specs = [
            ("official_notice", "notice.pdf"),
            ("paper_format", "format.html"),
            ("contest_rules", "rules.html"),
            ("ai_policy", "ai.html"),
        ]
        sources = []
        for role, name in source_specs:
            path = root / "rules" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(role, encoding="utf-8")
            sources.append(
                {
                    "role": role,
                    "url": f"https://www.mcm.edu.cn/{name}",
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
            "valid_through": "2026-09-13",
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
                "reports/problem_selection.json",
                "reports/training_runs.csv",
                "reports/training_defects.csv",
                "reports/online_actions.csv",
            ):
                self.assertTrue((root / relative).is_file(), relative)
            milestones = (root / "reports" / "milestones.csv").read_text(encoding="utf-8")
            self.assertIn("selection-lock,6", milestones)
            self.assertIn("receipt-lock,74", milestones)

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

    def test_problem_audition_requires_executable_evidence_and_h6_lock(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "results").mkdir()
            (root / "results" / "a.txt").write_text("baseline A", encoding="utf-8")
            (root / "results" / "b.txt").write_text("baseline B", encoding="utf-8")
            fields = [
                "problem_id", "attachment_status", "attachment_evidence",
                "baseline_command", "baseline_result", "subproblem_closure_risk",
                "result_verifiability", "upgrade_headroom", "team_fit",
                "writing_visual_potential", "fatal_risk", "score", "status",
            ]
            rows = []
            for problem, score in (("A", 86), ("B", 72)):
                rows.append(
                    {
                        "problem_id": problem,
                        "attachment_status": "verified",
                        "attachment_evidence": f"results/{problem.lower()}.txt",
                        "baseline_command": f"python code/{problem.lower()}.py",
                        "baseline_result": f"results/{problem.lower()}.txt",
                        "subproblem_closure_risk": "low",
                        "result_verifiability": "high",
                        "upgrade_headroom": "high",
                        "team_fit": "high",
                        "writing_visual_potential": "high",
                        "fatal_risk": "none",
                        "score": score,
                        "status": "verified",
                    }
                )
            write_csv(root / "reports" / "problem_audition.csv", fields, rows)
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
            self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["status"], "PASS")

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
                "run_id": "r1", "rehearsal_hours": 24, "selection_lock_hour": 5,
                "first_verified_result_hour": 10, "all_subproblem_results_hour": 22,
                "full_draft_hour": "", "strict_freeze_hour": "",
                "submission_rehearsal": "no", "unresolved_vetoes": 0,
                "status": "complete",
            }
            write_csv(root / "reports" / "training_runs.csv", run_fields, [short_run])
            defect_fields = ["run_id", "defect_class", "severity", "evidence", "resolution_status"]
            write_csv(root / "reports" / "training_defects.csv", defect_fields, [])
            out = root / "reports" / "training_readiness.json"
            self.run_script(
                "score_training_readiness.py", "--project-dir", str(root), "--out", str(out), expect=2
            )
            partial = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(partial["status"], "LIMITED")
            self.assertEqual(partial["readiness_state"], "partial")

            full_run = {
                "run_id": "r2", "rehearsal_hours": 74, "selection_lock_hour": 5.5,
                "first_verified_result_hour": 11, "all_subproblem_results_hour": 34,
                "full_draft_hour": 62, "strict_freeze_hour": 69,
                "submission_rehearsal": "yes", "unresolved_vetoes": 0,
                "status": "complete",
            }
            write_csv(root / "reports" / "training_runs.csv", run_fields, [short_run, full_run])
            write_csv(
                root / "reports" / "training_defects.csv",
                defect_fields,
                [
                    {"run_id": "r1", "defect_class": "late_selection", "severity": "major", "evidence": "reports/r1.json", "resolution_status": "resolved"},
                    {"run_id": "r2", "defect_class": "late_selection", "severity": "minor", "evidence": "reports/r2.json", "resolution_status": "resolved"},
                ],
            )
            self.run_script(
                "score_training_readiness.py", "--project-dir", str(root), "--out", str(out)
            )
            ready = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(ready["status"], "PASS", ready)
            self.assertEqual(ready["readiness_state"], "ready")
            self.assertEqual(ready["repeated_defects"]["late_selection"], 2)

    def test_live_online_actions_never_upload_and_pause_on_ambiguity(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            fields = [
                "action_id", "mode", "action_type", "purpose", "destination",
                "contains_current_contest_material", "privacy_ambiguity",
                "user_decision", "evidence", "status",
            ]
            safe_search = {
                "action_id": "n1", "mode": "live", "action_type": "search",
                "purpose": "official rule check", "destination": "www.mcm.edu.cn",
                "contains_current_contest_material": "no", "privacy_ambiguity": "no",
                "user_decision": "not_required", "evidence": "rules.lock.json",
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


if __name__ == "__main__":
    unittest.main()
