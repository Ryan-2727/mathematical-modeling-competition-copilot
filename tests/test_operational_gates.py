from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class OperationalGateTests(unittest.TestCase):
    def run_script(
        self, name: str, *args: str, expect: int = 0
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / name), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(result.returncode, expect, result.stdout + result.stderr)
        return result

    def create_rule_lock(self, root: Path, profile: str = "mcm-icm-current") -> None:
        snapshot = root / "reports" / "official-rules.html"
        snapshot.write_text("<html>official contest rules</html>\n", encoding="utf-8")
        rules = (
            [
                "paper_format=PDF",
                "paper_size_limit_mb=25",
                "extra_files_allowed=false",
                "total_page_limit=25",
                "ai_policy=disclose",
                "anonymity=control-number-only",
            ]
            if profile.startswith("mcm")
            else [
                "paper_format=PDF",
                "paper_size_limit_mb=20",
                "support_archive=ZIP-or-RAR",
                "main_text_page_limit=30",
                "ai_policy=disclose",
                "anonymity=no-identity",
            ]
        )
        command = [
            "create",
            "--project-dir",
            str(root),
            "--contest",
            "MCM/ICM" if profile.startswith("mcm") else "CUMCM",
            "--year",
            "2027" if profile.startswith("mcm") else "2026",
            "--profile",
            profile,
            "--valid-through",
            "2099-12-31",
            "--source-url",
            "https://example.org/official-rules",
            "--snapshot",
            "reports/official-rules.html",
        ]
        for rule in rules:
            command.extend(["--rule", rule])
        self.run_script("lock_contest_rules.py", *command)

    def test_rule_lock_and_setup_controller_detect_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "数学建模 Skill"
            self.run_script(
                "init_contest.py",
                "--project-dir",
                str(root),
                "--contest",
                "MCM/ICM",
                "--year",
                "2027",
                "--mode",
                "training",
            )
            self.create_rule_lock(root)
            phase_report = root / "reports" / "phase_setup.json"
            self.run_script(
                "contestctl.py",
                "check",
                "--project-dir",
                str(root),
                "--phase",
                "setup",
                "--out",
                str(phase_report),
            )
            self.assertEqual(
                json.loads(phase_report.read_text(encoding="utf-8"))["status"], "PASS"
            )
            (root / "reports" / "official-rules.html").write_text(
                "changed\n", encoding="utf-8"
            )
            self.run_script(
                "contestctl.py",
                "check",
                "--project-dir",
                str(root),
                "--phase",
                "setup",
                "--out",
                str(phase_report),
                expect=1,
            )
            self.run_script(
                "lock_contest_rules.py",
                "validate",
                "--project-dir",
                str(root),
                expect=1,
            )
            self.assertEqual(
                json.loads(
                    (root / "reports" / "rules_lock_verification.json").read_text(
                        encoding="utf-8"
                    )
                )["status"],
                "FAIL",
            )
            self.run_script(
                "contestctl.py",
                "check",
                "--project-dir",
                str(root),
                "--phase",
                "setup",
                "--out",
                str(root / "rules.lock.json"),
                expect=1,
            )

    def test_rule_lock_rejects_output_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.run_script(
                "init_contest.py",
                "--project-dir",
                str(root),
                "--contest",
                "MCM/ICM",
                "--year",
                "2027",
                "--mode",
                "training",
            )
            self.create_rule_lock(root)
            self.run_script(
                "lock_contest_rules.py",
                "validate",
                "--project-dir",
                str(root),
                "--out",
                str(root / "rules.lock.json"),
                expect=1,
            )
            hardlink = root / "reports" / "rules-hardlink.json"
            os.link(root / "rules.lock.json", hardlink)
            self.run_script(
                "contestctl.py",
                "check",
                "--project-dir",
                str(root),
                "--phase",
                "setup",
                "--out",
                str(hardlink),
                expect=1,
            )
            snapshot_alias = root / "reports" / "snapshot-hardlink.json"
            os.link(root / "reports" / "official-rules.html", snapshot_alias)
            self.run_script(
                "lock_contest_rules.py",
                "validate",
                "--project-dir",
                str(root),
                "--out",
                str(snapshot_alias),
                expect=1,
            )
            self.run_script(
                "lock_contest_rules.py",
                "validate",
                "--project-dir",
                str(root),
                "--out",
                str(hardlink),
                expect=1,
            )

    def test_freeze_reports_require_input_bindings(self) -> None:
        if str(SCRIPTS) not in sys.path:
            sys.path.insert(0, str(SCRIPTS))
        spec = importlib.util.spec_from_file_location(
            "contestctl_under_test", SCRIPTS / "contestctl.py"
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "reports").mkdir()
            (root / "support").mkdir()
            (root / "support" / "reproduction_commands.txt").write_text(
                "python solve.py\n", encoding="utf-8"
            )
            reproduction = root / "reports" / "reproduction_report.json"
            reproduction.write_text(
                json.dumps({
                    "status": "PASS",
                    "errors": [],
                    "reproduction_commands_sha256": sha256(
                        root / "support" / "reproduction_commands.txt"
                    ),
                }),
                encoding="utf-8",
            )
            status, _ = module.report_status(
                root, "reports/reproduction_report.json", reproduction
            )
            self.assertEqual(status, "FAIL")
            arbitrary = root / "arbitrary.txt"
            arbitrary.write_text("not a submission\n", encoding="utf-8")
            submission = root / "reports" / "submission_manifest.json"
            submission.write_text(
                json.dumps({
                    "status": "PASS",
                    "errors": [],
                    "artifacts": [{
                        "source_path": str(arbitrary),
                        "sha256": sha256(arbitrary),
                    }],
                }),
                encoding="utf-8",
            )
            status, _ = module.report_status(
                root, "reports/submission_manifest.json", submission
            )
            self.assertEqual(status, "FAIL")
            anonymity = root / "reports" / "anonymity_scan.txt"
            anonymity.write_text(
                "STATUS PASS\n"
                f"ROOT {root}\n"
                f"INPUT_FINGERPRINT {module.tree_fingerprint(root, anonymity)}\n",
                encoding="utf-8",
            )
            status, _ = module.report_status(
                root, "reports/anonymity_scan.txt", anonymity
            )
            self.assertEqual(status, "FAIL")

    def test_safe_file_accepts_windows_case_variation_after_resolution(self) -> None:
        if str(SCRIPTS) not in sys.path:
            sys.path.insert(0, str(SCRIPTS))
        spec = importlib.util.spec_from_file_location(
            "contestctl_case_test", SCRIPTS / "contestctl.py"
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        root = Path("C:/Users/RUNNER~1/AppData/Local/Temp/tmp65jb7jz")
        child = Path("c:/users/runner~1/appdata/local/temp/TMP65JB7JZ/support/input.txt")
        outside = Path("c:/users/runner~1/appdata/local/temp/TMP65JB7JZ-other/input.txt")
        with mock.patch.object(module.os.path, "normcase", side_effect=str.casefold):
            self.assertTrue(module.is_within_root(root, child))
            self.assertFalse(module.is_within_root(root, outside))

    def test_abstract_quality_requires_answer_validation_and_task_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            abstract = root / "paper" / "sections" / "abstract.tex"
            abstract.parent.mkdir(parents=True)
            repeated = (
                "问题一建立回归模型并得到误差为3.2\\%，结果表明方案有效，"
                "通过留出检验和敏感性分析验证稳定性。"
                "问题二建立优化算法并得到成本下降12.5\\%，最终建议采用稳健方案，"
                "通过扰动检验确认结论。"
            )
            abstract.write_text(repeated * 6, encoding="utf-8")
            report = root / "reports" / "abstract.json"
            self.run_script(
                "verify_abstract_quality.py",
                "--project-dir",
                str(root),
                "--expected-subproblems",
                "2",
                "--out",
                str(report),
            )
            self.assertEqual(json.loads(report.read_text(encoding="utf-8"))["status"], "PASS")
            abstract.write_text("问题一：我们建立了一个模型。", encoding="utf-8")
            self.run_script(
                "verify_abstract_quality.py",
                "--project-dir",
                str(root),
                "--expected-subproblems",
                "2",
                "--out",
                str(report),
                expect=1,
            )

    def test_manuscript_quality_uses_figure_manifest_and_logs(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paper = root / "paper"
            reports = root / "reports"
            (paper / "figures").mkdir(parents=True)
            reports.mkdir()
            (paper / "figures" / "trend.pdf").write_bytes(b"%PDF-1.4\nfixture")
            (root / "results").mkdir()
            (root / "results" / "trend.csv").write_text(
                "time,error\n1,2\n", encoding="utf-8"
            )
            (paper / "main.tex").write_text(
                "\\documentclass{article}\n\\usepackage{graphicx}\n"
                "\\begin{document}\nFigure~\\ref{fig:trend} shows the result.\n"
                "\\begin{figure}\\includegraphics{figures/trend.pdf}"
                "\\caption{Trend with uncertainty.}\\label{fig:trend}\\end{figure}\n"
                "\\end{document}\n",
                encoding="utf-8",
            )
            with (reports / "figure_manifest.csv").open(
                "w", encoding="utf-8", newline=""
            ) as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "figure",
                        "label",
                        "source_data",
                        "caption_insight",
                        "axes_units",
                        "color_accessibility",
                        "status",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "figure": "figures/trend.pdf",
                        "label": "fig:trend",
                        "source_data": "results/trend.csv",
                        "caption_insight": "uncertainty narrows",
                        "axes_units": "time (h), error (%)",
                        "color_accessibility": "grayscale checked",
                        "status": "verified",
                    }
                )
            out = reports / "manuscript.json"
            self.run_script(
                "verify_manuscript_quality.py",
                "--project-dir",
                str(root),
                "--out",
                str(out),
            )
            self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["status"], "PASS")
            (paper / "main.log").write_text(
                "LaTeX Warning: Reference `bad' undefined.\n", encoding="utf-8"
            )
            self.run_script(
                "verify_manuscript_quality.py",
                "--project-dir",
                str(root),
                "--out",
                str(out),
                expect=1,
            )

    def test_manuscript_quality_rejects_basename_only_manifest_match(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper" / "figures").mkdir(parents=True)
            (root / "reports").mkdir()
            (root / "results").mkdir()
            (root / "paper" / "figures" / "trend.pdf").write_bytes(b"%PDF fixture")
            (root / "results" / "trend.csv").write_text("x,y\n1,2\n", encoding="utf-8")
            (root / "paper" / "main.tex").write_text(
                "\\documentclass{article}\\usepackage{graphicx}\\begin{document}"
                "See Figure~\\ref{fig:trend}."
                "\\begin{figure}\\includegraphics{figures/trend.pdf}"
                "\\caption{Trend.}\\label{fig:trend}\\end{figure}\\end{document}",
                encoding="utf-8",
            )
            with (root / "reports" / "figure_manifest.csv").open(
                "w", encoding="utf-8", newline=""
            ) as handle:
                writer = csv.DictWriter(handle, fieldnames=[
                    "figure", "label", "source_data", "caption_insight",
                    "axes_units", "color_accessibility", "status",
                ])
                writer.writeheader()
                writer.writerow({
                    "figure": "old/trend.png",
                    "label": "fig:trend",
                    "source_data": "results/trend.csv",
                    "caption_insight": "trend",
                    "axes_units": "x, y",
                    "color_accessibility": "checked",
                    "status": "verified",
                })
            self.run_script(
                "verify_manuscript_quality.py",
                "--project-dir",
                str(root),
                "--out",
                str(root / "reports" / "manuscript.json"),
                expect=1,
            )

    def test_strict_bibliography_metadata_and_passages(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper").mkdir()
            (root / "reports" / "bibliography_metadata").mkdir(parents=True)
            (root / "reports" / "source_passages").mkdir()
            keys = [f"ref{i}" for i in range(10)]
            (root / "paper" / "main.tex").write_text(
                "\\documentclass{article}\\begin{document}"
                + "".join(
                    f"Evidence claim {i} \\label{{claim:{i}}} \\cite{{{key}}}."
                    for i, key in enumerate(keys)
                )
                + "\\end{document}\n",
                encoding="utf-8",
            )
            (root / "reports" / "claims.csv").write_text(
                "claim_id,subproblem,claim,source_file,source_locator,command,"
                "figure_or_table,paper_location,human_verification,status\n"
                + "".join(
                    f"C{i},Q1,Evidence claim {i},results/source.csv,row {i},"
                    f"python code/run.py,tab:{i},claim:{i},manually checked,verified\n"
                    for i in range(10)
                ),
                encoding="utf-8",
            )
            fields = [
                "citation_key",
                "title",
                "authors",
                "year",
                "venue",
                "doi_or_url",
                "verification_source",
                "verified_at",
                "scholar_query",
                "scholar_checked_at",
                "scholar_status",
                "metadata_snapshot",
                "metadata_sha256",
                "retraction_status",
                "retraction_checked_at",
                "claim_supported",
                "source_locator",
                "supporting_passage",
                "supporting_passage_sha256",
                "evidence_role",
                "claim_id",
                "paper_location",
                "relevance_justification",
                "removal_impact",
                "status",
            ]
            rows = []
            for i, key in enumerate(keys):
                title = f"Verified Reference {i}"
                doi = f"10.1000/test.{i}"
                metadata = root / "reports" / "bibliography_metadata" / f"{key}.json"
                metadata.write_text(
                    json.dumps(
                        {
                            "message": {
                                "title": [title],
                                "DOI": doi,
                                "issued": {"date-parts": [[2020 + i]]},
                                "author": [{"given": "Test", "family": "Author"}],
                                "container-title": ["Test Journal"],
                            }
                        }
                    ),
                    encoding="utf-8",
                )
                passage = root / "reports" / "source_passages" / f"{key}.txt"
                passage.write_text(
                    f"Recorded supporting passage for claim {i}.\n", encoding="utf-8"
                )
                rows.append(
                    {
                        "citation_key": key,
                        "title": title,
                        "authors": "Test Author",
                        "year": str(2020 + i),
                        "venue": "Test Journal",
                        "doi_or_url": doi,
                        "verification_source": (
                            "https://api.crossref.org/works/" + doi
                        ),
                        "verified_at": "2026-07-25",
                        "scholar_query": (
                            "https://scholar.google.com/scholar?q="
                            + title.replace(" ", "+")
                        ),
                        "scholar_checked_at": "2026-07-25",
                        "scholar_status": "found",
                        "metadata_snapshot": metadata.relative_to(root).as_posix(),
                        "metadata_sha256": sha256(metadata),
                        "retraction_status": "not_retracted",
                        "retraction_checked_at": "2026-07-25",
                        "claim_supported": f"claim {i}",
                        "source_locator": "methods, paragraph 1",
                        "supporting_passage": passage.relative_to(root).as_posix(),
                        "supporting_passage_sha256": sha256(passage),
                        "evidence_role": "method",
                        "claim_id": f"C{i}",
                        "paper_location": f"claim:{i}",
                        "relevance_justification": f"Provides the method evidence required by claim {i}",
                        "removal_impact": f"Claim {i} would lose its methodological source",
                        "status": "verified",
                    }
                )
            with (root / "reports" / "bibliography.csv").open(
                "w", encoding="utf-8", newline=""
            ) as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
            out = root / "reports" / "bibliography_verification.json"
            self.run_script(
                "verify_bibliography_metadata.py",
                "--project-dir",
                str(root),
                "--out",
                str(out),
            )
            self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["status"], "PASS")
            rows[0]["paper_location"] = "claim:missing"
            with (root / "reports" / "bibliography.csv").open(
                "w", encoding="utf-8", newline=""
            ) as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
            self.run_script(
                "verify_bibliography_metadata.py",
                "--project-dir",
                str(root),
                "--out",
                str(out),
                expect=1,
            )
            rows[0]["paper_location"] = "claim:0"
            rows[0]["verification_source"] = "official: attacker controlled"
            rows[0]["scholar_query"] = (
                "https://scholar.google.evil.example/scholar?q="
                + rows[0]["title"].replace(" ", "+")
            )
            with (root / "reports" / "bibliography.csv").open(
                "w", encoding="utf-8", newline=""
            ) as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
            self.run_script(
                "verify_bibliography_metadata.py",
                "--project-dir",
                str(root),
                "--out",
                str(out),
                expect=1,
            )
            rows[0]["verification_source"] = (
                "https://api.crossref.org/works/" + rows[0]["doi_or_url"]
            )
            rows[0]["scholar_query"] = (
                "https://scholar.google.com/scholar?q="
                + rows[0]["title"].replace(" ", "+")
            )
            with (root / "reports" / "bibliography.csv").open(
                "w", encoding="utf-8", newline=""
            ) as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
            metadata = root / rows[0]["metadata_snapshot"]
            metadata.write_text("{}\n", encoding="utf-8")
            self.run_script(
                "verify_bibliography_metadata.py",
                "--project-dir",
                str(root),
                "--out",
                str(out),
                expect=1,
            )

    def test_strict_bibliography_rejects_missing_scholar_and_author_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper").mkdir()
            (root / "reports").mkdir()
            (root / "paper" / "main.tex").write_text(
                "\\documentclass{article}\\begin{document}\\cite{x}\\end{document}",
                encoding="utf-8",
            )
            with (root / "reports" / "bibliography.csv").open(
                "w", encoding="utf-8", newline=""
            ) as handle:
                writer = csv.DictWriter(handle, fieldnames=sorted({
                    "citation_key", "title", "authors", "year", "venue",
                    "doi_or_url", "metadata_snapshot", "metadata_sha256",
                    "retraction_status", "retraction_checked_at",
                    "claim_supported", "source_locator", "supporting_passage",
                    "supporting_passage_sha256", "status",
                }))
                writer.writeheader()
                writer.writerow({field: "x" for field in writer.fieldnames})
            self.run_script(
                "verify_bibliography_metadata.py",
                "--project-dir",
                str(root),
                "--minimum-references",
                "1",
                "--out",
                str(root / "reports" / "bibliography_verification.json"),
                expect=1,
            )

    def test_delivery_and_official_submission_are_separate(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper").mkdir()
            (root / "delivery").mkdir()
            (root / "official-submission").mkdir()
            (root / "paper" / "main.pdf").write_bytes(b"%PDF-1.4\npaper")
            (root / "paper-source.zip").write_bytes(b"source")
            (root / "support.zip").write_bytes(b"support")
            (root / "contest_manifest.json").write_text(
                json.dumps({"submission_profile": "mcm-icm-current"}),
                encoding="utf-8",
            )
            delivery_sources = [
                ("paper.pdf", "paper_pdf", "paper/main.pdf"),
                ("paper-source.zip", "latex_source", "paper-source.zip"),
                ("support.zip", "support_archive", "support.zip"),
            ]
            with (root / "delivery" / "manifest.csv").open(
                "w", encoding="utf-8", newline=""
            ) as handle:
                writer = csv.DictWriter(
                    handle, fieldnames=["path", "role", "source_path", "sha256"]
                )
                writer.writeheader()
                for target, role, source in delivery_sources:
                    content = (root / source).read_bytes()
                    (root / "delivery" / target).write_bytes(content)
                    writer.writerow(
                        {
                            "path": target,
                            "role": role,
                            "source_path": source,
                            "sha256": hashlib.sha256(content).hexdigest(),
                        }
                    )
            official = root / "official-submission" / "1234567.pdf"
            official.write_bytes((root / "paper" / "main.pdf").read_bytes())
            with (root / "official-submission" / "manifest.csv").open(
                "w", encoding="utf-8", newline=""
            ) as handle:
                writer = csv.DictWriter(
                    handle, fieldnames=["path", "role", "source_path", "sha256"]
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "path": official.name,
                        "role": "paper_pdf",
                        "source_path": "paper/main.pdf",
                        "sha256": sha256(official),
                    }
                )
            out = root / "reports" / "delivery_profiles.json"
            self.run_script(
                "verify_delivery_profiles.py",
                "--project-dir",
                str(root),
                "--out",
                str(out),
            )
            self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["status"], "PASS")
            with (root / "official-submission" / "manifest.csv").open(
                "a", encoding="utf-8", newline=""
            ) as handle:
                handle.write(
                    f"support.zip,support_archive,support.zip,{sha256(root / 'support.zip')}\n"
                )
            (root / "official-submission" / "support.zip").write_bytes(
                (root / "support.zip").read_bytes()
            )
            self.run_script(
                "verify_delivery_profiles.py",
                "--project-dir",
                str(root),
                "--out",
                str(out),
                expect=1,
            )

    def test_cumcm_official_submission_rejects_other_role(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            for folder in ("paper", "delivery", "official-submission"):
                (root / folder).mkdir()
            sources = {
                "paper/main.pdf": b"%PDF-1.4\npaper",
                "paper-source.zip": b"source",
                "support.zip": b"support",
                "notes.txt": b"notes",
            }
            for relative, content in sources.items():
                (root / relative).write_bytes(content)
            (root / "contest_manifest.json").write_text(
                json.dumps({"submission_profile": "cumcm-current"}),
                encoding="utf-8",
            )
            delivery_rows = [
                ("paper.pdf", "paper_pdf", "paper/main.pdf"),
                ("paper-source.zip", "latex_source", "paper-source.zip"),
                ("support.zip", "support_archive", "support.zip"),
            ]
            with (root / "delivery" / "manifest.csv").open(
                "w", encoding="utf-8", newline=""
            ) as handle:
                writer = csv.DictWriter(
                    handle, fieldnames=["path", "role", "source_path", "sha256"]
                )
                writer.writeheader()
                for target, role, source in delivery_rows:
                    content = sources[source]
                    (root / "delivery" / target).write_bytes(content)
                    writer.writerow({
                        "path": target,
                        "role": role,
                        "source_path": source,
                        "sha256": hashlib.sha256(content).hexdigest(),
                    })
            official_rows = [
                ("paper.pdf", "paper_pdf", "paper/main.pdf"),
                ("notes.txt", "other", "notes.txt"),
            ]
            with (root / "official-submission" / "manifest.csv").open(
                "w", encoding="utf-8", newline=""
            ) as handle:
                writer = csv.DictWriter(
                    handle, fieldnames=["path", "role", "source_path", "sha256"]
                )
                writer.writeheader()
                for target, role, source in official_rows:
                    content = sources[source]
                    (root / "official-submission" / target).write_bytes(content)
                    writer.writerow({
                        "path": target,
                        "role": role,
                        "source_path": source,
                        "sha256": hashlib.sha256(content).hexdigest(),
                    })
            self.run_script(
                "verify_delivery_profiles.py",
                "--project-dir",
                str(root),
                "--out",
                str(root / "reports" / "delivery_profiles.json"),
                expect=1,
            )


if __name__ == "__main__":
    unittest.main()
