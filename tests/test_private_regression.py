from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "prepare_private_regression.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PrivateRegressionTests(unittest.TestCase):
    def run_script(self, *args: str, expect: int = 0) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(result.returncode, expect, result.stdout + result.stderr)
        return result

    def test_inventory_discovers_cases_and_marks_generated_paths(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            corpus = root / "corpus"
            case = corpus / "2021" / "A"
            (case / "code").mkdir(parents=True)
            (case / "CUMCM2021-A.pdf").write_bytes(b"statement")
            (case / "attachment.csv").write_text("x\n1\n", encoding="utf-8")
            (case / "code" / "solve.py").write_text("print(1)\n", encoding="utf-8")
            out = root / "inventory.json"
            self.run_script(
                "inventory", "--corpus-root", str(corpus), "--out", str(out),
                "--hash-candidates",
            )
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], 1)
            self.assertEqual(payload["cases"][0]["id"], "historical-2021-a")
            self.assertFalse(payload["cases"][0]["inventory_truncated"])
            self.assertEqual(payload["cases"][0]["skipped_risk_directories"], ["code"])
            self.assertIn("generated_or_solution_directory", payload["cases"][0]["source_tree_risks"])
            safe_candidate = next(
                item for item in payload["cases"][0]["candidates"] if item["path"] == "attachment.csv"
            )
            self.assertEqual(safe_candidate["sha256"], sha256(case / "attachment.csv"))

    def test_prepare_copies_only_explicit_safe_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            corpus = root / "corpus"
            source = corpus / "2022" / "B"
            source.mkdir(parents=True)
            (source / "statement.pdf").write_bytes(b"statement")
            (source / "data.csv").write_text("x,y\n1,2\n", encoding="utf-8")
            private = root / "private"
            private.mkdir()
            manifest = private / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "cases": [{
                            "id": "historical-2022-b",
                            "enabled": True,
                            "source_dir": "2022/B",
                            "allowed_inputs": ["statement.pdf", "data.csv"],
                            "acknowledged_risks": [],
                        }],
                    }
                ),
                encoding="utf-8",
            )
            out = private / "prepare.json"
            self.run_script(
                "prepare",
                "--corpus-root", str(corpus),
                "--private-root", str(private),
                "--manifest", str(manifest),
                "--out", str(out),
            )
            copied = private / "inputs" / "historical-2022-b" / "data.csv"
            self.assertTrue(copied.is_file())
            self.assertEqual(sha256(copied), sha256(source / "data.csv"))
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "PASS")
            self.assertEqual(payload["counts"]["prepared"], 1)

    def test_prepare_rejects_path_escape_and_unacknowledged_result_name(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            corpus = root / "corpus"
            source = corpus / "2023" / "C"
            source.mkdir(parents=True)
            (source / "result.xlsx").write_bytes(b"workbook")
            private = root / "private"
            private.mkdir()
            manifest = private / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "cases": [{
                            "id": "historical-2023-c",
                            "enabled": True,
                            "source_dir": "2023/C",
                            "allowed_inputs": ["../escape.csv", "result.xlsx"],
                            "acknowledged_risks": [],
                        }],
                    }
                ),
                encoding="utf-8",
            )
            out = private / "prepare.json"
            self.run_script(
                "prepare",
                "--corpus-root", str(corpus),
                "--private-root", str(private),
                "--manifest", str(manifest),
                "--out", str(out),
                expect=1,
            )
            errors = json.loads(out.read_text(encoding="utf-8"))["errors"]
            self.assertTrue(any("unsafe" in item for item in errors))
            self.assertTrue(any("result-named" in item for item in errors))

    def test_prepare_rejects_contaminated_tree_without_acknowledgement(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            corpus = root / "corpus"
            source = corpus / "2024" / "A"
            (source / "code").mkdir(parents=True)
            (source / "statement.pdf").write_bytes(b"statement")
            (source / "code" / "solution.py").write_text("print(1)\n", encoding="utf-8")
            private = root / "private"
            private.mkdir()
            manifest = private / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "cases": [{
                            "id": "historical-2024-a",
                            "enabled": True,
                            "source_dir": "2024/A",
                            "allowed_inputs": ["statement.pdf"],
                            "acknowledged_risks": [],
                        }],
                    }
                ),
                encoding="utf-8",
            )
            out = private / "prepare.json"
            self.run_script(
                "prepare",
                "--corpus-root", str(corpus),
                "--private-root", str(private),
                "--manifest", str(manifest),
                "--out", str(out),
                expect=1,
            )
            errors = json.loads(out.read_text(encoding="utf-8"))["errors"]
            self.assertTrue(any("contaminated" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
