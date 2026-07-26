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


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class AwardEvidenceGateTests(unittest.TestCase):
    def run_script(self, name: str, *args: str, expect: int = 0) -> None:
        result = subprocess.run([sys.executable, str(SCRIPTS / name), *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(result.returncode, expect, result.stdout + result.stderr)

    def test_evidence_chain_and_figure_narrative_pass(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            for name in ("reports", "results", "data", "paper"):
                (root / name).mkdir()
            source, result = root / "data" / "raw.csv", root / "results" / "metrics.json"
            source.write_text("x\n1\n", encoding="utf-8")
            result.write_text('{"value": 3}\n', encoding="utf-8")
            (root / "paper" / "main.tex").write_text("\\documentclass{article}\\begin{document}\\VerifiedValue{gain}\\end{document}\n", encoding="utf-8")
            (root / "reports" / "claims.csv").write_text("claim_id,subproblem,claim,source_file,source_locator,command,figure_or_table,paper_location,human_verification,status\nC1,Q1,better,results/metrics.json,/value,python code/run.py,fig:gain,main.tex,checked,verified\n", encoding="utf-8")
            (root / "results" / "verified_values.csv").write_text("key,value\ngain,3\n", encoding="utf-8")
            figure_fields = "figure,label,source_data,caption_insight,axes_units,color_accessibility,claim_id,question_answered,reader_takeaway,decision_relevance,status\n"
            (root / "reports" / "figure_manifest.csv").write_text(figure_fields + "figures/gain.pdf,fig:gain,results/metrics.json,gain,unit,checked,C1,does it improve,method improves,use candidate,verified\n", encoding="utf-8")
            (root / "reports" / "evidence_chain.csv").write_text("claim_id,code_or_command,source_data,data_sha256,result_file,result_sha256,verified_value_key,latex_macro,figure_label,paper_location,status\n" + f"C1,python code/run.py,data/raw.csv,{digest(source)},results/metrics.json,{digest(result)},gain,\\VerifiedValue{{gain}},fig:gain,main.tex,verified\n", encoding="utf-8")
            self.run_script("verify_evidence_chain.py", "--project-dir", str(root))
            self.run_script("verify_figure_narrative.py", "--project-dir", str(root))
            source.write_text("x\n2\n", encoding="utf-8")
            self.run_script("verify_evidence_chain.py", "--project-dir", str(root), expect=1)

    def test_decision_quality_requires_supported_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "reports").mkdir()
            (root / "results").mkdir()
            artifact = root / "results" / "challenge.json"
            artifact.write_text("{}\n", encoding="utf-8")
            (root / "reports" / "model_challenge.json").write_text(json.dumps({"status": "PASS", "errors": [], "subproblems": [{"subproblem": "Q1", "baseline_name": "mean", "candidate_name": "robust", "metric_direction": "lower", "baseline_metric": 10, "candidate_metric": 8, "minimum_relative_improvement": 0.1, "falsification_test": "holdout", "falsification_result": "pass", "result_file": "results/challenge.json", "selected_route": "candidate", "conclusion_status": "supported"}]}), encoding="utf-8")
            reports = {
                "decision_robustness.csv": ("decision_id,uncertainty_material,comparison_type,scenario_count,expected_value,worst_case_value,extreme_feasibility_rate,policy_changed,interpretation,status\n", "D1,true,robust,3,8,10,1,false,stable,verified\n"),
                "implementation_readiness.csv": ("decision_id,implementation_steps,required_inputs,execution_cost,execution_time,interpretability,extreme_feasibility_rate,failure_mode,contingency,paper_location,status\n", "D1,steps,inputs,low,1h,rule,1,timeout,baseline,main.tex,verified\n"),
                "fallback_plan.csv": ("subproblem,model_family,failure_mode,trigger,primary_route,fallback_route,boundary_statement,result_file,paper_location,status\n", "Q1,optimization,timeout,60s,robust,mean,limited,results/challenge.json,main.tex,verified\n"),
                "causal_claims.csv": ("claim_id,claim_type,estimand,causal_graph,confounders,counterfactual,identification_strategy,diagnostic,limitation,paper_location,status\n", ""),
            }
            for name, (header, row) in reports.items():
                (root / "reports" / name).write_text(header + row, encoding="utf-8")
            self.run_script("verify_decision_quality.py", "--project-dir", str(root))
            (root / "reports" / "decision_robustness.csv").write_text(reports["decision_robustness.csv"][0] + "D1,true,expected,1,8,10,1,false,weak,verified\n", encoding="utf-8")
            self.run_script("verify_decision_quality.py", "--project-dir", str(root), expect=1)

    def test_page_checklist_blocks_missing_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "reports").mkdir()
            (root / "reports" / "page_readability_checklist.csv").write_text("page,abstract_density,formula_first_definition,figure_legibility,blank_space,table_break,appendix_boundary,reference_consistency,reviewer,status\n1,pass,pass,pass,pass,pass,pass,pass,reviewer,pass\n", encoding="utf-8")
            self.run_script("verify_page_readability.py", "--project-dir", str(root), expect=1)


if __name__ == "__main__":
    unittest.main()
