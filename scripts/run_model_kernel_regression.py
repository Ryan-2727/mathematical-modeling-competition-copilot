#!/usr/bin/env python3
"""Run hidden-truth and metamorphic checks on bundled synthetic kernel fixtures."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from model_kernels import execute_kernel


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURES = ROOT / "assets" / "model-library" / "fixtures"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def distance(left: list[float], right: list[float]) -> float:
    return math.sqrt(sum((float(a) - float(b)) ** 2 for a, b in zip(left, right)))


def maximum_difference(left: Any, right: Any) -> float:
    if isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            return math.inf
        return max((maximum_difference(a, b) for a, b in zip(left, right)), default=0.0)
    return abs(float(left) - float(right))


class Recorder:
    def __init__(self, backend: str) -> None:
        self.backend = backend
        self.checks: list[dict[str, Any]] = []
        self.backends: set[str] = set()

    def execute(self, kernel: str, payload: dict[str, Any]) -> dict[str, Any]:
        result = execute_kernel(kernel, payload, self.backend)
        used = result.get("backend_used")
        if isinstance(used, str):
            self.backends.add(used)
        return result

    def check(
        self,
        kernel: str,
        fixture_hash: str,
        check_id: str,
        passed: bool,
        metric: str,
        observed: Any,
        expected: Any,
        tolerance: float | None = None,
        backend_used: str | None = None,
    ) -> None:
        self.checks.append(
            {
                "kernel": kernel,
                "fixture_sha256": fixture_hash,
                "check_id": check_id,
                "status": "PASS" if passed else "FAIL",
                "metric": metric,
                "observed": observed,
                "expected": expected,
                "tolerance": tolerance,
                "backend_used": backend_used,
            }
        )


def bearing_checks(fixture: dict[str, Any], digest: str, recorder: Recorder) -> None:
    kernel = fixture["kernel"]
    tolerance = float(fixture["tolerance"])
    truth = fixture["hidden_truth"]["position"]
    base = recorder.execute(kernel, fixture["base_input"])
    position = base.get("result", {}).get("position")
    error = math.inf if not isinstance(position, list) else distance(position, truth)
    recorder.check(kernel, digest, "hidden-truth-position", base["status"] == "PASS" and error <= tolerance,
                   "euclidean_error", error, 0.0, tolerance, base.get("backend_used"))
    recorder.check(kernel, digest, "observability-rank", base.get("diagnostics", {}).get("rank") == 2,
                   "rank", base.get("diagnostics", {}).get("rank"), 2, None, base.get("backend_used"))

    translation = next(item for item in fixture["transformations"] if item["id"] == "translation")
    shifted = copy.deepcopy(fixture["base_input"])
    dx, dy = translation["offset"]
    for item in shifted["observations"]:
        item["x"] += dx
        item["y"] += dy
    shifted_result = recorder.execute(kernel, shifted)
    shifted_truth = [truth[0] + dx, truth[1] + dy]
    shifted_error = distance(shifted_result["result"]["position"], shifted_truth)
    recorder.check(kernel, digest, "translation-invariance", shifted_error <= tolerance,
                   "translated_position_error", shifted_error, 0.0, tolerance, shifted_result.get("backend_used"))

    rotation = next(item for item in fixture["transformations"] if item["id"] == "rotation")
    angle = math.radians(float(rotation["angle_deg"]))
    cosine, sine = math.cos(angle), math.sin(angle)
    rotated = copy.deepcopy(fixture["base_input"])
    for item in rotated["observations"]:
        x, y = item["x"], item["y"]
        item["x"] = cosine * x - sine * y
        item["y"] = sine * x + cosine * y
        item["bearing_deg"] += rotation["angle_deg"]
    rotated_truth = [cosine * truth[0] - sine * truth[1], sine * truth[0] + cosine * truth[1]]
    rotated_result = recorder.execute(kernel, rotated)
    rotated_error = distance(rotated_result["result"]["position"], rotated_truth)
    recorder.check(kernel, digest, "rotation-invariance", rotated_error <= tolerance,
                   "rotated_position_error", rotated_error, 0.0, tolerance, rotated_result.get("backend_used"))

    noise = next(item for item in fixture["transformations"] if item["id"] == "noise")
    noisy = copy.deepcopy(fixture["base_input"])
    for item, offset in zip(noisy["observations"], noise["bearing_offsets_deg"]):
        item["bearing_deg"] += offset
    noisy_result = recorder.execute(kernel, noisy)
    noisy_error = distance(noisy_result["result"]["position"], truth)
    recorder.check(kernel, digest, "noise-degradation", noisy_result["status"] == "PASS" and noisy_error > error,
                   "position_error", noisy_error, f"> {error}", None, noisy_result.get("backend_used"))

    degenerate = recorder.execute(kernel, fixture["degenerate_input"])
    recorder.check(kernel, digest, "degenerate-observability", degenerate["status"] == "LIMITED",
                   "typed_status", degenerate["status"], "LIMITED", None, degenerate.get("backend_used"))


def coverage_checks(fixture: dict[str, Any], digest: str, recorder: Recorder) -> None:
    kernel = fixture["kernel"]
    tolerance = float(fixture["tolerance"])
    truth = fixture["hidden_truth"]
    base = recorder.execute(kernel, fixture["base_input"])
    diagnostics = base["diagnostics"]
    result = base["result"]
    recorder.check(kernel, digest, "hidden-truth-coverage", base["status"] == "PASS" and abs(diagnostics["coverage_ratio"] - truth["coverage_ratio"]) <= tolerance,
                   "coverage_ratio", diagnostics["coverage_ratio"], truth["coverage_ratio"], tolerance, base.get("backend_used"))
    recorder.check(kernel, digest, "hidden-truth-route", result["line_count"] == truth["line_count"] and abs(result["path_length"] - truth["path_length"]) <= tolerance,
                   "line_count_and_path", [result["line_count"], result["path_length"]], [truth["line_count"], truth["path_length"]], tolerance, base.get("backend_used"))

    translation = next(item for item in fixture["transformations"] if item["id"] == "translation")
    shifted = copy.deepcopy(fixture["base_input"])
    shifted["origin"] = translation["offset"]
    shifted_result = recorder.execute(kernel, shifted)
    invariant_error = max(
        abs(shifted_result["diagnostics"]["coverage_ratio"] - diagnostics["coverage_ratio"]),
        abs(shifted_result["result"]["path_length"] - result["path_length"]),
    )
    recorder.check(kernel, digest, "translation-invariance", invariant_error <= tolerance,
                   "coverage_path_difference", invariant_error, 0.0, tolerance, shifted_result.get("backend_used"))

    scaling = next(item for item in fixture["transformations"] if item["id"] == "unit_scaling")
    factor = float(scaling["factor"])
    scaled = copy.deepcopy(fixture["base_input"])
    for field in ("width", "height", "swath_width", "sweep_spacing"):
        scaled[field] *= factor
    scaled["origin"] = [value * factor for value in scaled["origin"]]
    scaled_result = recorder.execute(kernel, scaled)
    scale_error = max(
        abs(scaled_result["diagnostics"]["coverage_ratio"] - diagnostics["coverage_ratio"]),
        abs(scaled_result["result"]["path_length"] - factor * result["path_length"]),
    )
    recorder.check(kernel, digest, "unit-scaling", scale_error <= tolerance,
                   "scale_contract_error", scale_error, 0.0, tolerance, scaled_result.get("backend_used"))

    degenerate = recorder.execute(kernel, fixture["degenerate_input"])
    recorder.check(kernel, digest, "coverage-gap-detected", degenerate["status"] == "LIMITED" and degenerate["diagnostics"]["uncovered_ratio"] > 0,
                   "typed_status_and_uncovered_ratio", [degenerate["status"], degenerate["diagnostics"]["uncovered_ratio"]], ["LIMITED", "> 0"], None, degenerate.get("backend_used"))


def composition_checks(fixture: dict[str, Any], digest: str, recorder: Recorder) -> None:
    kernel = fixture["kernel"]
    tolerance = float(fixture["tolerance"])
    truth = fixture["hidden_truth"]
    base = recorder.execute(kernel, fixture["base_input"])
    result = base["result"]
    closed_error = maximum_difference(result["closed"][0], truth["first_closed_row"])
    replaced_error = maximum_difference(result["zero_replaced"][1], truth["second_replaced_row"])
    recorder.check(kernel, digest, "hidden-truth-closure", base["status"] == "PASS" and closed_error <= tolerance,
                   "maximum_closed_error", closed_error, 0.0, tolerance, base.get("backend_used"))
    recorder.check(kernel, digest, "hidden-truth-zero-replacement", replaced_error <= tolerance,
                   "maximum_replacement_error", replaced_error, 0.0, tolerance, base.get("backend_used"))
    recorder.check(kernel, digest, "clr-zero-sum", base["diagnostics"]["maximum_clr_sum_abs"] <= tolerance,
                   "maximum_clr_sum_abs", base["diagnostics"]["maximum_clr_sum_abs"], 0.0, tolerance, base.get("backend_used"))

    scaling = next(item for item in fixture["transformations"] if item["id"] == "row_scaling")
    scaled = copy.deepcopy(fixture["base_input"])
    scaled["compositions"] = [
        [value * factor for value in row]
        for row, factor in zip(scaled["compositions"], scaling["factors"])
    ]
    scaled_result = recorder.execute(kernel, scaled)
    invariant_error = max(
        maximum_difference(scaled_result["result"]["closed"], result["closed"]),
        maximum_difference(scaled_result["result"]["clr"], result["clr"]),
    )
    recorder.check(kernel, digest, "row-scale-invariance", invariant_error <= tolerance,
                   "maximum_transform_difference", invariant_error, 0.0, tolerance, scaled_result.get("backend_used"))

    permutation = next(item for item in fixture["transformations"] if item["id"] == "component_permutation")
    order = permutation["order"]
    permuted = copy.deepcopy(fixture["base_input"])
    permuted["compositions"] = [[row[index] for index in order] for row in permuted["compositions"]]
    permuted_result = recorder.execute(kernel, permuted)
    expected_clr = [[row[index] for index in order] for row in result["clr"]]
    permutation_error = maximum_difference(permuted_result["result"]["clr"], expected_clr)
    recorder.check(kernel, digest, "component-permutation", permutation_error <= tolerance,
                   "maximum_permutation_error", permutation_error, 0.0, tolerance, permuted_result.get("backend_used"))

    degenerate = recorder.execute(kernel, fixture["degenerate_input"])
    recorder.check(kernel, digest, "all-zero-row-rejected", degenerate["status"] == "FAIL",
                   "typed_status", degenerate["status"], "FAIL", None, degenerate.get("backend_used"))


def interval_checks(fixture: dict[str, Any], digest: str, recorder: Recorder) -> None:
    kernel = fixture["kernel"]
    tolerance = float(fixture["tolerance"])
    truth = fixture["hidden_truth"]
    base = recorder.execute(kernel, fixture["base_input"])
    probability_error = maximum_difference(base["result"]["probabilities"], truth["probabilities"])
    recorder.check(kernel, digest, "hidden-truth-distribution", base["status"] == "PASS" and probability_error <= tolerance,
                   "maximum_probability_error", probability_error, 0.0, tolerance, base.get("backend_used"))
    recorder.check(kernel, digest, "hidden-truth-median", base["result"]["median"] == truth["median"],
                   "median", base["result"]["median"], truth["median"], tolerance, base.get("backend_used"))

    reversed_input = copy.deepcopy(fixture["base_input"])
    reversed_input["intervals"].reverse()
    reversed_result = recorder.execute(kernel, reversed_input)
    order_error = maximum_difference(reversed_result["result"]["probabilities"], base["result"]["probabilities"])
    recorder.check(kernel, digest, "input-order-invariance", order_error <= tolerance,
                   "maximum_probability_difference", order_error, 0.0, tolerance, reversed_result.get("backend_used"))

    scaling = next(item for item in fixture["transformations"] if item["id"] == "unit_scaling")
    factor = float(scaling["factor"])
    scaled = copy.deepcopy(fixture["base_input"])
    scaled["support"] = [value * factor for value in scaled["support"]]
    for item in scaled["intervals"]:
        item["lower"] *= factor
        item["upper"] *= factor
    scaled_result = recorder.execute(kernel, scaled)
    scale_error = max(
        maximum_difference(scaled_result["result"]["probabilities"], base["result"]["probabilities"]),
        abs(scaled_result["result"]["median"] - factor * base["result"]["median"]),
    )
    recorder.check(kernel, digest, "unit-scaling", scale_error <= tolerance,
                   "scale_contract_error", scale_error, 0.0, tolerance, scaled_result.get("backend_used"))

    weak = copy.deepcopy(fixture["base_input"])
    broad = next(item for item in fixture["transformations"] if item["id"] == "weaker_information")["interval"]
    weak["intervals"] = [copy.deepcopy(broad) for _ in weak["intervals"]]
    weak_result = recorder.execute(kernel, weak)
    recorder.check(kernel, digest, "weaker-information-degradation", weak_result["status"] == "LIMITED" and weak_result["diagnostics"]["entropy"] >= base["diagnostics"]["entropy"],
                   "status_and_entropy", [weak_result["status"], weak_result["diagnostics"]["entropy"]], ["LIMITED", f">= {base['diagnostics']['entropy']}"] , None, weak_result.get("backend_used"))

    degenerate = recorder.execute(kernel, fixture["degenerate_input"])
    recorder.check(kernel, digest, "weak-identification-reported", degenerate["status"] == "LIMITED" and degenerate["diagnostics"]["weakly_identified"],
                   "typed_status", degenerate["status"], "LIMITED", None, degenerate.get("backend_used"))


def robust_checks(fixture: dict[str, Any], digest: str, recorder: Recorder) -> None:
    kernel = fixture["kernel"]
    tolerance = float(fixture["tolerance"])
    truth = fixture["hidden_truth"]
    base = recorder.execute(kernel, fixture["base_input"])
    robust = base["result"]["robust"]
    baseline = base["result"]["baseline"]
    recorder.check(kernel, digest, "hidden-truth-robust-selection", base["status"] == "PASS" and robust["selected_ids"] == truth["robust_selected_ids"],
                   "selected_ids", robust["selected_ids"], truth["robust_selected_ids"], None, base.get("backend_used"))
    recorder.check(kernel, digest, "hidden-truth-baseline-selection", baseline["selected_ids"] == truth["baseline_selected_ids"],
                   "selected_ids", baseline["selected_ids"], truth["baseline_selected_ids"], None, base.get("backend_used"))
    recorder.check(kernel, digest, "independent-feasibility", base["diagnostics"]["maximum_feasibility_residual"] <= tolerance,
                   "maximum_feasibility_residual", base["diagnostics"]["maximum_feasibility_residual"], 0.0, tolerance, base.get("backend_used"))
    recorder.check(kernel, digest, "robust-worst-case-advantage", robust["worst_value"] > baseline["worst_value"],
                   "worst_values", [robust["worst_value"], baseline["worst_value"]], "robust > baseline", None, base.get("backend_used"))

    reversed_input = copy.deepcopy(fixture["base_input"])
    reversed_input["items"].reverse()
    reversed_result = recorder.execute(kernel, reversed_input)
    recorder.check(kernel, digest, "input-order-invariance", reversed_result["result"]["robust"]["selected_ids"] == robust["selected_ids"],
                   "selected_ids", reversed_result["result"]["robust"]["selected_ids"], robust["selected_ids"], None, reversed_result.get("backend_used"))

    scaling = next(item for item in fixture["transformations"] if item["id"] == "cost_unit_scaling")
    factor = float(scaling["factor"])
    scaled = copy.deepcopy(fixture["base_input"])
    scaled["budget"] *= factor
    for item in scaled["items"]:
        item["cost"] *= factor
    scaled_result = recorder.execute(kernel, scaled)
    recorder.check(kernel, digest, "cost-unit-invariance", scaled_result["result"]["robust"]["selected_ids"] == robust["selected_ids"],
                   "selected_ids", scaled_result["result"]["robust"]["selected_ids"], robust["selected_ids"], None, scaled_result.get("backend_used"))

    degenerate = recorder.execute(kernel, fixture["degenerate_input"])
    recorder.check(kernel, digest, "infeasibility-reported", degenerate["status"] == "LIMITED" and not degenerate["diagnostics"]["feasible"],
                   "typed_status", degenerate["status"], "LIMITED", None, degenerate.get("backend_used"))


CHECKERS = {
    "bearing-only-localization": bearing_checks,
    "coverage-path-planning": coverage_checks,
    "compositional-data": composition_checks,
    "interval-censored-timing": interval_checks,
    "robust-binary-allocation": robust_checks,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", choices=["auto", "stdlib", "scientific"], default="auto")
    parser.add_argument("--fixture-dir", type=Path, default=DEFAULT_FIXTURES)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    recorder = Recorder(args.backend)
    fixture_hashes: dict[str, str] = {}
    errors: list[str] = []
    for kernel, checker in CHECKERS.items():
        path = args.fixture_dir / f"{kernel}.json"
        try:
            fixture = json.loads(path.read_text(encoding="utf-8-sig"))
            if not isinstance(fixture, dict) or fixture.get("kernel") != kernel:
                raise ValueError("fixture kernel does not match its filename")
            digest = sha256(path)
            fixture_hashes[kernel] = digest
            checker(fixture, digest, recorder)
        except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            errors.append(f"{kernel}: {exc}")

    failed = [record for record in recorder.checks if record["status"] == "FAIL"]
    status = "FAIL" if errors or failed else "PASS"
    payload = {
        "schema_version": 1,
        "status": status,
        "backend_requested": args.backend,
        "backends_used": sorted(recorder.backends),
        "fixture_hashes": fixture_hashes,
        "kernel_count": len(fixture_hashes),
        "check_count": len(recorder.checks),
        "checks": recorder.checks,
        "errors": errors + [record["check_id"] for record in failed],
        "warnings": [],
        "scope_limitation": "Synthetic fixtures validate bundled kernels, not future contest-model suitability or truth.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(status)
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
