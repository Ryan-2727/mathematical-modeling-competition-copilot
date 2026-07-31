from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import verify_submission as submission


def inspected(page_texts: list[str]) -> submission.PdfInspection:
    return submission.PdfInspection(
        page_count=len(page_texts),
        page_texts=page_texts,
        tools={
            "pdfinfo": {"available": True, "returncode": 0, "scope": "PDF page count"},
            "pdftotext": {
                "available": True,
                "returncode": 0,
                "scope": "PDF text",
            },
        },
    )


def mcm_page(control_number: str, page: int, body: str = "Solution") -> str:
    return f"Team {control_number}                                      Page {page}\n{body}\n"


class SubmissionProfileTests(unittest.TestCase):
    def make_pdf(self, root: Path, name: str = "paper.pdf") -> Path:
        paper = root / name
        paper.write_bytes(b"%PDF-1.4\nprofile-test\n")
        return paper

    def make_ai_support(self, root: Path) -> Path:
        support = root / "support.zip"
        with zipfile.ZipFile(support, "w") as archive:
            archive.writestr("AI工具使用详情.pdf", b"report")
        return support

    def test_expired_rule_snapshot_blocks_profile(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paper = self.make_pdf(root)
            expired = {
                "paper_suffixes": {".pdf"},
                "support_suffixes": {".zip"},
                "max_paper_mb": 20,
                "max_support_mb": 20,
                "snapshot": {
                    "profile_version": "expired-test.2000-01-01",
                    "verified_at": "2000-01-01",
                    "valid_through": "2000-01-02",
                    "official_sources": ["https://example.invalid/official"],
                },
            }
            with (
                patch.dict(submission.PROFILES, {"expired-test": expired}),
                patch.object(submission, "inspect_pdf", return_value=inspected(["test"])),
            ):
                payload = submission.verify_submission(
                    paper=paper,
                    support=None,
                    profile_name="expired-test",
                )
            self.assertEqual(payload["status"], "FAIL")
            check = next(
                item
                for item in payload["checks"]
                if item["id"] == "profile.rules_snapshot"
            )
            self.assertEqual(check["status"], "FAIL")
            self.assertIn("refresh official sources", check["evidence"])

    def test_cumcm_executes_content_and_ai_checks(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paper = self.make_pdf(root)
            support = self.make_ai_support(root)
            pages = [
                "摘要\n本文给出模型、结果与验证。\n关键词：建模",
                "模型建立\n本文使用 ChatGPT 辅助翻译，相关内容已人工核验 [2]。",
                "参考文献\n[1] Test. [2] OpenAI, ChatGPT, GPT-4o, 2026-07-24.",
                "A 附录：代码与支撑材料说明\n支撑材料的文件列表：code/run.py\n完整源程序代码如下。",
            ]
            with patch.object(submission, "inspect_pdf", return_value=inspected(pages)):
                payload = submission.verify_submission(
                    paper=paper,
                    support=support,
                    profile_name="cumcm-2026",
                    main_text_pages=3,
                    ai_mode="used",
                )
            self.assertEqual(payload["status"], "PASS", payload)
            statuses = {item["id"]: item["status"] for item in payload["checks"]}
            for check_id in (
                "cumcm.first_page_abstract",
                "cumcm.toc_forbidden",
                "cumcm.appendix_support_manifest",
                "cumcm.appendix_code_evidence",
                "cumcm.ai_report",
                "cumcm.ai_inline_disclosure",
                "cumcm.ai_reference",
                "cumcm.ai_mode",
            ):
                self.assertEqual(statuses[check_id], "PASS", check_id)

    def test_cumcm_ai_none_requires_exact_post_reference_declaration(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paper = self.make_pdf(root)
            pages = [
                "摘要\n本文给出模型、结果与验证。\n关键词：建模",
                "模型建立与求解",
                "参考文献\n[1] Test.\n本参赛队未使用任何 AI 工具",
                "A 附录：代码与支撑材料说明\n本论文没有支撑材料\n本论文没有用到程序",
            ]
            with patch.object(submission, "inspect_pdf", return_value=inspected(pages)):
                payload = submission.verify_submission(
                    paper=paper,
                    support=None,
                    profile_name="cumcm-2026",
                    main_text_pages=3,
                    ai_mode="none",
                )
            self.assertEqual(payload["status"], "PASS", payload)
            self.assertEqual(payload["ai_mode"], "none")

            pages[2] = "本参赛队未使用任何 AI 工具\n参考文献\n[1] Test."
            with patch.object(submission, "inspect_pdf", return_value=inspected(pages)):
                failure = submission.verify_submission(
                    paper=paper,
                    support=None,
                    profile_name="cumcm-2026",
                    main_text_pages=3,
                    ai_mode="none",
                )
            self.assertEqual(failure["status"], "FAIL")
            self.assertIn("cumcm.ai_non_use_declaration", {
                item["id"] for item in failure["checks"] if item["status"] == "FAIL"
            })

    def test_cumcm_ai_mode_is_required_and_contradictions_fail(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paper = self.make_pdf(root)
            support = self.make_ai_support(root)
            pages = [
                "摘要\n模型与结果",
                "本文使用 ChatGPT 辅助编程并完成人工核验。",
                "参考文献\n[1] OpenAI, ChatGPT, 2026.\n本参赛队未使用任何 AI 工具",
                "附录\n支撑材料的文件列表：AI工具使用详情.pdf\n本论文没有用到程序",
            ]
            with patch.object(submission, "inspect_pdf", return_value=inspected(pages)):
                missing = submission.verify_submission(
                    paper=paper,
                    support=support,
                    profile_name="cumcm-2026",
                    main_text_pages=3,
                )
                contradiction = submission.verify_submission(
                    paper=paper,
                    support=support,
                    profile_name="cumcm-2026",
                    main_text_pages=3,
                    ai_mode="used",
                )
            self.assertEqual(missing["status"], "FAIL")
            self.assertEqual(contradiction["status"], "FAIL")
            self.assertTrue(any("non-use declaration" in item for item in contradiction["errors"]))

    def test_cumcm_rejects_toc_wrong_first_page_and_missing_appendix_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paper = self.make_pdf(root)
            pages = [
                "Introduction\nThis is not an abstract.",
                "目录\n1 模型\n2 结果",
            ]
            with patch.object(submission, "inspect_pdf", return_value=inspected(pages)):
                payload = submission.verify_submission(
                    paper=paper,
                    support=None,
                    profile_name="cumcm-2026",
                    main_text_pages=31,
                )
            self.assertEqual(payload["status"], "FAIL")
            failed = {
                item["id"] for item in payload["checks"] if item["status"] == "FAIL"
            }
            self.assertTrue(
                {
                    "cumcm.main_text_pages",
                    "cumcm.first_page_abstract",
                    "cumcm.toc_forbidden",
                    "cumcm.appendix_support_manifest",
                    "cumcm.appendix_code_evidence",
                }.issubset(failed)
            )

    def test_mcm_profile_enforces_summary_font_filename_headers_and_page_count(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            control = "1234567"
            paper = self.make_pdf(root, f"{control}.pdf")
            pages = [
                mcm_page(control, 1, "Summary Sheet\nModel and main findings."),
                mcm_page(control, 2, "Table of Contents"),
                mcm_page(control, 3, "Solution and References"),
            ]
            with patch.object(submission, "inspect_pdf", return_value=inspected(pages)):
                payload = submission.verify_submission(
                    paper=paper,
                    support=None,
                    profile_name="mcm-icm-current",
                    font_size_pt=12,
                    control_number=control,
                )
            self.assertEqual(payload["status"], "PASS", payload)
            self.assertEqual(payload["profile_snapshot"]["profile_version"], "mcm-icm-2027.2026-07-24")
            self.assertEqual(payload["profile_snapshot"]["valid_through"], "2027-02-01")
            self.assertEqual(
                {
                    key for key in submission.PROFILES if key.startswith("mcm-icm")
                },
                {"mcm-icm", "mcm-icm-current", "mcm-icm-2027"},
            )
            self.assertIs(
                submission.PROFILES["mcm-icm"],
                submission.PROFILES["mcm-icm-current"],
            )
            self.assertRegex(
                payload["profile_snapshot"]["parameters_sha256"], r"^[0-9a-f]{64}$"
            )

    def test_mcm_ai_report_is_excluded_only_after_counted_solution(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            control = "7654321"
            paper = self.make_pdf(root, f"{control}.pdf")
            pages = [
                mcm_page(control, page, "Summary Sheet" if page == 1 else "Solution")
                for page in range(1, 26)
            ]
            pages[-1] += (
                "\nWe used ChatGPT to assist translation and verified the output [8].\n"
                "References\n[8] OpenAI, ChatGPT, GPT-4o, 2026.\n"
            )
            pages.append(
                mcm_page(control, 26, "Report on Use of AI\nOpenAI ChatGPT")
            )
            with patch.object(submission, "inspect_pdf", return_value=inspected(pages)):
                payload = submission.verify_submission(
                    paper=paper,
                    support=None,
                    profile_name="mcm-icm-2027",
                    font_size_pt=12,
                    control_number=control,
                    require_ai_report=True,
                )
            self.assertEqual(payload["status"], "PASS", payload)
            count_check = next(
                item for item in payload["checks"] if item["id"] == "mcm.counted_pages"
            )
            self.assertIn("25 pages", count_check["evidence"])

            over_limit = pages[:25] + [
                mcm_page(control, 26, "Still part of the solution"),
                mcm_page(control, 27, "Report on Use of AI Tools"),
            ]
            with patch.object(
                submission, "inspect_pdf", return_value=inspected(over_limit)
            ):
                failure = submission.verify_submission(
                    paper=paper,
                    support=None,
                    profile_name="mcm-icm-current",
                    font_size_pt=12,
                    control_number=control,
                    require_ai_report=True,
                )
            self.assertEqual(failure["status"], "FAIL")
            self.assertTrue(
                any("26 pages" in error for error in failure["errors"]),
                failure["errors"],
            )

    def test_mcm_rejects_support_and_under_12pt_declaration(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            control = "1234567"
            paper = self.make_pdf(root, f"{control}.pdf")
            support = root / "code.zip"
            with zipfile.ZipFile(support, "w") as archive:
                archive.writestr("run.py", "print('x')")
            pages = [mcm_page(control, 1, "Summary Sheet")]
            with patch.object(submission, "inspect_pdf", return_value=inspected(pages)):
                payload = submission.verify_submission(
                    paper=paper,
                    support=support,
                    profile_name="mcm-icm-current",
                    font_size_pt=11,
                    control_number=control,
                )
            self.assertEqual(payload["status"], "FAIL")
            self.assertTrue(
                any("prohibits additional" in error for error in payload["errors"])
            )
            self.assertTrue(any("12pt" in error for error in payload["errors"]))

    def test_missing_pdf_tools_is_fail_without_evidence_and_limited_with_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            control = "1234567"
            paper = self.make_pdf(root, f"{control}.pdf")
            unavailable = submission.PdfInspection(
                page_count=None,
                page_texts=None,
                tools={
                    "pdfinfo": {"available": False, "scope": "PDF page count"},
                    "pdftotext": {"available": False, "scope": "PDF text"},
                },
            )
            with patch.object(submission, "inspect_pdf", return_value=unavailable):
                failure = submission.verify_submission(
                    paper=paper,
                    support=None,
                    profile_name="mcm-icm-current",
                    font_size_pt=12,
                    control_number=control,
                )
            self.assertEqual(failure["status"], "FAIL")
            self.assertTrue(
                any("requires pdfinfo" in error for error in failure["errors"])
            )

            evidence = root / "evidence.json"
            evidence.write_text(
                json.dumps(
                    {
                        "paper_sha256": hashlib.sha256(paper.read_bytes()).hexdigest(),
                        "reviewer": "team visual inspection",
                        "recorded_at": "2026-07-24T20:00:00+08:00",
                        "summary_sheet_first": True,
                        "font_size_pt": 12,
                        "pdf_pages": 4,
                        "control_header_pages": "all_pages",
                        "ai_report_start_page": 4,
                        "ai_inline_disclosure": True,
                        "ai_reference_entry": True,
                    }
                ),
                encoding="utf-8",
            )
            with patch.object(submission, "inspect_pdf", return_value=unavailable):
                limited = submission.verify_submission(
                    paper=paper,
                    support=None,
                    profile_name="mcm-icm-current",
                    control_number=control,
                    evidence_path=evidence,
                    require_ai_report=True,
                )
            self.assertEqual(limited["status"], "LIMITED", limited)
            self.assertGreaterEqual(len(limited["limitations"]), 6)

    def test_mcm_template_has_required_submission_markers(self) -> None:
        template = ROOT / "assets" / "latex-paper-template-mcm"
        main = (template / "main.tex").read_text(encoding="utf-8")
        summary = (template / "sections" / "summary.tex").read_text(
            encoding="utf-8"
        )
        ai_report = (template / "sections" / "ai_report.tex").read_text(
            encoding="utf-8"
        )
        self.assertIn(r"\documentclass[12pt]{article}", main)
        self.assertIn(r"\fancyhead[C]{Team \# \TeamControlNumber}", main)
        self.assertIn(r"\fancyhead[R]{Page \thepage}", main)
        self.assertIn(r"\ifincludeaireport", main)
        self.assertIn("Summary Sheet", summary)
        self.assertIn(r"\section*{Report on Use of AI}", ai_report)

    @unittest.skipUnless(
        shutil.which("latexmk") and shutil.which("xelatex") and shutil.which("bibtex"),
        "latexmk, XeLaTeX, and BibTeX are unavailable",
    )
    def test_mcm_template_compiles_in_root_and_vscode_build_paths(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            paper = Path(raw) / "paper"
            shutil.copytree(ROOT / "assets" / "latex-paper-template-mcm", paper)
            (paper / "build").mkdir()
            report = Path(raw) / "compatibility.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "verify_latex_compatibility.py"),
                    "--paper-dir",
                    str(paper),
                    "--out",
                    str(report),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "PASS", payload)
            self.assertEqual(len(payload["builds"]), 2)
            self.assertGreater((paper / "main.pdf").stat().st_size, 0)
            self.assertGreater((paper / "build" / "main.pdf").stat().st_size, 0)

            submission_pdf = paper / "0000000.pdf"
            shutil.copy2(paper / "main.pdf", submission_pdf)
            profile_report = submission.verify_submission(
                paper=submission_pdf,
                support=None,
                profile_name="mcm-icm-current",
                font_size_pt=12,
                control_number="0000000",
            )
            self.assertEqual(profile_report["status"], "PASS", profile_report)


if __name__ == "__main__":
    unittest.main()
