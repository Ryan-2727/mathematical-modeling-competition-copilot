from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


class ExecutableQualityIntegrationTests(unittest.TestCase):
    def run_script(self, name: str, *args: str, expect: int = 0) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / name), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(result.returncode, expect, result.stdout + result.stderr)

    def test_initializer_and_profiles_route_all_four_improvements(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw) / "数学建模项目"
            self.run_script(
                "init_contest.py",
                "--project-dir",
                str(project),
                "--contest",
                "CUMCM",
                "--year",
                "2026",
                "--mode",
                "training",
            )
            expected = {
                "model_kernel_usage.csv",
                "compute_budget.csv",
                "compute_runs.jsonl",
                "prose_style_exemptions.csv",
            }
            self.assertTrue(
                all((project / "reports" / name).is_file() for name in expected)
            )
            self.run_script(
                "verify_model_kernel_evidence.py",
                "--project-dir",
                str(project),
                "--out",
                str(project / "reports" / "model_kernel_evidence.json"),
            )
            self.run_script(
                "verify_chinese_academic_style.py",
                "--project-dir",
                str(project),
                "--out",
                str(project / "reports" / "chinese_academic_style.json"),
            )
            self.run_script(
                "verify_compute_budget.py",
                "--project-dir",
                str(project),
                "--out",
                str(project / "reports" / "compute_budget_verification.json"),
                expect=1,
            )

        sys.path.insert(0, str(SCRIPTS))
        import contest_orchestration

        contest_orchestration.validate_registry()
        standard = contest_orchestration.load_profile("standard")
        strict = contest_orchestration.load_profile("strict")
        for profile in (standard, strict):
            self.assertIn("verify-chinese-style", profile["phases"]["paper"])
            self.assertIn("verify-paper-reasoning-narrative", profile["phases"]["paper"])
            self.assertIn("verify-model-kernel-evidence", profile["phases"]["freeze"])
            self.assertIn("verify-compute-budget", profile["phases"]["freeze"])

    def test_english_template_marks_chinese_audit_not_applicable(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw) / "mcm-project"
            self.run_script(
                "init_contest.py",
                "--project-dir",
                str(project),
                "--contest",
                "MCM",
                "--year",
                "2027",
                "--mode",
                "training",
            )
            out = project / "reports" / "chinese_academic_style.json"
            self.run_script(
                "verify_chinese_academic_style.py",
                "--project-dir",
                str(project),
                "--out",
                str(out),
            )
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "PASS")
            self.assertEqual(payload["advisory_status"], "NOT_APPLICABLE")


if __name__ == "__main__":
    unittest.main()
