from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "originality_preflight.py"


class OriginalityPreflightTests(unittest.TestCase):
    def run_scan(
        self,
        project: Path,
        corpus: Path,
        *,
        expected: int,
        confirmed: bool = True,
    ) -> tuple[dict[str, object], str]:
        out_json = project / "reports" / "originality_preflight.json"
        out_md = project / "reports" / "originality_preflight.md"
        command = [
            sys.executable,
            str(SCRIPT),
            "--project-dir", str(project),
            "--corpus-dir", str(corpus),
            "--out-json", str(out_json),
            "--out-md", str(out_md),
        ]
        if confirmed:
            command.append("--historical-corpus-confirmed")
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        self.assertTrue(out_json.is_file(), result.stdout + result.stderr)
        return (
            json.loads(out_json.read_text(encoding="utf-8")),
            out_md.read_text(encoding="utf-8"),
        )

    def make_project(self, root: Path, paragraph: str, *, mode: str = "training") -> Path:
        project = root / "project"
        (project / "paper" / "sections" / "nested").mkdir(parents=True)
        (project / "reports").mkdir()
        (project / "contest_manifest.json").write_text(
            json.dumps({"mode": mode, "submission_profile": "cum"}), encoding="utf-8"
        )
        (project / "paper" / "main.tex").write_text(
            "\\documentclass{article}\n\\begin{document}\n"
            "\\input{sections/model}\n\\end{document}\n",
            encoding="utf-8",
        )
        (project / "paper" / "sections" / "model.tex").write_text(
            "\\section{模型建立}\n" + paragraph + "\n\n"
            "\\include{nested/result}\n",
            encoding="utf-8",
        )
        (project / "paper" / "sections" / "nested" / "result.tex").write_text(
            "计算结果由本队程序独立产生，并使用留出数据完成验证。\n",
            encoding="utf-8",
        )
        return project

    def test_complete_latex_exact_match_is_located_and_review_bound(self) -> None:
        paragraph = (
            "针对观测误差与参数不确定性，我们构建分层优化模型，"
            "并通过灵敏度分析检验最终决策在扰动情景下的稳定性。"
        )
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            project = self.make_project(root, paragraph)
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "historical.txt").write_text(
                "历史论文段落。\n\n" + paragraph + "\n", encoding="utf-8"
            )

            report, markdown = self.run_scan(project, corpus, expected=2)
            self.assertEqual(report["status"], "REVIEW")
            finding = report["findings"][0]
            self.assertEqual(finding["risk"], "HIGH")
            self.assertEqual(finding["draft_path"], "paper/sections/model.tex")
            self.assertEqual(finding["draft_line_start"], 2)
            self.assertEqual(finding["draft_paragraph"], paragraph)
            self.assertEqual(finding["corpus_path"], str(corpus / "historical.txt"))
            self.assertTrue(finding["risk_reasons"])
            self.assertIn("命中原因", markdown)
            self.assertIn(paragraph, markdown)
            self.assertNotIn("![", markdown)
            self.assertNotIn("替换稿", markdown)

            review_path = project / "reports" / "originality_review.csv"
            with review_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "finding_id", "draft_sha256", "disposition", "reason",
                        "reviewer", "status",
                    ],
                )
                writer.writeheader()
                writer.writerow({
                    "finding_id": finding["finding_id"],
                    "draft_sha256": finding["draft_sha256"],
                    "disposition": "resolved",
                    "reason": "rewritten from the team's executed model evidence",
                    "reviewer": "team member 2",
                    "status": "complete",
                })
            report, _ = self.run_scan(project, corpus, expected=0)
            self.assertEqual(report["status"], "PASS")

            model = project / "paper" / "sections" / "model.tex"
            model.write_text(model.read_text(encoding="utf-8").replace(paragraph, paragraph + "补充说明。"), encoding="utf-8")
            report, _ = self.run_scan(project, corpus, expected=2)
            self.assertEqual(report["status"], "REVIEW")
            self.assertTrue(report["stale_reviews"])

    def test_near_duplicate_with_small_edits_is_reported(self) -> None:
        draft = "我们建立多目标规划模型，同时考虑成本、风险以及方案执行的稳定性，并比较不同权重下的结果。"
        source = "本文建立多目标规划模型，综合考虑成本、风险和方案执行稳定性，并对比不同权重条件下的结果。"
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            project = self.make_project(root, draft)
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "paper.md").write_text(source, encoding="utf-8")
            report, _ = self.run_scan(project, corpus, expected=2)
            finding = next(item for item in report["findings"] if item["draft_paragraph"] == draft)
            self.assertIn(finding["risk"], {"HIGH", "MEDIUM"})
            self.assertGreater(finding["ngram_jaccard"], 0.45)

    def test_unsafe_include_and_live_unconfirmed_corpus_fail(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            project = self.make_project(root, "这是一个具有足够长度且由本队独立写作的模型分析段落。", mode="live")
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "old.txt").write_text("完全不同的历史内容段落用于安全测试。", encoding="utf-8")
            report, _ = self.run_scan(project, corpus, expected=1, confirmed=False)
            self.assertTrue(any("historical" in item for item in report["errors"]))

            main = project / "paper" / "main.tex"
            main.write_text("\\input{../../../outside}\n", encoding="utf-8")
            report, _ = self.run_scan(project, corpus, expected=1)
            self.assertTrue(any("outside the project" in item for item in report["errors"]))

            main.write_text(
                "\\begin{document}\n这是一个恢复后的安全正文段落。\n\\end{document}\n",
                encoding="utf-8",
            )
            report, _ = self.run_scan(project, root, expected=1)
            self.assertTrue(any("must not contain the project" in item for item in report["errors"]))

    def test_unreadable_pdf_is_limited_and_creates_no_images(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            project = self.make_project(root, "本队采用独立计算结果解释模型机制并完成稳健性检验。")
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "image-only.pdf").write_bytes(b"not an extractable PDF")
            report, markdown = self.run_scan(project, corpus, expected=2)
            self.assertEqual(report["status"], "LIMITED")
            self.assertTrue(report["unreadable_corpus"])
            self.assertIn("未读取语料", markdown)
            self.assertFalse(any(project.rglob("*.png")))
            self.assertFalse(any(project.rglob("*.jpg")))

    def test_project_configuration_runs_without_corpus_cli_argument(self) -> None:
        paragraph = "该段从本队计算证据出发，说明模型选择、参数来源以及边界条件。"
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            project = self.make_project(root, paragraph)
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "historical.txt").write_text(paragraph, encoding="utf-8")
            config = project / "reports" / "originality_config.json"
            config.write_text(
                json.dumps({
                    "schema_version": 1,
                    "enabled": True,
                    "main_tex": "paper/main.tex",
                    "corpus_dirs": [str(corpus)],
                    "historical_corpus_confirmed": True,
                }),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--project-dir", str(project),
                    "--config", str(config),
                    "--out-json", str(project / "reports" / "originality_preflight.json"),
                    "--out-md", str(project / "reports" / "originality_preflight.md"),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            report = json.loads(
                (project / "reports" / "originality_preflight.json").read_text(encoding="utf-8")
            )
            self.assertTrue(report["historical_corpus_confirmed"])
            self.assertEqual(report["status"], "REVIEW")

    def test_display_math_and_asset_paths_are_not_scanned_as_prose(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            project = self.make_project(root, "独立正文段落用于确认公式后的文字不会被遗漏。")
            model = project / "paper" / "sections" / "model.tex"
            model.write_text(
                "\\begin{equation}objectiveFunctionName=historicalTemplateValue\\end{equation}\n"
                "\\[anotherLongHistoricalFormulaToken\\]\n"
                "\\includegraphics{historicalTemplateFigureName.pdf}\n"
                "独立正文段落用于确认公式后的文字不会被遗漏。\n",
                encoding="utf-8",
            )
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "old.txt").write_text(
                "objectiveFunctionName historicalTemplateValue "
                "anotherLongHistoricalFormulaToken historicalTemplateFigureName",
                encoding="utf-8",
            )
            report, _ = self.run_scan(project, corpus, expected=0)
            self.assertEqual(report["status"], "PASS")
            self.assertTrue(all(
                "historicalTemplate" not in item["draft_paragraph"]
                for item in report["findings"]
            ))


if __name__ == "__main__":
    unittest.main()
