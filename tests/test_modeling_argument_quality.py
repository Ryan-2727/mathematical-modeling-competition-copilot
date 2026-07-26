from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_modeling_argument_quality.py"


class ModelingArgumentQualityTests(unittest.TestCase):
    def run_script(self, root: Path, expect: int = 0) -> None:
        result = subprocess.run([sys.executable, str(SCRIPT), "--project-dir", str(root)], capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(result.returncode, expect, result.stdout + result.stderr)

    def write_fixture(self, root: Path, checks: int = 2) -> None:
        reports, results = root / "reports", root / "results"
        reports.mkdir()
        results.mkdir()
        artifact = results / "q1.json"
        artifact.write_text("{}\n", encoding="utf-8")
        (results / "verified_values.csv").write_text("key,value\nanswer,1\n", encoding="utf-8")
        (reports / "semantic_audit.csv").write_text("semantic_id,dataset,field,raw_representation,semantic_type,decision_impact,evidence,alternative_treatment,sensitivity_needed,used_by,status\nS1,data.csv,capacity,0,structural_zero,exclude,definition,missing,true,Q1,verified\n", encoding="utf-8")
        (reports / "mechanism_audit.json").write_text(json.dumps({"subproblems": [{"subproblem": "Q1", "mechanism": "flow balance", "assumptions": "capacity fixed", "semantic_ids": ["S1"], "falsifiable_implication": "conservation", "result_file": "results/q1.json", "status": "verified"}]}), encoding="utf-8")
        (reports / "validation_design.csv").write_text("subproblem,truth_availability,validation_strategy,independent_checks,primary_metric,baseline_or_invariant,split_or_scenario,acceptance_criterion,limitation,result_file,status\n" + f"Q1,no_ground_truth,invariant+small_case,{checks},residual,conservation,stress,residual=0,no labels,results/q1.json,verified\n", encoding="utf-8")
        (reports / "conclusion_map.csv").write_text("subproblem,question,answer_or_recommendation,decisive_value_key,method_rationale_location,validation_location,limitation_location,figure_or_table,paper_location,status\nQ1,what,choose A,answer,main.tex:method,main.tex:validation,main.tex:limits,Table 1,main.tex:q1,verified\n", encoding="utf-8")
        (reports / "innovation_ledger.csv").write_text("subproblem,baseline,problem_specific_change,mechanism_target,added_assumption,incremental_cost,comparison_metric,baseline_value,innovation_value,metric_direction,predeclared_minimum_improvement,relative_improvement,validation_artifact,claim_boundary,status\nQ1,mean,coupling repair,flow,none,low,residual,10,8,lower,0.1,0.2,results/q1.json,supported,verified\n", encoding="utf-8")

    def test_passes_complete_semantic_validation_conclusion_and_innovation_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.write_fixture(root)
            self.run_script(root)
            payload = json.loads((root / "reports" / "modeling_argument_quality.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "PASS")

    def test_blocks_single_check_without_ground_truth(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.write_fixture(root, checks=1)
            self.run_script(root, expect=1)
            errors = json.loads((root / "reports" / "modeling_argument_quality.json").read_text(encoding="utf-8"))["errors"]
            self.assertTrue(any("at least two independent checks" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
