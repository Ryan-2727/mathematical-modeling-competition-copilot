from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_model_reasoning_core.py"


class ModelReasoningCoreTests(unittest.TestCase):
    def run_script(self, root: Path, expect: int = 0) -> dict[str, object]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--project-dir", str(root)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(result.returncode, expect, result.stdout + result.stderr)
        return json.loads((root / "reports" / "model_reasoning_core.json").read_text(encoding="utf-8"))

    @staticmethod
    def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def fixture(self, root: Path, *, independent: bool = True, material: bool = False) -> None:
        reports, results = root / "reports", root / "results"
        reports.mkdir(); results.mkdir()
        (results / "primary.json").write_text("{}\n", encoding="utf-8")
        (results / "check.json").write_text("{}\n", encoding="utf-8")
        (results / "verified_values.csv").write_text(
            "key,value,value_type,unit,source_file,source_sha256,source_locator,source_kind,justification\n",
            encoding="utf-8",
        )
        model_fields = "subproblem,model_level,parent_model,baseline,candidate,added_mechanism,mechanism_fit,assumptions,new_parameters,expected_diagnostic_signature,failure_test,validation_cost,identifiability_status,selected,selection_evidence,status".split(",")
        self.write_csv(reports / "model_decision_log.csv", model_fields, [
            {"subproblem":"Q1","model_level":"C0","parent_model":"none","baseline":"naive","candidate":"naive","added_mechanism":"none","mechanism_fit":"reference","assumptions":"stationary","new_parameters":"none","expected_diagnostic_signature":"reference","failure_test":"error>1","validation_cost":"low","identifiability_status":"PASS","selected":"false","selection_evidence":"results/primary.json","status":"verified"},
            {"subproblem":"Q1","model_level":"C2","parent_model":"naive","baseline":"naive","candidate":"joint physical","added_mechanism":"observation bias","mechanism_fit":"condition residual","assumptions":"shared target","new_parameters":"offset","expected_diagnostic_signature":"condition bias decreases","failure_test":"bias unchanged","validation_cost":"medium","identifiability_status":"PASS","selected":"true","selection_evidence":"results/primary.json","status":"verified"},
        ])
        parameter_fields = "subproblem,model_id,parameter,symbol,role,unit,scope,source,bounds,identifiability_status,claim_boundary,status".split(",")
        self.write_csv(reports / "parameter_registry.csv", parameter_fields, [
            {"subproblem":"Q1","model_id":"joint physical","parameter":"target","symbol":"theta","role":"shared","unit":"m","scope":"all conditions","source":"data","bounds":"0..10","identifiability_status":"PASS","claim_boundary":"supported","status":"verified"},
            {"subproblem":"Q1","model_id":"joint physical","parameter":"offset","symbol":"b","role":"nuisance","unit":"signal","scope":"per condition","source":"data","bounds":"-1..1","identifiability_status":"PASS","claim_boundary":"supported","status":"verified"},
        ])
        route_fields = "subproblem,route_id,route_role,principle,data_representation,failure_mode,result_file,result_value,tolerance,comparison_status,limitation,status".split(",")
        check_principle = "feature invariant" if independent else "nonlinear fit"
        check_representation = "frequency peaks" if independent else "raw curve"
        self.write_csv(reports / "independent_routes.csv", route_fields, [
            {"subproblem":"Q1","route_id":"fit","route_role":"primary","principle":"nonlinear fit","data_representation":"raw curve","failure_mode":"local optimum","result_file":"results/primary.json","result_value":"1.00","tolerance":"0.05","comparison_status":"agree","limitation":"none","status":"verified"},
            {"subproblem":"Q1","route_id":"feature","route_role":"independent_check","principle":check_principle,"data_representation":check_representation,"failure_mode":"peak detection","result_file":"results/check.json","result_value":"1.02","tolerance":"0.05","comparison_status":"agree","limitation":"resolution","status":"verified"},
        ])
        reconciliation_fields = "subproblem,comparison_id,primary_route,comparison_route,primary_value,comparison_value,tolerance,disagreement_material,investigation_step,cause,resolution,claim_action,evidence_file,status".split(",")
        self.write_csv(reports / "result_reconciliation.csv", reconciliation_fields, [
            {"subproblem":"Q1","comparison_id":"R1","primary_route":"fit","comparison_route":"feature","primary_value":"1.00","comparison_value":"1.20" if material else "1.02","tolerance":"0.05","disagreement_material":str(material).lower(),"investigation_step":"parameter sharing" if material else "not_applicable","cause":"invalid sharing" if material else "within tolerance","resolution":"partial pooling" if material else "retain primary","claim_action":"admit","evidence_file":"results/check.json","status":"verified"}
        ])
        (reports / "joint_inference_design.json").write_text(json.dumps({"applicable": False, "reason": "single condition", "subproblems": []}), encoding="utf-8")

    def test_passes_cross_domain_reasoning_contract(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw); self.fixture(root)
            payload = self.run_script(root)
            self.assertEqual(payload["status"], "PASS")
            self.assertEqual(payload["counts"]["models"], 2)

    def test_rejects_same_objective_as_independent_route(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw); self.fixture(root, independent=False)
            payload = self.run_script(root, expect=1)
            self.assertTrue(any("two-difference" in error for error in payload["errors"]))

    def test_rejects_unresolved_material_disagreement(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw); self.fixture(root, material=True)
            payload = self.run_script(root, expect=1)
            self.assertTrue(any("admits a material disagreement" in error for error in payload["errors"]))

    def test_rejects_selected_nonidentifiable_model(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw); self.fixture(root)
            path = root / "reports" / "model_decision_log.csv"
            path.write_text(path.read_text(encoding="utf-8").replace("PASS,true,results/primary.json", "FAIL,true,results/primary.json"), encoding="utf-8")
            payload = self.run_script(root, expect=1)
            self.assertTrue(any("selected model has identifiability FAIL" in error for error in payload["errors"]))

    def test_complementary_checks_are_conditional(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw); self.fixture(root)
            path = root / "reports" / "independent_routes.csv"
            with path.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            rows[1]["route_role"] = "complementary_check"
            rows.append({**rows[1], "route_id": "bounds", "principle": "known limit", "data_representation": "parameter range", "failure_mode": "weak external bound"})
            self.write_csv(path, list(rows[0]), rows)
            payload = self.run_script(root, expect=2)
            self.assertEqual(payload["status"], "LIMITED")
            self.assertEqual(payload["reasoning_status"], "CONDITIONAL")

    def test_conditional_identifiability_requires_and_propagates_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw); self.fixture(root)
            path = root / "reports" / "parameter_registry.csv"
            original = path.read_text(encoding="utf-8")
            path.write_text(original.replace("PASS,supported,verified", "CONDITIONAL,fixed calibration,verified", 1), encoding="utf-8")
            payload = self.run_script(root, expect=2)
            self.assertEqual(payload["reasoning_status"], "CONDITIONAL")
            path.write_text(path.read_text(encoding="utf-8").replace("CONDITIONAL,fixed calibration", "CONDITIONAL,"), encoding="utf-8")
            failed = self.run_script(root, expect=1)
            self.assertTrue(any("CONDITIONAL lacks claim_boundary" in error for error in failed["errors"]))

    def test_joint_inference_requires_registered_parameters_and_competing_strategies(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw); self.fixture(root)
            joint = {
                "applicable": True,
                "reason": "repeated measurements",
                "subproblems": [{
                    "subproblem": "Q1",
                    "conditions": ["a", "b"],
                    "shared_parameters": ["target"],
                    "condition_specific_parameters": [],
                    "nuisance_parameters": ["offset"],
                    "separate_fit_baseline": "separate fits",
                    "joint_objective": "shared target objective",
                    "strategies_compared": ["separate", "joint_shared"],
                    "comparison_result": "joint removes condition drift",
                    "sharing_verdict": "accepted",
                    "evidence_file": "results/primary.json",
                    "status": "verified",
                }],
            }
            path = root / "reports" / "joint_inference_design.json"
            path.write_text(json.dumps(joint), encoding="utf-8")
            self.assertEqual(self.run_script(root)["status"], "PASS")
            joint["subproblems"][0]["shared_parameters"] = ["unknown"]
            joint["subproblems"][0]["strategies_compared"] = ["joint_shared"]
            path.write_text(json.dumps(joint), encoding="utf-8")
            failed = self.run_script(root, expect=1)
            self.assertTrue(any("unregistered parameters" in error for error in failed["errors"]))
            self.assertTrue(any("compare separate and joint" in error for error in failed["errors"]))


if __name__ == "__main__":
    unittest.main()
