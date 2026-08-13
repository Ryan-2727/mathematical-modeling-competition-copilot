from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from verify_latex_compatibility import source_fingerprint


class ScriptTests(unittest.TestCase):
    def run_script(self, name: str, *args: str, expect: int = 0) -> subprocess.CompletedProcess[str]:
        result = subprocess.run([sys.executable, str(SCRIPTS / name), *args], capture_output=True, text=True)
        self.assertEqual(result.returncode, expect, result.stdout + result.stderr)
        return result

    def test_init_and_ai_log(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "project"
            self.run_script("init_contest.py", "--project-dir", str(root), "--contest", "CUMCM", "--year", "2026", "--mode", "training")
            manifest = json.loads((root / "contest_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["mode"], "training")
            for filename in (
                "model_decision_log.csv",
                "parameter_registry.csv",
                "independent_routes.csv",
                "result_reconciliation.csv",
                "joint_inference_design.json",
                "stress_tests.csv",
                "units.csv",
                "reviewer_scorecard.csv",
                "milestones.csv",
                "paper_depth_plan.csv",
            ):
                self.assertTrue((root / "reports" / filename).is_file(), filename)
            for filename in (
                root / "reports" / "bibliography.csv",
                root / "reports" / "figure_manifest.csv",
                root / "reports" / "model_validation.json",
                root / "results" / "verified_values.csv",
                root / "plan.md",
                root / "todo.md",
                root / "rules.lock.json",
                root / "paper" / "main.tex",
                root / "paper" / "references.bib",
                root / "paper" / ".latexmkrc",
                root / "paper" / ".vscode" / "settings.json",
                root / "paper" / ".vscode" / "extensions.json",
                root / "paper" / "code" / "main.py",
                root / "paper" / "sections" / "abstract.tex",
                root / "paper" / "sections" / "ai_declaration.tex",
                root / "support" / "README.md",
                root / "support" / "reproduction_commands.txt",
                root / "support" / "materials_manifest.csv",
                root / "support" / "data_inventory.csv",
                root / "environment" / "README.md",
                root / "delivery" / "manifest.csv",
                root / "official-submission" / "manifest.csv",
            ):
                self.assertTrue(filename.is_file(), str(filename))
            main_tex = (root / "paper" / "main.tex").read_text(encoding="utf-8")
            self.assertLess(
                main_tex.index(r"\input{sections/ai_declaration}"),
                main_tex.index(r"\bibliography{references}"),
            )
            log = root / "reports" / "ai_usage_log.jsonl"
            self.run_script("log_ai_use.py", "--log", str(log), "--tool", "TestAI", "--version", "1", "--purpose", "outline", "--stage", "writing", "--prompt-summary", "test", "--adopted", "partial", "--human-verification", "reviewed")
            self.assertIn("TestAI", log.read_text(encoding="utf-8"))

    def test_init_selects_mcm_icm_template_and_profile(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "project"
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
            manifest = json.loads((root / "contest_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["latex_template"], "mcm-icm")
            self.assertEqual(manifest["submission_profile"], "mcm-icm-current")
            self.assertTrue((root / "paper" / "main.tex").is_file())

    def test_skill_contract_and_invocation_gate(self) -> None:
        result = self.run_script("validate_skill_contract.py")
        self.assertIn("PASS", result.stdout)

    def test_anonymity_scan(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "note.txt").write_text("University internal draft", encoding="utf-8")
            out = root / "scan.txt"
            self.run_script("anonymity_scan.py", "--root", str(root), "--out", str(out), expect=1)
            self.assertIn("TEXT", out.read_text(encoding="utf-8"))

    def test_submission_rejects_missing_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            out = root / "manifest.json"
            self.run_script("verify_submission.py", "--paper", str(root / "missing.pdf"), "--out", str(out), expect=1)
            self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["status"], "FAIL")

    def test_ai_report_archive_and_state(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "project"
            self.run_script("init_contest.py", "--project-dir", str(root), "--contest", "CUMCM", "--year", "2026", "--mode", "training")
            log = root / "reports" / "ai_usage_log.jsonl"
            self.run_script("log_ai_use.py", "--log", str(log), "--tool", "TestAI", "--version", "1", "--purpose", "draft", "--stage", "writing", "--prompt-summary", "test", "--adopted", "yes", "--human-verification", "checked")
            report = root / "support" / "AI工具使用详情.md"
            self.run_script("render_ai_use_report.py", "--log", str(log), "--out", str(report))
            archive = root / "support.zip"
            archive_manifest = root / "support_manifest.json"
            self.run_script("build_support_archive.py", "--project-dir", str(root), "--include", "support/AI工具使用详情.md", "--out", str(archive), "--manifest", str(archive_manifest))
            manifest = root / "contest_manifest.json"
            self.run_script("set_submission_state.py", "--manifest", str(manifest), "--state", "verified", "--evidence", str(report))
            self.assertEqual(json.loads(manifest.read_text(encoding="utf-8"))["submission_state"], "verified")

    def test_recursive_corpus_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "corpus" / "2025"
            root.mkdir(parents=True)
            (root / "A001.pdf").write_bytes(b"not-a-real-pdf")
            out = root.parent.parent / "metrics.json"
            self.run_script("paper_corpus_metrics.py", "--pdf-dir", str(root.parent.parent), "--recursive", "--out", str(out))
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["pdf_count"], 1)
            self.assertTrue(data["papers"][0]["relative_path"].replace("\\", "/").endswith("corpus/2025/A001.pdf"))

    def test_paper_depth_bounds_and_subproblem_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "project"
            reports = root / "reports"
            reports.mkdir(parents=True)
            header = "section,role,planned_pages,actual_pages,required_content,evidence,status\n"
            rows = [
                "摘要,abstract,1,1,answers,main.tex:abstract,complete",
                "重述,restatement,1,1,scope,main.tex:restatement,complete",
                "分析,analysis,2,2,rationale,main.tex:analysis,complete",
                "假设符号,assumptions_notation,1,1,definitions,main.tex:notation,complete",
                "问题一,subproblem,4,4,seven-part-chain,main.tex:q1,complete",
                "问题二,subproblem,4,4,seven-part-chain,main.tex:q2,complete",
                "检验,validation,2,2,robustness,main.tex:validation,complete",
                "结论,conclusion,1,1,direct-answers,main.tex:conclusion,complete",
                "文献,references,1,1,verified-sources,main.tex:references,complete",
            ]
            (reports / "paper_depth_plan.csv").write_text(
                header + "\n".join(rows) + "\n", encoding="utf-8"
            )
            out = reports / "paper_depth.json"
            common = (
                "--project-dir", str(root), "--main-text-pages", "28",
                "--appendix-pages", "12", "--minimum-main-text-pages", "24",
                "--minimum-total-pages", "30", "--maximum-main-text-pages", "30",
                "--expected-subproblems", "2", "--out", str(out),
            )
            self.run_script("verify_paper_depth.py", *common)
            self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["status"], "PASS")
            failing = list(common)
            failing[failing.index("28")] = "20"
            self.run_script("verify_paper_depth.py", *failing)
            advisory = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(advisory["status"], "PASS")
            self.assertTrue(any("depth floor" in item for item in advisory["warnings"]))
            failing.extend(["--minimum-mode", "enforce"])
            self.run_script("verify_paper_depth.py", *failing, expect=1)
            self.assertTrue(any("depth floor" in error for error in json.loads(out.read_text(encoding="utf-8"))["errors"]))

    def test_claim_ledger_and_reproduction(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "project"
            self.run_script("init_contest.py", "--project-dir", str(root), "--contest", "CUMCM", "--year", "2026", "--mode", "training")
            (root / "results" / "answer.txt").write_text("42", encoding="utf-8")
            (root / "reports" / "claims.csv").write_text("claim_id,subproblem,claim,source_file,source_locator,command,figure_or_table,paper_location,human_verification,status\nC1,Q1,answer,results/answer.txt,line 1,python code/run.py,Table 1,Section 3,checked,verified\n", encoding="utf-8")
            (root / "reports" / "argument_coverage.csv").write_text("subproblem,need_or_mechanism,model,solution,quantified_result,interpretation,validation,status\nQ1,need,model,solve,result,meaning,check,complete\n", encoding="utf-8")
            report = root / "reports" / "evidence.json"
            self.run_script("verify_claims.py", "--project-dir", str(root), "--out", str(report))
            self.assertEqual(json.loads(report.read_text(encoding="utf-8"))["status"], "PASS")
            reproducibility = root / "reports" / "reproduce.json"
            self.run_script("run_reproduction.py", "--project-dir", str(root), "--command", f'{sys.executable} -c "open(\'results/rebuilt.txt\', \'w\').write(\'ok\')"', "--expected", "results/rebuilt.txt", "--out", str(reproducibility))
            self.assertEqual(json.loads(reproducibility.read_text(encoding="utf-8"))["status"], "PASS")

    def test_award_readiness_pass_and_missing_stress_failure(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "project"
            reports = root / "reports"
            self.run_script("init_contest.py", "--project-dir", str(root), "--contest", "CUMCM", "--year", "2026", "--mode", "training")
            (root / "results" / "q1_stress.json").write_text("{}", encoding="utf-8")
            (reports / "argument_coverage.csv").write_text(
                "subproblem,need_or_mechanism,model,solution,quantified_result,interpretation,validation,status\n"
                "Q1,mechanism,baseline plus candidate,executed,42,decision meaning,stress test,complete\n",
                encoding="utf-8",
            )
            (reports / "model_decision_log.csv").write_text(
                "subproblem,baseline,candidate,mechanism_fit,assumptions,failure_test,validation_cost,selected,selection_evidence,status\n"
                "Q1,mean model,robust model,matches outliers,independent errors,outlier injection,low,robust model,lower held-out error,complete\n",
                encoding="utf-8",
            )
            stress_header = "claim_id,subproblem,stress_type,change,acceptance_criterion,result_file,outcome,verdict,status\n"
            (reports / "stress_tests.csv").write_text(
                stress_header
                + "C1,Q1,data perturbation,inject five percent outliers,error increase below ten percent,results/q1_stress.json,eight percent increase,pass,complete\n",
                encoding="utf-8",
            )
            (reports / "units.csv").write_text(
                "symbol,meaning,unit,source,conversion,range_check,status\n"
                "x,observed quantity,kg,provided data,none,nonnegative,complete\n",
                encoding="utf-8",
            )
            score_rows = [
                f"{dimension},4,paper and result evidence,remaining objection,targeted revision,complete"
                for dimension in (
                    "assumption_rationality",
                    "model_creativity",
                    "result_correctness",
                    "writing_clarity",
                )
            ]
            (reports / "reviewer_scorecard.csv").write_text(
                "dimension,score_1_to_5,evidence,major_objection,smallest_fix,status\n"
                + "\n".join(score_rows)
                + "\n",
                encoding="utf-8",
            )
            milestones = (reports / "milestones.csv").read_text(encoding="utf-8").replace(",pending\n", ",complete\n")
            (reports / "milestones.csv").write_text(milestones, encoding="utf-8")
            out = reports / "award_readiness.json"
            self.run_script("verify_award_readiness.py", "--project-dir", str(root), "--out", str(out))
            self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["status"], "PASS")

            (reports / "stress_tests.csv").write_text(stress_header, encoding="utf-8")
            self.run_script("verify_award_readiness.py", "--project-dir", str(root), "--out", str(out), expect=1)
            failure = json.loads(out.read_text(encoding="utf-8"))
            self.assertTrue(any("does not cover subproblem Q1" in error for error in failure["errors"]))

    def test_verified_literature_and_two_part_delivery(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "project"
            self.run_script(
                "init_contest.py",
                "--project-dir", str(root),
                "--contest", "CUMCM",
                "--year", "2026",
                "--mode", "training",
            )
            keys = [f"ref{i}" for i in range(10)]
            main_tex = root / "paper" / "main.tex"
            main_tex.write_text(
                "% !TeX program = xelatex\n"
                "% !TeX encoding = UTF-8\n"
                "% !TeX root = main.tex\n"
                "% !BIB program = bibtex\n"
                "\\documentclass{article}\n\\begin{document}\n"
                f"Evidence \\cite{{{','.join(keys)}}}.\n"
                "\\bibliographystyle{plain}\n\\bibliography{references}\n"
                "\\end{document}\n",
                encoding="utf-8",
            )
            (root / "paper" / "main.pdf").write_bytes(b"%PDF-1.4\n" + b"verified build fixture\n" * 12)
            (root / "paper" / "references.bib").write_text(
                "\n".join(
                    f"@article{{{key}, title={{Verified Modeling Reference {i}}}, "
                    f"author={{Author, Test}}, journal={{Journal of Tests}}, year={{202{i % 10}}}}}"
                    for i, key in enumerate(keys)
                )
                + "\n",
                encoding="utf-8",
            )

            bibliography_path = root / "reports" / "bibliography.csv"
            bibliography_fields = [
                "citation_key", "title", "authors", "year", "venue", "doi_or_url",
                "verification_source", "verified_at", "scholar_query", "scholar_checked_at",
                "scholar_status", "claim_supported", "source_locator", "status",
            ]
            bibliography_rows = [
                {
                    "citation_key": key,
                    "title": f"Verified Modeling Reference {i}",
                    "authors": "Test Author",
                    "year": f"202{i % 10}",
                    "venue": "Journal of Tests",
                    "doi_or_url": f"https://doi.org/10.1000/test.{i}",
                    "verification_source": f"Crossref and publisher metadata record {i}",
                    "verified_at": "2026-07-17",
                    "scholar_query": f"https://scholar.google.com/scholar?q=%22Verified+Modeling+Reference+{i}%22",
                    "scholar_checked_at": "2026-07-17",
                    "scholar_status": "found",
                    "claim_supported": f"methodological claim {i}",
                    "source_locator": "abstract and methods section",
                    "status": "verified",
                }
                for i, key in enumerate(keys)
            ]
            with bibliography_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=bibliography_fields)
                writer.writeheader()
                writer.writerows(bibliography_rows)

            artifacts = {
                "code/run.py": b"print('reproduce')\n",
                "data/processed/input.csv": b"x,y\n1,2\n",
                "environment/requirements.txt": b"numpy==2.0.0\n",
                "results/summary.csv": b"metric,value\nscore,1.0\n",
            }
            for relative, content in artifacts.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            (root / "support" / "reproduction_commands.txt").write_text(
                "python code/run.py\n"
                "xelatex -interaction=nonstopmode -output-directory=paper paper/main.tex\n",
                encoding="utf-8",
            )
            categories = {
                "code/run.py": "code",
                "data/processed/input.csv": "processed-data",
                "environment/requirements.txt": "environment",
                "results/summary.csv": "result",
            }
            manifest_path = root / "support" / "materials_manifest.csv"
            with manifest_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["path", "category", "source", "license", "sha256", "included", "notes"],
                )
                writer.writeheader()
                for relative, category in categories.items():
                    writer.writerow({
                        "path": relative,
                        "category": category,
                        "source": "team-generated fixture",
                        "license": "contest-use",
                        "sha256": hashlib.sha256((root / relative).read_bytes()).hexdigest(),
                        "included": "yes",
                        "notes": "required for reproduction",
                    })
            data_path = root / "data" / "processed" / "input.csv"
            with (root / "support" / "data_inventory.csv").open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "dataset", "included_path", "source_url", "license", "version_or_date",
                        "sha256", "retrieval_command", "status",
                    ],
                )
                writer.writeheader()
                writer.writerow({
                    "dataset": "processed fixture",
                    "included_path": "data/processed/input.csv",
                    "source_url": "https://example.org/contest-data",
                    "license": "contest-use",
                    "version_or_date": "2026-07-17",
                    "sha256": hashlib.sha256(data_path.read_bytes()).hexdigest(),
                    "retrieval_command": "provided with the contest fixture",
                    "status": "included",
                })
            (root / "reports" / "latex_compatibility.json").write_text(
                json.dumps(
                    {
                        "status": "PASS",
                        "compile_backed": True,
                        "engine": "xelatex",
                        "build_driver": "latexmk",
                        "source_sha256": source_fingerprint(root / "paper"),
                        "builds": [
                            {"pdf": "main.pdf", "returncode": 0},
                            {"pdf": "build/main.pdf", "returncode": 0},
                        ],
                        "errors": [],
                        "warnings": [],
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            self.run_script(
                "build_support_archive.py",
                "--project-dir", str(root),
                "--materials-manifest", "support/materials_manifest.csv",
                "--out", str(root / "support.zip"),
                "--manifest", str(root / "support_manifest.json"),
            )
            support_manifest = json.loads((root / "support_manifest.json").read_text(encoding="utf-8"))
            self.assertTrue(all(isinstance(path, str) for path in support_manifest["files"]))
            self.assertEqual(len(support_manifest["files"]), len(support_manifest["artifacts"]))
            report = root / "reports" / "paper_delivery.json"
            self.run_script("verify_paper_delivery.py", "--project-dir", str(root), "--out", str(report))
            self.assertEqual(json.loads(report.read_text(encoding="utf-8"))["status"], "PASS")

            original_tex = main_tex.read_text(encoding="utf-8")
            main_tex.write_text(original_tex.replace(",ref9", ""), encoding="utf-8")
            self.run_script(
                "verify_paper_delivery.py", "--project-dir", str(root), "--out", str(report), expect=1
            )
            citation_failure = json.loads(report.read_text(encoding="utf-8"))
            self.assertTrue(any("at least 10" in error for error in citation_failure["errors"]))
            main_tex.write_text(original_tex, encoding="utf-8")

            bibliography_rows[0]["verification_source"] = ""
            with bibliography_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=bibliography_fields)
                writer.writeheader()
                writer.writerows(bibliography_rows)
            self.run_script(
                "verify_paper_delivery.py", "--project-dir", str(root), "--out", str(report), expect=1
            )
            source_failure = json.loads(report.read_text(encoding="utf-8"))
            self.assertTrue(any("empty required fields" in error for error in source_failure["errors"]))
            bibliography_rows[0]["verification_source"] = "Crossref and publisher metadata record 0"
            with bibliography_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=bibliography_fields)
                writer.writeheader()
                writer.writerows(bibliography_rows)

            bibliography_rows[0]["scholar_status"] = "not_found"
            with bibliography_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=bibliography_fields)
                writer.writeheader()
                writer.writerows(bibliography_rows)
            self.run_script(
                "verify_paper_delivery.py", "--project-dir", str(root), "--out", str(report), expect=1
            )
            scholar_failure = json.loads(report.read_text(encoding="utf-8"))
            self.assertTrue(any("not confirmed in Google Scholar" in error for error in scholar_failure["errors"]))
            bibliography_rows[0]["scholar_status"] = "found"
            with bibliography_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=bibliography_fields)
                writer.writeheader()
                writer.writerows(bibliography_rows)

            original_title = bibliography_rows[9]["title"]
            original_query = bibliography_rows[9]["scholar_query"]
            bibliography_rows[9]["title"] = bibliography_rows[8]["title"]
            bibliography_rows[9]["scholar_query"] = bibliography_rows[8]["scholar_query"]
            with bibliography_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=bibliography_fields)
                writer.writeheader()
                writer.writerows(bibliography_rows)
            self.run_script(
                "verify_paper_delivery.py", "--project-dir", str(root), "--out", str(report), expect=1
            )
            duplicate_failure = json.loads(report.read_text(encoding="utf-8"))
            self.assertTrue(any("duplicates title" in error for error in duplicate_failure["errors"]))
            self.assertTrue(any("at least 10" in error for error in duplicate_failure["errors"]))
            bibliography_rows[9]["title"] = original_title
            bibliography_rows[9]["scholar_query"] = original_query
            with bibliography_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=bibliography_fields)
                writer.writeheader()
                writer.writerows(bibliography_rows)

            (root / "code" / "run.py").write_text("print('changed')\n", encoding="utf-8")
            self.run_script(
                "verify_paper_delivery.py", "--project-dir", str(root), "--out", str(report), expect=1
            )
            hash_failure = json.loads(report.read_text(encoding="utf-8"))
            self.assertTrue(any("SHA-256 mismatch" in error for error in hash_failure["errors"]))
            self.assertTrue(any("stale or modified copy" in error for error in hash_failure["errors"]))

    def test_latex_scaffold_and_static_validation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "project"
            result = self.run_script("scaffold_latex_paper.py", "--project-dir", str(root))
            self.assertIn("paper/.latexmkrc", result.stdout)
            self.assertTrue((root / "paper" / ".vscode" / "settings.json").is_file())
            self.assertTrue((root / "paper" / "sections" / "model.tex").is_file())
            self.assertTrue((root / "paper" / "figures").is_dir())
            self.assertTrue((root / "paper" / "build").is_dir())

            second = self.run_script(
                "scaffold_latex_paper.py", "--project-dir", str(root), expect=1
            )
            self.assertIn("not empty", second.stdout)
            self.run_script(
                "scaffold_latex_paper.py", "--project-dir", str(root), "--force"
            )

            report = root / "static.json"
            self.run_script(
                "verify_latex_compatibility.py",
                "--paper-dir", str(root / "paper"),
                "--out", str(report),
                "--static-only",
                expect=2,
            )
            self.assertEqual(json.loads(report.read_text(encoding="utf-8"))["status"], "LIMITED")

            main_tex = root / "paper" / "main.tex"
            main_tex.write_text(
                main_tex.read_text(encoding="utf-8")
                + "\n\\setmainfont{Times New Roman}\n"
                + "\\input{C:\\\\Users\\\\contestant\\\\private}\n"
                + "\\lstinputlisting{../private.py}\n",
                encoding="utf-8",
            )
            self.run_script(
                "verify_latex_compatibility.py",
                "--paper-dir", str(root / "paper"),
                "--out", str(report),
                "--static-only",
                expect=1,
            )
            failure = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(failure["status"], "FAIL")
            self.assertTrue(any("filesystem path" in error for error in failure["errors"]))
            self.assertTrue(any("font name" in error for error in failure["errors"]))
            self.assertTrue(any("code listing" in error for error in failure["errors"]))

    @unittest.skipUnless(
        shutil.which("latexmk") and shutil.which("xelatex") and shutil.which("bibtex"),
        "latexmk, XeLaTeX, and BibTeX are unavailable",
    )
    def test_portable_latex_compiles_for_both_build_paths(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "project"
            self.run_script("scaffold_latex_paper.py", "--project-dir", str(root))
            report = root / "latex_compatibility.json"
            self.run_script(
                "verify_latex_compatibility.py",
                "--paper-dir", str(root / "paper"),
                "--out", str(report),
            )
            payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "PASS")
            self.assertTrue(payload["compile_backed"])
            self.assertEqual(len(payload["builds"]), 2)
            self.assertGreater((root / "paper" / "main.pdf").stat().st_size, 0)
            self.assertGreater((root / "paper" / "build" / "main.pdf").stat().st_size, 0)

    def test_similarity_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            draft = root / "draft.md"; draft.write_text("one two three four five six seven eight nine ten eleven twelve", encoding="utf-8")
            corpus = root / "corpus"; corpus.mkdir()
            (corpus / "old.md").write_text("one two three four five six seven eight nine ten eleven twelve", encoding="utf-8")
            out = root / "similarity.json"
            self.run_script("similarity_preflight.py", "--draft", str(draft), "--corpus-dir", str(corpus), "--out", str(out), "--min-overlap", "1")
            self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["status"], "REVIEW")

    def test_portable_latex_archive(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            project = root / "project"
            self.run_script("scaffold_latex_paper.py", "--project-dir", str(project))
            paper = project / "paper"
            archive = root / "portable.zip"
            with zipfile.ZipFile(archive, "w") as bundle:
                for path in paper.rglob("*"):
                    if path.is_file() and "build" not in path.relative_to(paper).parts:
                        bundle.write(path, path.relative_to(paper).as_posix())
            report = root / "portable.json"
            self.run_script("verify_portable_latex.py", "--archive", str(archive), "--out", str(report))
            self.assertEqual(json.loads(report.read_text(encoding="utf-8"))["status"], "PASS")
            if shutil.which("latexmk") and shutil.which("xelatex") and shutil.which("bibtex"):
                self.run_script(
                    "verify_portable_latex.py",
                    "--archive", str(archive),
                    "--out", str(report),
                    "--compile",
                )
                self.assertTrue(
                    json.loads(report.read_text(encoding="utf-8"))["details"]["compatibility"]["compile_backed"]
                )

            main_tex = paper / "main.tex"
            main_tex.write_text(
                main_tex.read_text(encoding="utf-8").replace(
                    "\\begin{document}", "\\input{../escape}\\n\\begin{document}"
                ),
                encoding="utf-8",
            )
            with zipfile.ZipFile(archive, "w") as bundle:
                for path in paper.rglob("*"):
                    if path.is_file() and "build" not in path.relative_to(paper).parts:
                        bundle.write(path, path.relative_to(paper).as_posix())
            self.run_script("verify_portable_latex.py", "--archive", str(archive), "--out", str(report), expect=1)
            self.assertIn(
                "missing or nonportable TeX input",
                " ".join(json.loads(report.read_text(encoding="utf-8"))["errors"]),
            )

    def test_cumcm_2026_submission_profile(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paper = root / "paper.docx"; paper.write_bytes(b"docx-placeholder")
            support = root / "support.zip"
            with zipfile.ZipFile(support, "w") as archive:
                archive.writestr("AI\u5de5\u5177\u4f7f\u7528\u8be6\u60c5.pdf", b"pdf-placeholder")
            out = root / "manifest.json"
            self.run_script("verify_submission.py", "--paper", str(paper), "--support", str(support), "--profile", "cumcm-2026", "--main-text-pages", "30", "--ai-mode", "used", "--out", str(out))
            self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["status"], "PASS")

    @unittest.skipUnless(shutil.which("xelatex") or shutil.which("pdflatex"), "LaTeX is unavailable")
    def test_ai_report_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            log = root / "ai.jsonl"
            self.run_script("log_ai_use.py", "--log", str(log), "--tool", "TestAI", "--version", "1", "--purpose", "draft", "--stage", "writing", "--prompt-summary", "outline", "--adopted", "partial", "--human-verification", "reviewed")
            pdf = root / "AI\u5de5\u5177\u4f7f\u7528\u8be6\u60c5.pdf"
            self.run_script("render_ai_use_report.py", "--log", str(log), "--out", str(root / "report.md"), "--pdf-out", str(pdf))
            self.assertGreater(pdf.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
