from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


class ComputeBudgetTests(unittest.TestCase):
    def run_script(self, name: str, *args: str, expect: int = 0) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / name), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(result.returncode, expect, result.stdout + result.stderr)

    def profile(
        self,
        root: Path,
        run_id: str,
        role: str,
        scale: str,
        size: int,
        artifact: str,
        timeout: float = 5.0,
        expect: int = 0,
        worker: str = "worker.py",
    ) -> None:
        self.run_script(
            "profile_compute_run.py",
            "--project-dir",
            str(root),
            "--run-id",
            run_id,
            "--model-id",
            "model-a",
            "--role",
            role,
            "--scale-label",
            scale,
            "--input-size",
            str(size),
            "--timeout-seconds",
            str(timeout),
            "--remaining-time-seconds",
            "60",
            "--result-artifact",
            artifact,
            "--solver-status",
            "not_applicable",
            "--",
            sys.executable,
            worker,
            str(size),
            artifact,
            expect=expect,
        )

    @staticmethod
    def write_budget(root: Path) -> None:
        fields = [
            "model_id",
            "selected",
            "primary_run_ids",
            "fallback_run_id",
            "required_scale_count",
            "single_scale_reason",
            "remaining_time_seconds",
            "solver_gap_required",
            "status",
        ]
        with (root / "reports" / "compute_budget.csv").open(
            "w", encoding="utf-8", newline=""
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerow(
                {
                    "model_id": "model-a",
                    "selected": "yes",
                    "primary_run_ids": "primary-small;primary-representative",
                    "fallback_run_id": "fallback-representative",
                    "required_scale_count": "2",
                    "single_scale_reason": "",
                    "remaining_time_seconds": "60",
                    "solver_gap_required": "no",
                    "status": "verified",
                }
            )

    def test_real_runs_and_fallback_form_a_hash_bound_budget(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "reports").mkdir()
            (root / "results").mkdir()
            (root / "worker.py").write_text(
                "from pathlib import Path\n"
                "import sys\n"
                "size = int(sys.argv[1])\n"
                "target = Path(sys.argv[2])\n"
                "target.parent.mkdir(parents=True, exist_ok=True)\n"
                "target.write_text(str(sum(range(size + 1))), encoding='utf-8')\n",
                encoding="utf-8",
            )
            self.profile(root, "primary-small", "primary", "small", 10, "results/small.txt")
            self.profile(
                root,
                "primary-representative",
                "primary",
                "representative",
                100,
                "results/representative.txt",
            )
            self.profile(
                root,
                "fallback-representative",
                "fallback",
                "representative",
                100,
                "results/fallback.txt",
            )
            self.write_budget(root)
            out = root / "reports" / "compute_budget_verification.json"
            self.run_script(
                "verify_compute_budget.py",
                "--project-dir",
                str(root),
                "--out",
                str(out),
            )
            report = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "PASS", report)
            self.assertEqual(report["selected_model_count"], 1)
            self.assertRegex(report["compute_runs_sha256"], r"^[0-9a-f]{64}$")
            runs = [
                json.loads(line)
                for line in (root / "reports" / "compute_runs.jsonl").read_text(
                    encoding="utf-8"
                ).splitlines()
            ]
            self.assertEqual(len(runs), 3)
            self.assertTrue(all(run["aggregate"]["wall_seconds_max"] > 0 for run in runs))
            self.assertTrue(all(run["memory"]["status"] in {"PASS", "LIMITED"} for run in runs))
            self.assertTrue(
                all(
                    not Path(token).is_absolute()
                    for run in runs
                    for token in run["command"]
                )
            )
            self.assertTrue(
                all(
                    len(run["command_sha256"]) == 64
                    and set(run["command_sha256"]) <= set("0123456789abcdef")
                    for run in runs
                )
            )

            (root / "results" / "representative.txt").write_text(
                "stale", encoding="utf-8"
            )
            self.run_script(
                "verify_compute_budget.py",
                "--project-dir",
                str(root),
                "--out",
                str(out),
                expect=1,
            )

    def test_profiler_timeout_is_a_typed_failure(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "reports").mkdir()
            (root / "results").mkdir()
            (root / "slow.py").write_text(
                "import time\ntime.sleep(2)\n", encoding="utf-8"
            )
            self.profile(
                root,
                "timeout-run",
                "primary",
                "representative",
                1,
                "results/never.txt",
                timeout=0.1,
                expect=1,
                worker="slow.py",
            )
            record = json.loads(
                (root / "reports" / "compute_runs.jsonl").read_text(encoding="utf-8")
            )
            self.assertEqual(record["status"], "TIMEOUT")
            self.assertTrue(record["measurements"][0]["timed_out"])
            self.assertGreaterEqual(record["aggregate"]["wall_seconds_max"], 0.1)

    def test_profiler_launch_failure_is_recorded_without_a_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "reports").mkdir()
            (root / "results").mkdir()
            self.run_script(
                "profile_compute_run.py",
                "--project-dir",
                str(root),
                "--run-id",
                "launch-failure",
                "--model-id",
                "model-a",
                "--role",
                "primary",
                "--scale-label",
                "representative",
                "--input-size",
                "1",
                "--timeout-seconds",
                "1",
                "--remaining-time-seconds",
                "60",
                "--result-artifact",
                "results/never.txt",
                "--solver-status",
                "not_applicable",
                "--",
                "definitely-not-a-real-executable-20260820",
                expect=1,
            )
            record = json.loads(
                (root / "reports" / "compute_runs.jsonl").read_text(encoding="utf-8")
            )
            self.assertEqual(record["status"], "FAIL")
            self.assertIn("launch_error", record["measurements"][0])


if __name__ == "__main__":
    unittest.main()
