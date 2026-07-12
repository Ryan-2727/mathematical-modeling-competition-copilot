from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
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

    def test_recursive_corpus_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "corpus" / "2025"
            root.mkdir(parents=True)
            (root / "A001.pdf").write_bytes(b"not-a-real-pdf")
            out = root.parent.parent / "metrics.json"
            self.run_script("paper_corpus_metrics.py", "--pdf-dir", str(root.parent.parent), "--recursive", "--out", str(out))
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["pdf_count"], 1)
            self.assertTrue(data["papers"][0]["relative_path"].replace("\\", "/").endswith("corpus/2025/A001.pdf"))

    def test_claim_ledger_and_reproduction(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "project"
            self.run_script("init_contest.py", "--project-dir", str(root), "--contest", "CUMCM", "--year", "2026", "--mode", "training")
            (root / "results" / "answer.txt").write_text("42", encoding="utf-8")
            (root / "reports" / "claims.csv").write_text("claim_id,subproblem,claim,source_file,source_locator,command,figure_or_table,paper_location,human_verification,status\nC1,Q1,answer,results/answer.txt,line 1,python code/run.py,Table 1,Section 3,checked,verified\n", encoding="utf-8")
            (root / "reports" / "argument_coverage.csv").write_text("subproblem,need_or_mechanism,model,solution,quantified_result,interpretation,validation,status\nQ1,need,model,solve,result,meaning,check,complete\n", encoding="utf-8")
            report = root / "reports" / "evidence.json"
            self.run_script("verify_claims.py", "--project-dir", str(root), "--out", str(report))
            self.assertEqual(json.loads(report.read_text(encoding="utf-8"))["status"], "PASS")
            reproducibility = root / "reports" / "reproduce.json"
            self.run_script("run_reproduction.py", "--project-dir", str(root), "--command", f'{sys.executable} -c "open(\'results/rebuilt.txt\', \'w\').write(\'ok\')"', "--expected", "results/rebuilt.txt", "--out", str(reproducibility))
            self.assertEqual(json.loads(reproducibility.read_text(encoding="utf-8"))["status"], "PASS")

    def test_similarity_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            draft = root / "draft.md"; draft.write_text("one two three four five six seven eight nine ten eleven twelve", encoding="utf-8")
            corpus = root / "corpus"; corpus.mkdir()
            (corpus / "old.md").write_text("one two three four five six seven eight nine ten eleven twelve", encoding="utf-8")
            out = root / "similarity.json"
            self.run_script("similarity_preflight.py", "--draft", str(draft), "--corpus-dir", str(corpus), "--out", str(out), "--min-overlap", "1")
            self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["status"], "REVIEW")

    def test_cumcm_2026_submission_profile(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paper = root / "paper.docx"; paper.write_bytes(b"docx-placeholder")
            support = root / "support.zip"
            with zipfile.ZipFile(support, "w") as archive:
                archive.writestr("AI\u5de5\u5177\u4f7f\u7528\u8be6\u60c5.pdf", b"pdf-placeholder")
            out = root / "manifest.json"
            self.run_script("verify_submission.py", "--paper", str(paper), "--support", str(support), "--profile", "cumcm-2026", "--main-text-pages", "30", "--require-ai-report", "--out", str(out))
            self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["status"], "PASS")

    @unittest.skipUnless(shutil.which("xelatex") or shutil.which("pdflatex"), "LaTeX is unavailable")
    def test_ai_report_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            log = root / "ai.jsonl"
            self.run_script("log_ai_use.py", "--log", str(log), "--tool", "TestAI", "--version", "1", "--purpose", "draft", "--stage", "writing", "--prompt-summary", "outline", "--adopted", "partial", "--human-verification", "reviewed")
            pdf = root / "AI\u5de5\u5177\u4f7f\u7528\u8be6\u60c5.pdf"
            self.run_script("render_ai_use_report.py", "--log", str(log), "--out", str(root / "report.md"), "--pdf-out", str(pdf))
            self.assertGreater(pdf.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
