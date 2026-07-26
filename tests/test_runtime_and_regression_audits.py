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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RuntimeAndRegressionAuditTests(unittest.TestCase):
    def run_script(self, name: str, *args: str, expect: int = 0) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / name), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(result.returncode, expect, result.stdout + result.stderr)

    def test_runtime_probe_records_observed_package_state(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.run_script(
                "probe_runtime_capabilities.py", "--project-dir", str(root),
                "--require", "linear_programming",
            )
            report = json.loads((root / "reports" / "runtime_capabilities.json").read_text(encoding="utf-8"))
            self.assertEqual(report["required_profiles"], ["linear_programming"])
            self.assertEqual(report["packages"][0]["package"], "scipy")

    def test_cache_audit_binds_hashes_and_time_order(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / "data" / "raw" / "events.csv"
            cache = root / "data" / "processed" / "daily.csv"
            source.parent.mkdir(parents=True)
            cache.parent.mkdir(parents=True)
            source.write_text("date,value\n2024-01-01,1\n", encoding="utf-8")
            cache.write_text("date,total\n2024-01-01,1\n", encoding="utf-8")
            manifest = root / "reports" / "cache_manifest.json"
            manifest.parent.mkdir()
            manifest.write_text(json.dumps({
                "schema_version": 1,
                "source": {"path": "data/raw/events.csv", "sha256": sha256(source)},
                "cache": {"path": "data/processed/daily.csv", "sha256": sha256(cache), "aggregation_rule": "daily sum"},
                "time_split": {"training_end": "2024-01-31", "target_start": "2024-02-01"},
            }), encoding="utf-8")
            self.run_script("verify_data_cache.py", "--project-dir", str(root), "--manifest", "reports/cache_manifest.json")
            cache.write_text("changed\n", encoding="utf-8")
            self.run_script("verify_data_cache.py", "--project-dir", str(root), "--manifest", "reports/cache_manifest.json", expect=1)

    def test_template_audit_requires_review_of_prefilled_values(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            template = root / "data" / "raw" / "template.csv"
            template.parent.mkdir(parents=True)
            template.write_text("id,value\n", encoding="utf-8")
            self.run_script("verify_result_template.py", "--project-dir", str(root), "--template", "data/raw/template.csv")
            template.write_text("id,value\n1,2\n", encoding="utf-8")
            self.run_script("verify_result_template.py", "--project-dir", str(root), "--template", "data/raw/template.csv", expect=2)
            self.run_script("verify_result_template.py", "--project-dir", str(root), "--template", "data/raw/template.csv", "--allow-prefilled")

    def test_private_rubric_emits_hashes_not_evidence_content(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            evidence: list[str] = []
            dimensions = ("input_audit", "feasibility", "reproducibility", "writing", "visual_communication")
            for dimension in dimensions:
                path = root / "reports" / f"{dimension}.json"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps({"status": "PASS", "private_note": "do not expose"}), encoding="utf-8")
                evidence.extend(["--evidence", f"{dimension}=reports/{dimension}.json"])
            self.run_script("score_private_regression.py", "--private-root", str(root), "--case-id", "case-a", *evidence)
            report = json.loads((root / "regression_rubric.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "PASS")
            self.assertNotIn("private_note", json.dumps(report, ensure_ascii=False))
            self.assertEqual(len(report["dimensions"]), 5)

    def test_private_rubric_accepts_evidence_located_defect_log(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            evidence: list[str] = []
            dimensions = ("input_audit", "feasibility", "reproducibility", "writing", "visual_communication")
            for dimension in dimensions:
                path = root / "reports" / f"{dimension}.json"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps({"status": "PASS"}), encoding="utf-8")
                evidence.extend(["--evidence", f"{dimension}=reports/{dimension}.json"])
            log = root / "reports" / "defects.csv"
            log.write_text(
                "dimension,category,severity,artifact_locator,status\n"
                "writing,unsupported_figure,major,paper/main.tex:fig-2,open\n",
                encoding="utf-8",
            )
            self.run_script(
                "score_private_regression.py", "--private-root", str(root),
                "--case-id", "case-a", *evidence,
                "--defect-log", "reports/defects.csv",
            )
            report = json.loads((root / "regression_rubric.json").read_text(encoding="utf-8"))
            self.assertEqual(report["defect_category_counts"], {"unsupported_figure": 1})


if __name__ == "__main__":
    unittest.main()
