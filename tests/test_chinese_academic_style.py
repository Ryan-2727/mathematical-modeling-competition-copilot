from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_chinese_academic_style.py"
EXEMPTION_FIELDS = [
    "finding_sha256",
    "rule",
    "source_file",
    "line",
    "reason",
    "reviewer",
    "status",
]


class ChineseAcademicStyleTests(unittest.TestCase):
    def run_audit(self, root: Path, *args: str, expect: int = 0) -> dict:
        out = root / "reports" / "chinese_academic_style.json"
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--project-dir",
                str(root),
                "--out",
                str(out),
                *args,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(result.returncode, expect, result.stdout + result.stderr)
        return json.loads(out.read_text(encoding="utf-8"))

    @staticmethod
    def scaffold(root: Path, abstract: str, conclusion: str) -> None:
        (root / "paper" / "sections").mkdir(parents=True)
        (root / "reports").mkdir()
        (root / "contest_manifest.json").write_text(
            json.dumps({"latex_template": "cumcm"}), encoding="utf-8"
        )
        (root / "paper" / "main.tex").write_text(
            "\\documentclass{article}\n"
            "\\begin{document}\n"
            "\\input{sections/abstract}\n"
            "\\input{sections/conclusion}\n"
            "\\end{document}\n",
            encoding="utf-8",
        )
        (root / "paper" / "sections" / "abstract.tex").write_text(
            abstract, encoding="utf-8"
        )
        (root / "paper" / "sections" / "conclusion.tex").write_text(
            conclusion, encoding="utf-8"
        )
        with (root / "reports" / "prose_style_exemptions.csv").open(
            "w", encoding="utf-8", newline=""
        ) as handle:
            csv.DictWriter(handle, fieldnames=EXEMPTION_FIELDS).writeheader()

    def test_default_audit_is_advisory_and_artifact_located(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            long_sentence = "这一句连续说明模型假设参数估计计算过程验证过程稳健性分析实施条件和结论边界" * 3 + "。"
            self.scaffold(
                root,
                "\\section{摘要}\n"
                "本文采用ABC模型分析数据。\n"
                "模型效果显著且较好。\n"
                "价格提高导致销量下降。\n"
                "误差为1.2\\%，另一场景误差为1.234\\%。\n"
                "本文本文本文本文用于说明。\n"
                "该方案具有较高的实施价值。\n"
                + long_sentence
                + "\n",
                "\\section{结论}\n该方案具有较高的实施价值。\n",
            )
            report = self.run_audit(root)
            self.assertEqual(report["status"], "PASS", report)
            self.assertEqual(report["advisory_status"], "REVIEW")
            rules = {item["rule"] for item in report["unresolved_findings"]}
            self.assertTrue(
                {
                    "undefined_abbreviation",
                    "vague_claim",
                    "causal_overclaim",
                    "precision_consistency",
                    "duplicate_sentence",
                    "long_sentence",
                    "excessive_self_reference",
                }
                <= rules,
                rules,
            )
            self.assertTrue(
                all(item["source_file"] and item["line"] >= 1 for item in report["findings"])
            )
            strict = self.run_audit(root, "--fail-on", "major", expect=1)
            self.assertEqual(strict["status"], "FAIL")

    def test_human_exemption_is_bound_and_stale_exemption_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.scaffold(
                root,
                "\\section{摘要}\n模型效果显著。\n",
                "\\section{结论}\n结果见表~\\ref{tab:result}。\n",
            )
            first = self.run_audit(root)
            finding = next(
                item for item in first["findings"] if item["rule"] == "vague_claim"
            )
            with (root / "reports" / "prose_style_exemptions.csv").open(
                "w", encoding="utf-8", newline=""
            ) as handle:
                writer = csv.DictWriter(handle, fieldnames=EXEMPTION_FIELDS)
                writer.writeheader()
                writer.writerow(
                    {
                        "finding_sha256": finding["finding_sha256"],
                        "rule": finding["rule"],
                        "source_file": finding["source_file"],
                        "line": finding["line"],
                        "reason": "A nearby table is added by the official template at compile time.",
                        "reviewer": "team-paper-reviewer",
                        "status": "verified",
                    }
                )
            exempted = self.run_audit(root)
            self.assertEqual(len(exempted["exempted_findings"]), 1)
            self.assertEqual(len(exempted["unresolved_findings"]), 0)

            (root / "paper" / "sections" / "abstract.tex").write_text(
                "\\section{摘要}\n模型效果明显。\n", encoding="utf-8"
            )
            stale = self.run_audit(root, expect=1)
            self.assertTrue(any("stale" in error for error in stale["errors"]))

    def test_evidence_qualified_prose_avoids_targeted_false_positives(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.scaffold(
                root,
                "\\section{摘要}\n"
                "针对配送路径问题，我们先分析车辆容量与时间窗约束，再建立线性规划模型。\n"
                "算法精度显著提高至\\VerifiedValue{accuracy}，结果见表~\\ref{tab:accuracy}。\n"
                "层次分析法（AHP）仅用于确定已声明的权重。\n",
                "\\section{结论}\n"
                "现有数据支持预测关联，但证据不足以识别因果效应，相关限制见第~\\ref{sec:limits}节。\n",
            )
            report = self.run_audit(root)
            rules = {item["rule"] for item in report["unresolved_findings"]}
            self.assertNotIn("undefined_abbreviation", rules)
            self.assertNotIn("vague_claim", rules)
            self.assertNotIn("causal_overclaim", rules)
            self.assertEqual(report["advisory_status"], "PASS", report)


if __name__ == "__main__":
    unittest.main()
