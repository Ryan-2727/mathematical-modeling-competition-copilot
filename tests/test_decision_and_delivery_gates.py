from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


class DecisionAndDeliveryGateTests(unittest.TestCase):
    def run_script(self, name: str, root: Path, expect: int | set[int] = 0) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / name), "--project-dir", str(root)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        expected = expect if isinstance(expect, set) else {expect}
        self.assertIn(result.returncode, expected, result.stdout + result.stderr)

    @staticmethod
    def digest(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def test_decision_stability_requires_conditional_disclosure(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "reports").mkdir()
            (root / "results").mkdir()
            (root / "results/q1.json").write_text("{}\n", encoding="utf-8")
            (root / "reports/conclusion_map.csv").write_text("subproblem\nQ1\n", encoding="utf-8")
            header = "decision_id,subproblem,baseline_recommendation,perturbation_id,perturbation,perturbed_recommendation,recommendation_changed,materiality,conditional_conclusion,limitation_location,result_file,paper_location,status\n"
            row = "D1,Q1,route A,P1,demand +10%,route B,true,material,conditional,sec:limit,results/q1.json,sec:conclusion,verified\n"
            ledger = root / "reports/decision_stability.csv"
            ledger.write_text(header + row, encoding="utf-8")
            self.run_script("verify_decision_stability.py", root)
            ledger.write_text(header + row.replace("conditional", "unconditional", 1), encoding="utf-8")
            self.run_script("verify_decision_stability.py", root, expect=1)

    def test_figure_numeric_contract_rejects_stale_data_hash(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "reports").mkdir()
            (root / "results").mkdir()
            data = root / "results/series.csv"
            data.write_text("x,y\n1,2\n", encoding="utf-8")
            (root / "results/verified_values.csv").write_text("key,value\npeak,2\n", encoding="utf-8")
            (root / "reports/figure_manifest.csv").write_text("figure,label,source_data\nfig.pdf,fig:trend,results/series.csv\n", encoding="utf-8")
            header = "figure,label,source_data,data_sha256,axis_x,axis_y,axis_scale,x_limits,y_limits,value_transform,decisive_value_keys,paper_location,status\n"
            row = f"fig.pdf,fig:trend,results/series.csv,{self.digest(data)},time,value,linear,1:1,2:2,none,peak,sec:results,verified\n"
            contract = root / "reports/figure_numeric_contract.csv"
            contract.write_text(header + row, encoding="utf-8")
            self.run_script("verify_figure_numeric_contract.py", root)
            contract.write_text(header + row.replace(self.digest(data), "0" * 64), encoding="utf-8")
            self.run_script("verify_figure_numeric_contract.py", root, expect=1)

    def test_model_budget_requires_single_selected_route_and_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "reports").mkdir()
            header = (
                "subproblem,route_name,route_type,selected,estimated_hours,risk_level,"
                "validation_hours,fallback_route,expected_value,deadline_hours,"
                "comparison_metric,metric_direction,baseline_value,candidate_value,"
                "minimum_advantage,validation_artifact,paper_treatment,status\n"
            )
            baseline = (
                "Q1,baseline,baseline,true,2,low,1,fallback,not_applicable,10,"
                "not_applicable,not_applicable,not_applicable,not_applicable,"
                "not_applicable,not_applicable,primary,verified\n"
            )
            fallback = (
                "Q1,fallback,fallback,false,1,low,1,baseline,not_applicable,10,"
                "not_applicable,not_applicable,not_applicable,not_applicable,"
                "not_applicable,not_applicable,fallback,verified\n"
            )
            budget = root / "reports/model_budget.csv"
            budget.write_text(header + baseline + fallback, encoding="utf-8")
            self.run_script("verify_model_budget.py", root)
            budget.write_text(header + baseline + fallback.replace(",false,", ",true,"), encoding="utf-8")
            self.run_script("verify_model_budget.py", root, expect=1)

            evidence = root / "results.json"
            evidence.write_text('{"score": 0.81}\n', encoding="utf-8")
            candidate = (
                "Q1,complex,candidate,true,3,medium,1,baseline,better score,10,"
                "validated_score,higher,0.80,0.81,0.02,results.json,primary,verified\n"
            )
            budget.write_text(
                header
                + baseline.replace(",true,", ",false,").replace(",primary,", ",comparison,")
                + candidate
                + fallback,
                encoding="utf-8",
            )
            self.run_script("verify_model_budget.py", root, expect=1)
            budget.write_text(
                header
                + baseline.replace(",true,", ",false,").replace(",primary,", ",comparison,")
                + candidate.replace(",0.81,0.02,", ",0.83,0.02,")
                + fallback,
                encoding="utf-8",
            )
            self.run_script("verify_model_budget.py", root)

    def test_three_minute_review_requires_all_reader_path_elements(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "reports").mkdir()
            (root / "results").mkdir()
            (root / "paper/sections").mkdir(parents=True)
            (root / "paper/sections/abstract.tex").write_text("Answer.", encoding="utf-8")
            (root / "reports/figure_manifest.csv").write_text("label\nfig:route\n", encoding="utf-8")
            (root / "results/verified_values.csv").write_text("key\nanswer\n", encoding="utf-8")
            (root / "reports/conclusion_map.csv").write_text("subproblem\nQ1\n", encoding="utf-8")
            header = "element,reader_question,direct_answer,evidence_type,evidence_ref,paper_location,status\n"
            rows = [
                "abstract,what,answer,paper_file,paper/sections/abstract.tex,p1,verified\n",
                "route_figure,how,route,figure_label,fig:route,p2,verified\n",
                "core_result,what,result,verified_value,answer,p3,verified\n",
                "recommendation,what,choose,conclusion_map,Q1,p4,verified\n",
                "limitation,when,boundary,conclusion_map,Q1,p5,verified\n",
            ]
            review = root / "reports/three_minute_review.csv"
            review.write_text(header + "".join(rows), encoding="utf-8")
            self.run_script("verify_three_minute_review.py", root)
            review.write_text(header + "".join(rows[:-1]), encoding="utf-8")
            self.run_script("verify_three_minute_review.py", root, expect=1)

    def test_latex_dependency_lock_reports_missing_tools_honestly(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper/.vscode").mkdir(parents=True)
            (root / "paper/main.tex").write_text("\\documentclass{article}\n\\usepackage{graphicx,booktabs}\n", encoding="utf-8")
            (root / "paper/.latexmkrc").write_text("$pdf_mode = 5;\n", encoding="utf-8")
            (root / "paper/.vscode/settings.json").write_text("{}\n", encoding="utf-8")
            (root / "paper/.vscode/extensions.json").write_text("{}\n", encoding="utf-8")
            self.run_script("verify_latex_dependency_lock.py", root, expect={0, 2})
            report = json.loads((root / "reports/latex_dependency_lock.json").read_text(encoding="utf-8"))
            self.assertIn(report["status"], {"PASS", "LIMITED"})
            (root / "paper/main.tex").unlink()
            self.run_script("verify_latex_dependency_lock.py", root, expect=1)

    def test_initializer_creates_new_ledgers_and_freeze_registers_reports(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "project"
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "init_contest.py"), "--project-dir", str(root), "--contest", "CUMCM", "--year", "2026", "--mode", "training"],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            for name in ("decision_stability.csv", "figure_numeric_contract.csv", "model_budget.csv", "three_minute_review.csv"):
                self.assertTrue((root / "reports" / name).is_file())
        sys.path.insert(0, str(SCRIPTS))
        try:
            import contestctl
            for report in ("reports/decision_stability.json", "reports/figure_numeric_contract.json", "reports/model_budget.json", "reports/three_minute_review.json", "reports/latex_dependency_lock.json"):
                self.assertIn(report, contestctl.REPORTS["freeze"])
                self.assertIn(report, contestctl.REPORT_BINDINGS)
        finally:
            sys.path.remove(str(SCRIPTS))


if __name__ == "__main__":
    unittest.main()
