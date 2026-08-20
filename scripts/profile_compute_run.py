#!/usr/bin/env python3
"""Measure one explicit contest command without invoking a shell."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import importlib.util
import json
import math
import os
import signal
import statistics
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_file(root: Path, relative: str) -> Path:
    root = root.resolve()
    target = (root / relative).resolve()
    try:
        common = os.path.commonpath((os.path.normcase(str(root)), os.path.normcase(str(target))))
    except ValueError as exc:
        raise ValueError(f"path is outside project root: {relative}") from exc
    if common != os.path.normcase(str(root)):
        raise ValueError(f"path is outside project root: {relative}")
    return target


def portable_command(command: list[str], root: Path) -> list[str]:
    """Remove machine-specific absolute paths while retaining an audit locator."""
    root = root.resolve()
    portable: list[str] = []
    for token in command:
        candidate = Path(token)
        if not candidate.is_absolute():
            portable.append(token)
            continue
        try:
            relative = candidate.resolve().relative_to(root)
        except (OSError, ValueError):
            portable.append(f"<external:{candidate.name or 'path'}>")
        else:
            portable.append(relative.as_posix())
    return portable


class MemorySampler:
    def __init__(self) -> None:
        self.psutil = None
        if importlib.util.find_spec("psutil") is not None:
            import psutil

            self.psutil = psutil
            self.method = "psutil_process_tree_rss"
        elif os.name == "nt":
            self.method = "windows_parent_working_set"
        elif Path("/proc").is_dir():
            self.method = "linux_proc_process_tree_rss"
        else:
            self.method = "unavailable"

    def sample(self, pid: int) -> int | None:
        if self.psutil is not None:
            try:
                process = self.psutil.Process(pid)
                processes = [process] + process.children(recursive=True)
                return sum(item.memory_info().rss for item in processes if item.is_running())
            except self.psutil.Error:
                return None
        if os.name == "nt":
            return self._windows(pid)
        if self.method.startswith("linux_proc"):
            return self._linux_tree(pid, set())
        return None

    @staticmethod
    def _windows(pid: int) -> int | None:
        class ProcessMemoryCounters(ctypes.Structure):
            _fields_ = [
                ("cb", ctypes.c_ulong),
                ("PageFaultCount", ctypes.c_ulong),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        process_query_information = 0x0400
        process_vm_read = 0x0010
        handle = ctypes.windll.kernel32.OpenProcess(
            process_query_information | process_vm_read, False, pid
        )
        if not handle:
            return None
        counters = ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        try:
            ok = ctypes.windll.psapi.GetProcessMemoryInfo(
                handle, ctypes.byref(counters), counters.cb
            )
            return int(counters.WorkingSetSize) if ok else None
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)

    @classmethod
    def _linux_tree(cls, pid: int, seen: set[int]) -> int | None:
        if pid in seen:
            return 0
        seen.add(pid)
        status = Path(f"/proc/{pid}/status")
        try:
            text = status.read_text(encoding="ascii", errors="replace")
        except OSError:
            return None
        rss = 0
        for line in text.splitlines():
            if line.startswith("VmRSS:"):
                parts = line.split()
                if len(parts) >= 2:
                    rss = int(parts[1]) * 1024
                break
        children_path = Path(f"/proc/{pid}/task/{pid}/children")
        try:
            child_ids = [int(value) for value in children_path.read_text().split()]
        except (OSError, ValueError):
            child_ids = []
        for child in child_ids:
            child_rss = cls._linux_tree(child, seen)
            if child_rss is not None:
                rss += child_rss
        return rss


def terminate(process: subprocess.Popen[bytes], sampler: MemorySampler) -> None:
    if sampler.psutil is not None:
        try:
            parent = sampler.psutil.Process(process.pid)
            descendants = parent.children(recursive=True)
            for child in descendants:
                child.kill()
            parent.kill()
            return
        except sampler.psutil.Error:
            pass
    if os.name != "nt":
        try:
            os.killpg(process.pid, signal.SIGKILL)
            return
        except OSError:
            pass
    process.kill()


def measure_once(
    command: list[str], root: Path, timeout: float, sampler: MemorySampler
) -> dict[str, Any]:
    with tempfile.TemporaryFile() as stdout_handle, tempfile.TemporaryFile() as stderr_handle:
        kwargs: dict[str, Any] = {
            "cwd": root,
            "stdout": stdout_handle,
            "stderr": stderr_handle,
            "shell": False,
        }
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            kwargs["start_new_session"] = True
        started = time.perf_counter()
        try:
            process = subprocess.Popen(command, **kwargs)
        except OSError as exc:
            elapsed = time.perf_counter() - started
            return {
                "wall_seconds": elapsed,
                "peak_memory_mb": None,
                "memory_method": sampler.method,
                "exit_code": None,
                "timed_out": False,
                "launch_error": str(exc),
                "stdout_sha256": sha256_bytes(b""),
                "stderr_sha256": sha256_bytes(str(exc).encode("utf-8", errors="replace")),
                "stdout_bytes": 0,
                "stderr_bytes": len(str(exc).encode("utf-8", errors="replace")),
            }
        peak_bytes: int | None = sampler.sample(process.pid)
        timed_out = False
        while process.poll() is None:
            current = sampler.sample(process.pid)
            if current is not None:
                peak_bytes = current if peak_bytes is None else max(peak_bytes, current)
            if time.perf_counter() - started >= timeout:
                timed_out = True
                terminate(process, sampler)
                break
            time.sleep(0.01)
        try:
            returncode = process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            terminate(process, sampler)
            returncode = process.wait(timeout=2)
        elapsed = time.perf_counter() - started
        stdout_handle.seek(0)
        stderr_handle.seek(0)
        stdout = stdout_handle.read()
        stderr = stderr_handle.read()
    return {
        "wall_seconds": elapsed,
        "peak_memory_mb": None if peak_bytes is None else peak_bytes / (1024 * 1024),
        "memory_method": sampler.method,
        "exit_code": returncode,
        "timed_out": timed_out,
        "stdout_sha256": sha256_bytes(stdout),
        "stderr_sha256": sha256_bytes(stderr),
        "stdout_bytes": len(stdout),
        "stderr_bytes": len(stderr),
    }


def record_hash(record: dict[str, Any]) -> str:
    canonical = json.dumps(
        record, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def existing_run_ids(path: Path) -> set[str]:
    ids: set[str] = set()
    if not path.is_file():
        return ids
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"compute_runs.jsonl line {line_number} is invalid: {exc}") from exc
        if not isinstance(item, dict) or not isinstance(item.get("run_id"), str):
            raise ValueError(f"compute_runs.jsonl line {line_number} lacks run_id")
        ids.add(item["run_id"])
    return ids


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--role", choices=["primary", "fallback"], required=True)
    parser.add_argument(
        "--scale-label", choices=["small", "medium", "representative", "full"], required=True
    )
    parser.add_argument("--input-size", type=float, required=True)
    parser.add_argument("--timeout-seconds", type=float, required=True)
    parser.add_argument("--remaining-time-seconds", type=float, required=True)
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--result-artifact", required=True)
    parser.add_argument("--solver-status", required=True)
    parser.add_argument("--solver-gap", type=float)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    root = args.project_dir.resolve()
    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        parser.error("an explicit command is required after --")
    if args.timeout_seconds <= 0 or args.remaining_time_seconds <= 0:
        parser.error("timeout and remaining time must be positive")
    if args.repeat < 1 or args.input_size < 0:
        parser.error("repeat must be positive and input-size must be nonnegative")
    if args.solver_gap is not None and (
        not math.isfinite(args.solver_gap) or args.solver_gap < 0
    ):
        parser.error("solver-gap must be finite and nonnegative")
    result_path = safe_file(root, args.result_artifact)
    runs_path = root / "reports" / "compute_runs.jsonl"
    runs_path.parent.mkdir(parents=True, exist_ok=True)
    if args.run_id in existing_run_ids(runs_path):
        print(f"FAIL: duplicate run-id {args.run_id}")
        return 1

    sampler = MemorySampler()
    measurements = [
        measure_once(command, root, args.timeout_seconds, sampler)
        for _ in range(args.repeat)
    ]
    timed_out = any(item["timed_out"] for item in measurements)
    failed = any(item["exit_code"] != 0 for item in measurements)
    artifact_exists = result_path.is_file()
    status = "TIMEOUT" if timed_out else ("FAIL" if failed or not artifact_exists else "PASS")
    wall_values = [float(item["wall_seconds"]) for item in measurements]
    memory_values = [
        float(item["peak_memory_mb"])
        for item in measurements
        if item["peak_memory_mb"] is not None
    ]
    memory_status = "PASS" if len(memory_values) == len(measurements) else "LIMITED"
    record: dict[str, Any] = {
        "schema_version": 1,
        "run_id": args.run_id,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "model_id": args.model_id,
        "role": args.role,
        "scale_label": args.scale_label,
        "input_size": args.input_size,
        "command": portable_command(command, root),
        "command_sha256": sha256_bytes(
            json.dumps(
                command, ensure_ascii=False, separators=(",", ":"), allow_nan=False
            ).encode("utf-8")
        ),
        "cwd": ".",
        "timeout_seconds": args.timeout_seconds,
        "remaining_time_seconds": args.remaining_time_seconds,
        "repeat": args.repeat,
        "solver_status": args.solver_status,
        "solver_gap": args.solver_gap,
        "result_artifact": args.result_artifact.replace("\\", "/"),
        "result_artifact_sha256": sha256_file(result_path) if artifact_exists else None,
        "status": status,
        "measurements": measurements,
        "aggregate": {
            "wall_seconds_max": max(wall_values),
            "wall_seconds_median": statistics.median(wall_values),
            "peak_memory_mb_max": max(memory_values) if memory_values else None,
        },
        "memory": {
            "status": memory_status,
            "method": sampler.method,
            "scope": "process tree when supported; otherwise the directly launched process",
        },
    }
    record["record_sha256"] = record_hash(record)
    with runs_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n")
    print(status)
    if memory_status == "LIMITED":
        print("WARNING peak-memory instrumentation was unavailable for at least one sample")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
