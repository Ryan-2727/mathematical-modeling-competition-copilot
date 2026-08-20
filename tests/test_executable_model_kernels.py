from __future__ import annotations

import importlib.util
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
LIBRARY = ROOT / "assets" / "model-library" / "cumcm-bc-model-cards.json"


class ExecutableModelKernelTests(unittest.TestCase):
    def run_script(self, name: str, *args: str, expect: int = 0) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / name), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(result.returncode, expect, result.stdout + result.stderr)
        return result

    def test_five_model_cards_link_real_kernels_and_fixtures(self) -> None:
        payload = json.loads(LIBRARY.read_text(encoding="utf-8"))
        bundled = [card for card in payload["cards"] if card["implementation"]["bundled"]]
        self.assertEqual(len(bundled), 5)
        for card in bundled:
            implementation = card["implementation"]
            self.assertTrue((ROOT / implementation["dispatcher"]).is_file())
            self.assertTrue((ROOT / implementation["fixture"]).is_file())
            self.assertEqual(implementation["fallback_backend"], "stdlib")
            self.assertEqual(
                set(implementation["supported_backends"]), {"stdlib", "scientific"}
            )
        self.run_script("verify_model_library.py")

    def test_stdlib_hidden_truth_and_metamorphic_regression(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            out = Path(raw) / "kernel-regression.json"
            self.run_script(
                "run_model_kernel_regression.py",
                "--backend",
                "stdlib",
                "--out",
                str(out),
            )
            report = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "PASS", report)
            self.assertEqual(report["kernel_count"], 5)
            self.assertGreaterEqual(report["check_count"], 20)
            self.assertEqual({record["status"] for record in report["checks"]}, {"PASS"})

    def test_dispatcher_binds_input_and_does_not_hide_backend(self) -> None:
        fixture = json.loads(
            (
                ROOT
                / "assets"
                / "model-library"
                / "fixtures"
                / "bearing-only-localization.json"
            ).read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / "input.json"
            out = root / "output.json"
            source.write_text(json.dumps(fixture["base_input"]), encoding="utf-8")
            self.run_script(
                "run_model_kernel.py",
                "--kernel",
                "bearing-only-localization",
                "--input",
                str(source),
                "--output",
                str(out),
                "--backend",
                "stdlib",
            )
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "PASS")
            self.assertEqual(payload["backend_requested"], "stdlib")
            self.assertEqual(payload["backend_used"], "stdlib")
            self.assertEqual(payload["input_locator"], "input.json")
            self.assertNotIn(str(root), json.dumps(payload, ensure_ascii=False))
            self.assertRegex(payload["input_sha256"], r"^[0-9a-f]{64}$")
            self.assertLess(payload["diagnostics"]["position_error_proxy"], 1e-10)

    def test_project_usage_binds_kernel_output_and_synthetic_regression(self) -> None:
        fixture_path = (
            ROOT
            / "assets"
            / "model-library"
            / "fixtures"
            / "bearing-only-localization.json"
        )
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw)
            (project / "code").mkdir()
            (project / "results").mkdir()
            (project / "reports").mkdir()
            source = project / "code" / "bearing-input.json"
            output = project / "results" / "bearing-output.json"
            regression = project / "reports" / "kernel-regression.json"
            source.write_text(json.dumps(fixture["base_input"]), encoding="utf-8")
            self.run_script(
                "run_model_kernel.py",
                "--kernel",
                "bearing-only-localization",
                "--input",
                str(source),
                "--output",
                str(output),
                "--backend",
                "stdlib",
            )
            self.run_script(
                "run_model_kernel_regression.py",
                "--backend",
                "stdlib",
                "--out",
                str(regression),
            )
            fields = [
                "model_id",
                "card_id",
                "kernel_id",
                "used",
                "backend",
                "input_file",
                "input_sha256",
                "output_file",
                "output_sha256",
                "synthetic_regression_report",
                "synthetic_regression_sha256",
                "adaptation_note",
                "status",
            ]
            with (project / "reports" / "model_kernel_usage.csv").open(
                "w", encoding="utf-8", newline=""
            ) as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerow(
                    {
                        "model_id": "bearing-baseline",
                        "card_id": "bearing-only-localization",
                        "kernel_id": "bearing-only-localization",
                        "used": "yes",
                        "backend": "stdlib",
                        "input_file": "code/bearing-input.json",
                        "input_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                        "output_file": "results/bearing-output.json",
                        "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                        "synthetic_regression_report": "reports/kernel-regression.json",
                        "synthetic_regression_sha256": hashlib.sha256(
                            regression.read_bytes()
                        ).hexdigest(),
                        "adaptation_note": "Synthetic checks validate the reference implementation only; contest assumptions are audited separately.",
                        "status": "verified",
                    }
                )
            report = project / "reports" / "model_kernel_evidence.json"
            self.run_script(
                "verify_model_kernel_evidence.py",
                "--project-dir",
                str(project),
                "--out",
                str(report),
            )
            self.assertEqual(
                json.loads(report.read_text(encoding="utf-8"))["status"], "PASS"
            )
            output.write_text("{}\n", encoding="utf-8")
            self.run_script(
                "verify_model_kernel_evidence.py",
                "--project-dir",
                str(project),
                "--out",
                str(report),
                expect=1,
            )

    @unittest.skipUnless(
        importlib.util.find_spec("numpy") is not None
        and importlib.util.find_spec("scipy") is not None,
        "scientific backend requires NumPy and SciPy",
    )
    def test_scientific_hidden_truth_and_metamorphic_regression(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            out = Path(raw) / "kernel-regression-scientific.json"
            self.run_script(
                "run_model_kernel_regression.py",
                "--backend",
                "scientific",
                "--out",
                str(out),
            )
            report = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "PASS", report)
            self.assertEqual(report["backends_used"], ["scientific"])


if __name__ == "__main__":
    unittest.main()
