from __future__ import annotations

import binascii
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import verify_pdf_visual
from run_reproduction import parse_argv


class ArtifactQATests(unittest.TestCase):
    def run_script(
        self,
        name: str,
        *args: str,
        expect: int = 0,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / name), *args],
            capture_output=True,
            text=True,
            env=env,
        )
        self.assertEqual(result.returncode, expect, result.stdout + result.stderr)
        return result

    @staticmethod
    def write_png(path: Path, metadata: str) -> None:
        def chunk(kind: bytes, data: bytes) -> bytes:
            body = kind + data
            return (
                len(data).to_bytes(4, "big")
                + body
                + binascii.crc32(body).to_bytes(4, "big")
            )

        scanline = b"\x00\xff\xff\xff"
        path.write_bytes(
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00")
            + chunk(b"tEXt", b"Comment\x00" + metadata.encode("utf-8"))
            + chunk(b"IDAT", zlib.compress(scanline))
            + chunk(b"IEND", b"")
        )

    def test_pdf_qa_reports_limited_or_fail_when_poppler_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            pdf = Path(raw) / "paper.pdf"
            pdf.write_bytes(b"%PDF-1.4\nfixture")
            with mock.patch.object(verify_pdf_visual.shutil, "which", return_value=None):
                limited = verify_pdf_visual.verify_pdf(pdf)
                strict = verify_pdf_visual.verify_pdf(pdf, strict_tools=True)
            self.assertEqual(limited["status"], "LIMITED")
            self.assertIn("pdfinfo", limited["limitations"][0])
            self.assertEqual(strict["status"], "FAIL")
            self.assertTrue(any("Poppler" in item for item in strict["errors"]))

    def test_pdf_qa_checks_markers_contents_metadata_and_rendering(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            pdf = root / "paper.pdf"
            pdf.write_bytes(b"%PDF-1.4\nfixture")

            def fake_run(command: list[str]) -> subprocess.CompletedProcess[str]:
                if command[0] == "pdfinfo":
                    return subprocess.CompletedProcess(
                        command,
                        0,
                        stdout=(
                            "Pages: 2\n"
                            "Page size: 595.28 x 841.89 pts (A4)\n"
                            "Author: Example University Team\n"
                            "Creator: XeLaTeX\n"
                        ),
                        stderr="",
                    )
                if command[0] == "pdftotext":
                    return subprocess.CompletedProcess(
                        command,
                        0,
                        stdout=(
                            "Wrong first page marker with enough explanatory text\n"
                            "Figure 1: Isolated workflow caption\n"
                            "\f目录\n"
                            "See Table 2 for supporting values that are not captioned.\n\f"
                        ),
                        stderr="",
                    )
                if command[0] == "pdftoppm":
                    prefix = Path(command[-1])
                    prefix.with_name(prefix.name + "-1.png").write_bytes(b"png1")
                    prefix.with_name(prefix.name + "-2.png").write_bytes(b"png2")
                    return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
                if command[0] == "pdfimages":
                    return subprocess.CompletedProcess(
                        command,
                        0,
                        stdout=(
                            "page num type width height color comp bpc enc interp "
                            "object ID x-ppi y-ppi size ratio\n"
                            "1 0 image 600 400 rgb 3 8 image no 12 0 72 72 10K 1.0%\n"
                        ),
                        stderr="",
                    )
                raise AssertionError(command)

            with (
                mock.patch.object(
                    verify_pdf_visual.shutil,
                    "which",
                    side_effect=lambda name: name,
                ),
                mock.patch.object(
                    verify_pdf_visual,
                    "run_command",
                    side_effect=fake_run,
                ),
            ):
                report = verify_pdf_visual.verify_pdf(
                    pdf,
                    page_size="A4",
                    sparse_threshold=10,
                    first_page_markers=["Summary Sheet"],
                    strict_tools=True,
                )
            self.assertEqual(report["status"], "FAIL")
            self.assertTrue(any("Author metadata" in item for item in report["errors"]))
            self.assertTrue(any("first page" in item for item in report["errors"]))
            self.assertTrue(any("table-of-contents" in item for item in report["errors"]))
            self.assertEqual(report["checks"]["render"]["rendered_pages"], 2)
            link_issues = report["checks"]["figure_table_links"]["issues"]
            self.assertEqual(
                {issue["type"] for issue in link_issues},
                {"caption_without_body_reference", "reference_without_caption"},
            )
            self.assertEqual(
                report["checks"]["raster_assets"]["low_resolution"][0]["x_ppi"],
                72.0,
            )
            self.assertTrue(any("below 150 PPI" in item for item in report["warnings"]))

    def test_pdf_qa_accepts_linked_artifacts_and_print_quality_raster(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            pdf = root / "paper.pdf"
            pdf.write_bytes(b"%PDF-1.4\nfixture")

            def fake_run(command: list[str]) -> subprocess.CompletedProcess[str]:
                if command[0] == "pdfinfo":
                    return subprocess.CompletedProcess(
                        command,
                        0,
                        stdout="Pages: 1\nPage size: 595.28 x 841.89 pts (A4)\n",
                        stderr="",
                    )
                if command[0] == "pdftotext":
                    return subprocess.CompletedProcess(
                        command,
                        0,
                        stdout=(
                            "Summary Sheet with sufficient explanatory text\n"
                            "Table of Contents\n"
                            "Figure 1: Model workflow\n"
                            "As shown in Figure 1, the workflow is reproducible.\n"
                            "Table 2: Verified results\n"
                            "Table 2 summarizes the values supporting the conclusion.\n\f"
                        ),
                        stderr="",
                    )
                if command[0] == "pdftoppm":
                    prefix = Path(command[-1])
                    prefix.with_name(prefix.name + "-1.png").write_bytes(b"png")
                    return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
                if command[0] == "pdfimages":
                    return subprocess.CompletedProcess(
                        command,
                        0,
                        stdout=(
                            "page num type width height color comp bpc enc interp "
                            "object ID x-ppi y-ppi size ratio\n"
                            "1 0 image 1800 1200 rgb 3 8 image no 12 0 300 300 1M 1.0%\n"
                        ),
                        stderr="",
                    )
                raise AssertionError(command)

            with (
                mock.patch.object(
                    verify_pdf_visual.shutil,
                    "which",
                    side_effect=lambda name: name,
                ),
                mock.patch.object(
                    verify_pdf_visual,
                    "run_command",
                    side_effect=fake_run,
                ),
            ):
                report = verify_pdf_visual.verify_pdf(
                    pdf,
                    page_size="A4",
                    first_page_markers=["Summary Sheet"],
                    forbidden_terms=[],
                    strict_tools=True,
                )
            self.assertEqual(report["status"], "PASS", report)
            self.assertEqual(report["checks"]["figure_table_links"]["issues"], [])
            self.assertEqual(report["checks"]["raster_assets"]["low_resolution"], [])
            self.assertEqual(report["warnings"], [])

    def test_pdfimages_missing_is_limited_or_strict_failure(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            pdf = root / "paper.pdf"
            pdf.write_bytes(b"%PDF-1.4\nfixture")

            def fake_run(command: list[str]) -> subprocess.CompletedProcess[str]:
                if command[0] == "pdfinfo":
                    return subprocess.CompletedProcess(
                        command,
                        0,
                        stdout="Pages: 1\nPage size: 595.28 x 841.89 pts (A4)\n",
                        stderr="",
                    )
                if command[0] == "pdftotext":
                    return subprocess.CompletedProcess(
                        command,
                        0,
                        stdout="Summary Sheet with enough text for a complete first page.\n\f",
                        stderr="",
                    )
                if command[0] == "pdftoppm":
                    prefix = Path(command[-1])
                    prefix.with_name(prefix.name + "-1.png").write_bytes(b"png")
                    return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
                raise AssertionError(command)

            def which(name: str) -> str | None:
                return None if name == "pdfimages" else name

            with (
                mock.patch.object(
                    verify_pdf_visual.shutil,
                    "which",
                    side_effect=which,
                ),
                mock.patch.object(
                    verify_pdf_visual,
                    "run_command",
                    side_effect=fake_run,
                ),
            ):
                limited = verify_pdf_visual.verify_pdf(pdf)
                strict = verify_pdf_visual.verify_pdf(pdf, strict_tools=True)
            self.assertEqual(limited["status"], "LIMITED")
            self.assertTrue(
                any("pdfimages" in item for item in limited["limitations"])
            )
            self.assertEqual(strict["status"], "FAIL")
            self.assertTrue(any("pdfimages" in item for item in strict["errors"]))

    def test_anonymity_scan_finds_png_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.write_png(root / "figure.png", "Created at Example University")
            out = root / "anonymity.txt"
            self.run_script(
                "anonymity_scan.py",
                "--root",
                str(root),
                "--out",
                str(out),
                expect=1,
            )
            report = out.read_text(encoding="utf-8")
            self.assertIn("STATUS FAIL", report)
            self.assertIn("IMAGE_METADATA", report)
            self.assertIn("not a full guarantee", report)

    def test_anonymity_requested_ocr_is_limited_when_tool_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.write_png(root / "figure.png", "benign metadata")
            out = root / "anonymity.txt"
            env = os.environ.copy()
            env["PATH"] = ""
            self.run_script(
                "anonymity_scan.py",
                "--root",
                str(root),
                "--out",
                str(out),
                "--ocr",
                expect=2,
                env=env,
            )
            report = out.read_text(encoding="utf-8")
            self.assertIn("STATUS LIMITED", report)
            self.assertIn("tesseract unavailable", report)

    def test_reproduction_uses_clean_argv_runs_and_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "project"
            root.mkdir()
            (root / "input.txt").write_text("source", encoding="utf-8")
            out = Path(raw) / "reports" / "reproduction.json"
            command = json.dumps(
                [
                    sys.executable,
                    "-c",
                    "from pathlib import Path; "
                    "Path('result.txt').write_text('stable', encoding='utf-8')",
                ]
            )
            self.run_script(
                "run_reproduction.py",
                "--project-dir",
                str(root),
                "--argv-json",
                command,
                "--expected",
                "result.txt",
                "--repeat",
                "2",
                "--out",
                str(out),
            )
            report = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "PASS")
            self.assertFalse(report["shell"])
            self.assertTrue(all(item["clean_copy"] for item in report["runs"]))
            self.assertTrue(report["comparisons"][0]["match"])
            for run in report["runs"]:
                self.assertTrue(Path(run["stdout_log"]).is_file())
                self.assertTrue(Path(run["stderr_log"]).is_file())

    def test_reproduction_csv_tolerance_and_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "project"
            root.mkdir()
            csv_out = Path(raw) / "csv-report.json"
            csv_command = json.dumps(
                [
                    sys.executable,
                    "-c",
                    "import os; from pathlib import Path; "
                    "i=int(os.environ['REPRODUCTION_RUN_INDEX']); "
                    "Path('result.csv').write_text("
                    "'metric,value\\nscore,'+str(1+i*1e-8)+'\\n', encoding='utf-8')",
                ]
            )
            self.run_script(
                "run_reproduction.py",
                "--project-dir",
                str(root),
                "--argv-json",
                csv_command,
                "--expected",
                "result.csv",
                "--repeat",
                "2",
                "--csv-atol",
                "0.000001",
                "--out",
                str(csv_out),
            )
            csv_report = json.loads(csv_out.read_text(encoding="utf-8"))
            self.assertEqual(csv_report["status"], "PASS")
            self.assertEqual(csv_report["comparisons"][0]["method"], "csv")

            mismatch_out = Path(raw) / "hash-report.json"
            hash_command = json.dumps(
                [
                    sys.executable,
                    "-c",
                    "import os; from pathlib import Path; "
                    "Path('result.txt').write_text("
                    "os.environ['REPRODUCTION_RUN_INDEX'], encoding='utf-8')",
                ]
            )
            self.run_script(
                "run_reproduction.py",
                "--project-dir",
                str(root),
                "--argv-json",
                hash_command,
                "--expected",
                "result.txt",
                "--repeat",
                "2",
                "--out",
                str(mismatch_out),
                expect=1,
            )
            mismatch = json.loads(mismatch_out.read_text(encoding="utf-8"))
            self.assertEqual(mismatch["status"], "FAIL")
            self.assertTrue(any("SHA-256 differs" in item for item in mismatch["errors"]))

    def test_shell_execution_requires_explicit_opt_in(self) -> None:
        argv, shell, source = parse_argv(
            None,
            None,
            f'{sys.executable} -c "print(1)"',
            False,
        )
        self.assertIsInstance(argv, list)
        self.assertFalse(shell)
        self.assertIn("without a shell", source)
        command, shell, source = parse_argv(None, None, "echo explicit", True)
        self.assertEqual(command, "echo explicit")
        self.assertTrue(shell)
        self.assertEqual(source, "explicit shell command")


if __name__ == "__main__":
    unittest.main()
