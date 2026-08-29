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


def md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Cumcm2026ComplianceHardeningTests(unittest.TestCase):
    def run_script(self, name: str, *args: str, expect: int = 0) -> dict[str, object]:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / name), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(result.returncode, expect, result.stdout + result.stderr)
        return json.loads(Path(args[-1]).read_text(encoding="utf-8"))

    def test_live_current_problem_platform_browsing_is_forbidden(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            reports = root / "reports"
            reports.mkdir()
            fields = [
                "action_id", "mode", "action_type", "purpose", "destination",
                "contains_current_contest_material", "current_problem_related",
                "destination_category", "privacy_ambiguity", "user_decision",
                "classification_evidence", "evidence", "status",
            ]
            base = {
                "action_id": "n1", "mode": "live", "action_type": "browse",
                "purpose": "inspect discussion", "destination": "github.com/example/repo",
                "contains_current_contest_material": "no",
                "current_problem_related": "yes",
                "destination_category": "communication_platform",
                "privacy_ambiguity": "no", "user_decision": "approved",
                "classification_evidence": "team classified destination and subject",
                "evidence": "reports/online_actions.csv", "status": "declared",
            }
            with (reports / "online_actions.csv").open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerow(base)
            out = reports / "online_actions_verification.json"
            payload = self.run_script(
                "verify_online_actions.py", "--project-dir", str(root), "--out", str(out), expect=1
            )
            self.assertTrue(any("current-problem" in item for item in payload["errors"]))

            base.update(action_id="n1b", destination_category="official")
            with (reports / "online_actions.csv").open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerow(base)
            payload = self.run_script(
                "verify_online_actions.py", "--project-dir", str(root), "--out", str(out), expect=1
            )
            self.assertTrue(any("known communication platform" in item for item in payload["errors"]))

            base.update(
                action_id="n2", purpose="verify official rules", destination="www.mcm.edu.cn",
                current_problem_related="no", destination_category="official",
                user_decision="not_required",
            )
            with (reports / "online_actions.csv").open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerow(base)
            payload = self.run_script(
                "verify_online_actions.py", "--project-dir", str(root), "--out", str(out)
            )
            self.assertEqual(payload["status"], "PASS")

            base.update(
                action_id="n3", destination="unclassified.example",
                current_problem_related="uncertain", destination_category="uncertain",
                privacy_ambiguity="yes", user_decision="pending",
            )
            with (reports / "online_actions.csv").open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerow(base)
            payload = self.run_script(
                "verify_online_actions.py", "--project-dir", str(root), "--out", str(out), expect=1
            )
            self.assertTrue(any("ask the user" in item for item in payload["errors"]))

    def test_submission_md5_lock_uses_actual_file_bytes_and_deadline(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper").mkdir()
            (root / "reports").mkdir()
            paper = root / "paper" / "main.pdf"
            paper.write_bytes(b"frozen paper")
            evidence = root / "reports" / "official-client-md5.txt"
            evidence.write_text(md5(paper), encoding="utf-8")
            ledger = {
                "schema_version": 1,
                "profile": "cumcm-2026",
                "artifacts": [{
                    "role": "paper", "path": "paper/main.pdf",
                    "recorded_md5": md5(paper),
                    "md5_generated_at": "2026-09-13T19:40:00+08:00",
                    "md5_submitted_at": "2026-09-13T19:50:00+08:00",
                    "evidence": "reports/official-client-md5.txt",
                }],
            }
            ledger_path = root / "reports" / "submission_md5_lock.json"
            ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
            out = root / "reports" / "submission_md5_verification.json"
            payload = self.run_script(
                "verify_submission_md5_lock.py", "--project-dir", str(root),
                "--ledger", str(ledger_path), "--out", str(out)
            )
            self.assertEqual(payload["status"], "PASS")
            self.assertEqual(payload["artifacts"][0]["actual_md5"], md5(paper))
            self.assertEqual(payload["artifacts"][0]["actual_sha256"], sha256(paper))

            paper.write_bytes(b"changed after hash")
            payload = self.run_script(
                "verify_submission_md5_lock.py", "--project-dir", str(root),
                "--ledger", str(ledger_path), "--out", str(out), expect=1
            )
            self.assertTrue(any("MD5 mismatch" in item for item in payload["errors"]))

            ledger["artifacts"][0]["recorded_md5"] = md5(paper)
            ledger["artifacts"][0]["md5_submitted_at"] = "2026-09-13T20:01:00+08:00"
            ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
            payload = self.run_script(
                "verify_submission_md5_lock.py", "--project-dir", str(root),
                "--ledger", str(ledger_path), "--out", str(out), expect=1
            )
            self.assertTrue(any("deadline" in item for item in payload["errors"]))

    def test_submission_md5_without_official_evidence_is_limited(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper").mkdir()
            (root / "reports").mkdir()
            (root / "paper" / "main.pdf").write_bytes(b"paper")
            ledger = {
                "schema_version": 1, "profile": "cumcm-2026",
                "artifacts": [{"role": "paper", "path": "paper/main.pdf"}],
            }
            ledger_path = root / "reports" / "submission_md5_lock.json"
            ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
            out = root / "reports" / "submission_md5_verification.json"
            payload = self.run_script(
                "verify_submission_md5_lock.py", "--project-dir", str(root),
                "--ledger", str(ledger_path), "--out", str(out), expect=2
            )
            self.assertEqual(payload["status"], "LIMITED")

    def test_official_similarity_metrics_enforce_25_percent_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper").mkdir()
            (root / "reports").mkdir()
            paper = root / "paper" / "main.pdf"
            paper.write_bytes(b"paper")
            evidence = root / "reports" / "cnki-report.pdf"
            evidence.write_bytes(b"report")
            ledger = {
                "schema_version": 1, "profile": "cumcm-2026",
                "provider": "Tongfang/CNKI", "paper_path": "paper/main.pdf",
                "paper_sha256": sha256(paper), "report_time": "2026-09-13T18:00:00+08:00",
                "evidence": "reports/cnki-report.pdf", "reviewer": "student-1",
                "metrics": {
                    "overall_text_copy_ratio": 0.249,
                    "excluding_own_published_ratio": 0.10,
                },
            }
            ledger_path = root / "reports" / "similarity_risk.json"
            ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
            out = root / "reports" / "similarity_risk_verification.json"
            payload = self.run_script(
                "verify_similarity_risk.py", "--project-dir", str(root),
                "--ledger", str(ledger_path), "--out", str(out)
            )
            self.assertEqual(payload["status"], "PASS")

            ledger["metrics"]["overall_text_copy_ratio"] = 0.25
            ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
            payload = self.run_script(
                "verify_similarity_risk.py", "--project-dir", str(root),
                "--ledger", str(ledger_path), "--out", str(out), expect=1
            )
            self.assertTrue(any("threshold" in item for item in payload["errors"]))

            ledger["metrics"]["overall_text_copy_ratio"] = 0.10
            ledger["evidence"] = ""
            ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
            payload = self.run_script(
                "verify_similarity_risk.py", "--project-dir", str(root),
                "--ledger", str(ledger_path), "--out", str(out), expect=2
            )
            self.assertEqual(payload["status"], "LIMITED")

    def test_rules_and_readmes_state_precise_boundaries(self) -> None:
        rules = (ROOT / "references" / "embedded" / "cumcm-2026-rules.md").read_text(encoding="utf-8")
        self.assertIn("Physical paper sequence", rules)
        self.assertIn("Electronic paper submission", rules)
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        readme_zh = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        self.assertNotIn("internet search is allowed", readme.lower())
        self.assertNotIn("允许互联网搜索", readme_zh)
        self.assertIn("communication platforms", readme)
        self.assertIn("交流平台", readme_zh)

    def test_strict_freeze_adds_checks_only_for_cumcm_2026(self) -> None:
        sys.path.insert(0, str(SCRIPTS))
        import contest_orchestration

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "reports").mkdir()
            (root / "contest_manifest.json").write_text(
                json.dumps({"submission_profile": "cumcm-2026"}), encoding="utf-8"
            )
            payload = contest_orchestration.run_workflow(
                root, "freeze", "strict", None, dry_run=True
            )
            nodes = {item["node"] for item in payload["nodes"]}
            self.assertIn("verify-submission-md5-lock", nodes)
            self.assertIn("verify-official-similarity-risk", nodes)

            (root / "contest_manifest.json").write_text(
                json.dumps({"submission_profile": "mcm-icm-current"}), encoding="utf-8"
            )
            payload = contest_orchestration.run_workflow(
                root, "freeze", "strict", None, dry_run=True
            )
            nodes = {item["node"] for item in payload["nodes"]}
            self.assertNotIn("verify-submission-md5-lock", nodes)
            self.assertNotIn("verify-official-similarity-risk", nodes)


if __name__ == "__main__":
    unittest.main()
