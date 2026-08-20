from __future__ import annotations

import json
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


class PaperPresentationQualityTests(unittest.TestCase):
    def run_script(self, name: str, *args: str, expect: int | set[int] = 0) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / name), *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        expected = expect if isinstance(expect, set) else {expect}
        self.assertIn(result.returncode, expected, result.stdout + result.stderr)

    def test_answer_density_requires_direct_answer_in_conclusion(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper/sections").mkdir(parents=True)
            (root / "reports").mkdir()
            (root / "paper/sections/abstract.tex").write_text(
                "For Q1, the model returns 12 units after validation by residual comparison.", encoding="utf-8"
            )
            (root / "paper/sections/conclusion.tex").write_text("Choose route A.", encoding="utf-8")
            header = "subproblem,question,answer_or_recommendation,decisive_value_key,method_rationale_location,validation_location,limitation_location,figure_or_table,paper_location,status\n"
            row = "Q1,what,Choose route A,value,q1-method,q1-validation,q1-limit,Table 1,q1-conclusion,verified\n"
            (root / "reports/conclusion_map.csv").write_text(header + row, encoding="utf-8")
            self.run_script("verify_answer_density.py", "--project-dir", str(root))
            (root / "paper/sections/conclusion.tex").write_text("No direct recommendation.", encoding="utf-8")
            self.run_script("verify_answer_density.py", "--project-dir", str(root), expect=1)

    def test_visual_design_system_requires_one_profile(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "reports").mkdir()
            figure = "figure,label,source_data,caption_insight,axes_units,color_accessibility,claim_id,question_answered,reader_takeaway,decision_relevance,visual_role,style_profile,palette_or_grayscale,typography_precision,panel_order,legibility_evidence,status\nfig.pdf,fig:q1,result.csv,trend,units,gray,C1,what,improves,select,uncertainty,contest-v1,grayscale,checked,1,page 2,verified\n"
            table = "table,label,source_data,caption_insight,units,precision,emphasis,continuation_check,claim_id,question_answered,reader_takeaway,decision_relevance,style_profile,legibility_evidence,status\ntable.tex,tab:q1,result.csv,values,units,2dp,best,not_applicable,C1,what,improves,select,contest-v1,page 2,verified\n"
            (root / "reports/figure_manifest.csv").write_text(figure, encoding="utf-8")
            (root / "reports/table_manifest.csv").write_text(table, encoding="utf-8")
            self.run_script("verify_visual_design_system.py", "--project-dir", str(root))
            (root / "reports/table_manifest.csv").write_text(table.replace("contest-v1", "contest-v2"), encoding="utf-8")
            self.run_script("verify_visual_design_system.py", "--project-dir", str(root), expect=1)

    def test_presentation_checklist_reports_limited_without_parser(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper").mkdir()
            (root / "reports").mkdir()
            (root / "paper/main.pdf").write_bytes(b"%PDF-1.4\n1 0 obj << /Type /Page >>\nendobj\n%%EOF\n")
            header = "page,hierarchy,font_readability,orphaned_headings_captions,formula_breaks,table_continuity,whitespace_balance,visual_consistency,reviewer,status\n"
            row = "1,pass,pass,pass,pass,not_applicable,pass,pass,reviewer,pass\n"
            (root / "reports/presentation_checklist.csv").write_text(header + row, encoding="utf-8")
            self.run_script("verify_paper_presentation.py", "--project-dir", str(root), expect={1, 2})
            report = json.loads((root / "reports/paper_presentation.json").read_text(encoding="utf-8"))
            self.assertIn(report["status"], {"FAIL", "LIMITED"})

    def test_initialization_creates_presentation_ledgers(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "project"
            self.run_script(
                "init_contest.py", "--project-dir", str(root), "--contest", "CUMCM",
                "--year", "2026", "--mode", "training",
            )
            figure_header = (root / "reports/figure_manifest.csv").read_text(encoding="utf-8")
            self.assertIn("style_profile", figure_header)
            self.assertIn("legibility_evidence", figure_header)
            self.assertTrue((root / "reports/table_manifest.csv").is_file())
            self.assertTrue((root / "reports/presentation_checklist.csv").is_file())
            self.assertTrue((root / "reports/model_simplification_log.csv").is_file())
            self.assertTrue((root / "reports/visual_storyboard.csv").is_file())

    def test_abstract_structure_requires_analysis_method_and_result_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper/sections").mkdir(parents=True)
            abstract = root / "paper/sections/abstract.tex"
            abstract.write_text(
                "Analysis: identify the decision. Method: use a robust model. Results: 12 units.",
                encoding="utf-8",
            )
            self.run_script("verify_abstract_structure.py", "--project-dir", str(root))
            abstract.write_text("Analysis: identify the decision. Method: use a robust model.", encoding="utf-8")
            self.run_script("verify_abstract_structure.py", "--project-dir", str(root), expect=1)

    def test_summary_numbers_require_verified_macros_or_narrow_exemptions(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper/sections").mkdir(parents=True)
            (root / "results").mkdir()
            (root / "reports").mkdir()
            source = root / "results/source.json"
            source.write_text('{"score": 0.81, "count": 42}\n', encoding="utf-8")
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            (root / "results/verified_values.csv").write_text(
                "key,value,value_type,unit,source_file,source_sha256,source_locator,"
                "source_kind,justification\n"
                f"score,0.81,number,dimensionless,results/source.json,{digest},/score,computed,reproduced\n"
                f"count,42,integer,items,results/source.json,{digest},/count,computed,reproduced\n",
                encoding="utf-8",
            )
            abstract = root / "paper/sections/abstract.tex"
            conclusion = root / "paper/sections/conclusion.tex"
            abstract.write_text(
                r"问题 1 的主要结果为 \VerifiedValue{score}。" + "\n",
                encoding="utf-8",
            )
            conclusion.write_text(
                r"最终数量为 \VerifiedValueWithUnit{count}。" + "\n",
                encoding="utf-8",
            )
            (root / "reports/numeric_exemptions.csv").write_text(
                "source_file,line,literal,occurrence,category,reason,status\n"
                "paper/sections/abstract.tex,1,1,1,question_id,subproblem identifier,verified\n",
                encoding="utf-8",
            )
            self.run_script(
                "verify_summary_numeric_traceability.py",
                "--project-dir", str(root),
            )
            conclusion.write_text(
                conclusion.read_text(encoding="utf-8") + "Raw error 9.9%.\n",
                encoding="utf-8",
            )
            self.run_script(
                "verify_summary_numeric_traceability.py",
                "--project-dir", str(root),
                expect=1,
            )

    def test_result_story_requires_authorized_simplification_and_comparison_visual(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "reports").mkdir()
            (root / "results").mkdir()
            (root / "results/q1.json").write_text("{}\n", encoding="utf-8")
            (root / "results/verified_values.csv").write_text("key,value\nanswer,12\n", encoding="utf-8")
            (root / "reports/conclusion_map.csv").write_text(
                "subproblem,decisive_value_key,status\nQ1,answer,verified\n", encoding="utf-8"
            )
            log_header = "subproblem,primary_route,failure_diagnostic,decision_state,retained_core_factors,removed_noncritical_factors,simplified_route,user_authorization,original_model_treatment,result_file,paper_location,status\n"
            unauthorized = "Q1,full,timeout,user_authorized_simplification,flow balance,minor feature,simplified,,model_optimization,results/q1.json,main.tex,verified\n"
            (root / "reports/model_simplification_log.csv").write_text(log_header + unauthorized, encoding="utf-8")
            storyboard_header = "artifact_id,artifact_type,subproblem,question,claim_id,source_result,selection_rationale,paper_location,status\n"
            result_row = "fig:q1,result_chart,Q1,what,C1,results/q1.json,answer,main.tex,verified\n"
            (root / "reports/visual_storyboard.csv").write_text(storyboard_header + result_row, encoding="utf-8")
            (root / "reports/model_challenge.json").write_text(
                json.dumps({"subproblems": [{"subproblem": "Q1", "baseline_name": "base", "candidate_name": "candidate"}]}),
                encoding="utf-8",
            )
            self.run_script("verify_result_story.py", "--project-dir", str(root), expect=1)
            authorized = unauthorized.replace(",simplified,,model_optimization,", ",simplified,user-approved:model-simplification,model_optimization,")
            comparison = "fig:comparison,model_comparison,Q1,which route,C1,results/q1.json,compare,main.tex,verified\n"
            (root / "reports/model_simplification_log.csv").write_text(log_header + authorized, encoding="utf-8")
            (root / "reports/visual_storyboard.csv").write_text(storyboard_header + result_row + comparison, encoding="utf-8")
            self.run_script("verify_result_story.py", "--project-dir", str(root))


if __name__ == "__main__":
    unittest.main()
