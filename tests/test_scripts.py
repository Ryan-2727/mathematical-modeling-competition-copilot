from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


class ScriptTests(unittest.TestCase):
    def run_script(self, name: str, *args: str, expect: int = 0) -> subprocess.CompletedProcess[str]:
        result = subprocess.run([sys.executable, str(SCRIPTS / name), *args], capture_output=True, text=True)
        self.assertEqual(result.returncode, expect, result.stdout + result.stderr)
        return result

    def test_init_and_ai_log(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "project"
            self.run_script("init_contest.py", "--project-dir", str(root), "--contest", "CUMCM", "--year", "2026", "--mode", "training")
            manifest = json.loads((root / "contest_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["mode"], "training")
            log = root / "reports" / "ai_usage_log.jsonl"
            self.run_script("log_ai_use.py", "--log", str(log), "--tool", "TestAI", "--version", "1", "--purpose", "outline", "--stage", "writing", "--prompt-summary", "test", "--adopted", "partial", "--human-verification", "reviewed")
            self.assertIn("TestAI", log.read_text(encoding="utf-8"))

    def test_anonymity_scan(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "note.txt").write_text("University internal draft", encoding="utf-8")
            out = root / "scan.txt"
            self.run_script("anonymity_scan.py", "--root", str(root), "--out", str(out), expect=1)
            self.assertIn("TEXT", out.read_text(encoding="utf-8"))

    def test_submission_rejects_missing_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            out = root / "manifest.json"
            self.run_script("verify_submission.py", "--paper", str(root / "missing.pdf"), "--out", str(out), expect=1)
            self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["status"], "FAIL")

    def test_ai_report_archive_and_state(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "project"
            self.run_script("init_contest.py", "--project-dir", str(root), "--contest", "CUMCM", "--year", "2026", "--mode", "training")
            log = root / "reports" / "ai_usage_log.jsonl"
            self.run_script("log_ai_use.py", "--log", str(log), "--tool", "TestAI", "--version", "1", "--purpose", "draft", "--stage", "writing", "--prompt-summary", "test", "--adopted", "yes", "--human-verification", "checked")
            report = root / "support" / "AI工具使用详情.md"
            self.run_script("render_ai_use_report.py", "--log", str(log), "--out", str(report))
            archive = root / "support.zip"
            archive_manifest = root / "support_manifest.json"
            self.run_script("build_support_archive.py", "--project-dir", str(root), "--include", "support/AI工具使用详情.md", "--out", str(archive), "--manifest", str(archive_manifest))
            manifest = root / "contest_manifest.json"
            self.run_script("set_submission_state.py", "--manifest", str(manifest), "--state", "verified", "--evidence", str(report))
            self.assertEqual(json.loads(manifest.read_text(encoding="utf-8"))["submission_state"], "verified")


if __name__ == "__main__":
    unittest.main()
