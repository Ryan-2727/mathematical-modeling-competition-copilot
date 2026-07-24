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
sys.path.insert(0, str(SCRIPTS))

from aggregate_reviewer_reports import aggregate_reviews
from paper_corpus_metrics import generate_manifest, parse_pdfinfo, validate_manifest


def review(role: str, score: float, confidence: float) -> dict[str, object]:
    return {
        "review_id": f"{role}-review-01",
        "reviewer_role": role,
        "score": score,
        "confidence": confidence,
        "artifact_locators": [f"paper/main.tex:{role}"],
        "strongest_objection": {
            "summary": f"{role} objection",
            "severity": "major",
            "artifact_locator": f"reports/{role}_evidence.json",
            "rerun_required": role == "evidence",
        },
        "accepted_limitations": [],
    }


class CorpusManifestTests(unittest.TestCase):
    def test_example_manifest_is_portable_and_complete(self) -> None:
        manifest = json.loads(
            (ROOT / "assets" / "corpus-manifest.example.json").read_text(
                encoding="utf-8"
            )
        )
        serialized = json.dumps(manifest, ensure_ascii=False)
        self.assertNotRegex(serialized, r"[A-Za-z]:[\\/]")
        for entry in manifest["papers"]:
            self.assertTrue(entry["id"])
            self.assertTrue(entry["source_category"])
            self.assertTrue(entry["inspection_date"])
            self.assertRegex(entry["sha256"], r"^[0-9a-f]{64}$")
            self.assertIn("pages", entry)
            self.assertIn("page_size_pt", entry)
            self.assertIsInstance(entry["limitations"], list)

    def test_generate_manifest_uses_portable_ids_and_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            corpus = Path(raw) / "corpus"
            paper = corpus / "2025" / "A001.pdf"
            paper.parent.mkdir(parents=True)
            payload = b"portable-corpus-fixture"
            paper.write_bytes(payload)

            manifest = generate_manifest(
                pdf_dir=corpus,
                recursive=True,
                corpus_id="cumcm-training",
                source_category="official-excellent-paper",
                inspection_date="2026-07-24",
                pdfinfo_tool=None,
            )

            self.assertEqual(manifest["status"], "LIMITED")
            self.assertEqual(manifest["pdf_count"], 1)
            entry = manifest["papers"][0]
            self.assertEqual(entry["id"], "cumcm-training/2025/A001")
            self.assertEqual(entry["relative_path"], "2025/A001.pdf")
            self.assertEqual(entry["source_category"], "official-excellent-paper")
            self.assertEqual(entry["inspection_date"], "2026-07-24")
            self.assertEqual(entry["sha256"], hashlib.sha256(payload).hexdigest())
            self.assertIsNone(entry["pages"])
            self.assertIsNone(entry["page_size_pt"])
            self.assertTrue(entry["limitations"])
            self.assertNotIn(str(corpus), json.dumps(manifest, ensure_ascii=False))

    def test_validate_manifest_reports_missing_tool_and_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            corpus = Path(raw) / "corpus"
            corpus.mkdir()
            paper = corpus / "A001.pdf"
            paper.write_bytes(b"first")
            manifest = generate_manifest(
                pdf_dir=corpus,
                recursive=False,
                corpus_id="training",
                source_category="user-provided-reference",
                inspection_date="2026-07-24",
                pdfinfo_tool=None,
            )

            limited = validate_manifest(manifest, corpus, pdfinfo_tool=None)
            self.assertEqual(limited["status"], "LIMITED")
            self.assertEqual(limited["errors"], [])
            self.assertTrue(limited["limitations"])

            paper.write_bytes(b"changed")
            failed = validate_manifest(manifest, corpus, pdfinfo_tool=None)
            self.assertEqual(failed["status"], "FAIL")
            self.assertTrue(any("SHA-256 mismatch" in error for error in failed["errors"]))

    def test_cli_generates_and_validates_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "sample.pdf").write_bytes(b"not-a-real-pdf")
            manifest_path = root / "manifest.json"
            generate = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "paper_corpus_metrics.py"),
                    "--pdf-dir",
                    str(corpus),
                    "--corpus-id",
                    "portable-training",
                    "--source-category",
                    "user-provided-reference",
                    "--inspection-date",
                    "2026-07-24",
                    "--out",
                    str(manifest_path),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(generate.returncode, 0, generate.stdout + generate.stderr)

            report_path = root / "validation.json"
            validate = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "paper_corpus_metrics.py"),
                    "--mode",
                    "validate",
                    "--pdf-dir",
                    str(corpus),
                    "--manifest",
                    str(manifest_path),
                    "--out",
                    str(report_path),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(validate.returncode, 2, validate.stdout + validate.stderr)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "LIMITED")
            self.assertEqual(report["errors"], [])

    def test_parse_pdfinfo_page_metrics(self) -> None:
        pages, page_size = parse_pdfinfo(
            "Pages:          37\nPage size:      252 x 356.04 pts\n"
        )
        self.assertEqual(pages, 37)
        self.assertEqual(page_size, {"width_pt": 252.0, "height_pt": 356.04})


class ReviewerAggregationTests(unittest.TestCase):
    def test_aggregate_reports_disagreement_veto_limitations_and_rerun(self) -> None:
        model = review("model", 4, 0.8)
        evidence = review("evidence", 2, 0.9)
        writing = review("writing", 5, 0.7)
        model["strongest_objection"]["severity"] = "veto"
        writing["accepted_limitations"] = [
            {
                "summary": "One appendix figure remains dense.",
                "artifact_locator": "paper/main.tex:appendix-figure",
                "rerun_required": False,
            }
        ]

        result = aggregate_reviews([model, evidence, writing])

        self.assertEqual(result["status"], "VETO")
        self.assertEqual(result["review_count"], 3)
        self.assertEqual(result["disagreement"]["score_range"], 3.0)
        self.assertTrue(result["disagreement"]["material"])
        self.assertEqual(len(result["veto_findings"]), 1)
        self.assertEqual(len(result["accepted_limitations"]), 1)
        self.assertTrue(result["rerun_required"])
        self.assertNotIn("award_prediction", json.dumps(result))

    def test_aggregate_rejects_missing_locator_and_award_prediction(self) -> None:
        reports = [
            review("model", 4, 0.8),
            review("evidence", 4, 0.8),
            review("writing", 4, 0.8),
        ]
        reports[0]["artifact_locators"] = []
        with self.assertRaisesRegex(ValueError, "artifact_locators"):
            aggregate_reviews(reports)

        reports[0] = review("model", 4, 0.8)
        reports[0]["award_prediction"] = "national first prize"
        with self.assertRaisesRegex(ValueError, "award prediction"):
            aggregate_reviews(reports)

    def test_cli_reads_exactly_three_review_files(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = []
            for role in ("model", "evidence", "writing"):
                path = root / f"{role}.json"
                payload = review(role, 4, 0.8)
                payload["strongest_objection"]["severity"] = "none"
                payload["strongest_objection"]["rerun_required"] = False
                path.write_text(
                    json.dumps(payload, ensure_ascii=False),
                    encoding="utf-8",
                )
                paths.append(path)
            out = root / "aggregate.json"
            command = [sys.executable, str(SCRIPTS / "aggregate_reviewer_reports.py")]
            for path in paths:
                command.extend(["--review", str(path)])
            command.extend(["--out", str(out)])

            completed = subprocess.run(command, capture_output=True, text=True)

            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            result = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "PASS")
            self.assertFalse(result["rerun_required"])


if __name__ == "__main__":
    unittest.main()
