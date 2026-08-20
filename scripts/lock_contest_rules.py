#!/usr/bin/env python3
"""Create and validate hash-bound official contest rule snapshots."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from contest_profile import load_contest_profile


PROFILE_RULES = {
    "cumcm": {
        "paper_format",
        "paper_size_limit_mb",
        "support_archive",
        "main_text_page_limit",
        "ai_policy",
        "anonymity",
    },
    "mcm-icm": {
        "paper_format",
        "paper_size_limit_mb",
        "extra_files_allowed",
        "total_page_limit",
        "ai_policy",
        "anonymity",
    },
}

CUMCM_2026_PROFILE = load_contest_profile("cumcm-2026")
CUMCM_2026_SOURCE_ROLES = set(CUMCM_2026_PROFILE["source_urls"])
CUMCM_2026_SOURCE_KINDS = {
    role: set(variants)
    for role, variants in CUMCM_2026_PROFILE.get("source_variants", {}).items()
}
CUMCM_2026_RULES = {
    key: CUMCM_2026_PROFILE[key]
    for key in (
        "competition_start",
        "competition_end",
        "registration_deadline",
        "hash_deadline",
        "upload_open",
        "upload_deadline",
        "timezone",
        "submission_channel",
    )
}
CUMCM_2026_CHECKPOINTS = CUMCM_2026_PROFILE["freshness_checkpoints"]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_project_file(root: Path, relative: str) -> Path | None:
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return None
    return resolved


def profile_family(profile: str) -> str:
    lowered = profile.lower()
    if lowered.startswith("cumcm"):
        return "cumcm"
    if lowered.startswith("mcm") or lowered.startswith("icm"):
        return "mcm-icm"
    return "generic"


def parse_datetime(value: object, label: str, errors: list[str]) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{label} must be an ISO-8601 datetime")
        return None
    if parsed.tzinfo is None:
        errors.append(f"{label} must include a timezone offset")
        return None
    return parsed


def validate_lock(
    root: Path,
    payload: Any,
    *,
    as_of_date: date | None = None,
    mode: str = "precontest",
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(payload, dict):
        payload = {}
        errors.append("rules lock must be a JSON object")
    for field in ("contest", "year", "profile", "created_at_utc", "valid_through"):
        if not payload.get(field):
            errors.append(f"missing rules lock field: {field}")
    try:
        valid_through = date.fromisoformat(str(payload.get("valid_through") or ""))
    except ValueError:
        errors.append("valid_through must be YYYY-MM-DD")
    else:
        if date.today() > valid_through:
            errors.append(f"rules lock expired on {valid_through.isoformat()}")
    sources = payload.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("rules lock needs at least one official source snapshot")
        sources = []
    source_reports: list[dict[str, Any]] = []
    source_roles: set[str] = set()
    source_role_kinds: dict[str, set[str]] = {}
    for index, source in enumerate(sources, 1):
        local_errors: list[str] = []
        if not isinstance(source, dict):
            errors.append(f"sources[{index}] must be an object")
            continue
        url = str(source.get("url") or "").strip()
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.netloc:
            local_errors.append("official source URL must use HTTPS")
        relative = str(source.get("snapshot") or "").strip()
        role = str(source.get("role") or "").strip()
        kind = str(source.get("kind") or "").strip()
        if role:
            if not kind and role in source_roles:
                local_errors.append(f"duplicate source role: {role}")
            source_roles.add(role)
            if kind:
                if kind in source_role_kinds.setdefault(role, set()):
                    local_errors.append(f"duplicate source role/kind: {role}/{kind}")
                source_role_kinds[role].add(kind)
        path = safe_project_file(root, relative)
        if path is None or not path.is_file():
            local_errors.append("snapshot is missing or outside the project")
        else:
            expected = str(source.get("sha256") or "").lower()
            actual = sha256_file(path)
            if expected != actual:
                local_errors.append("snapshot SHA-256 mismatch")
        source_reports.append(
            {
                "url": url,
                "role": role,
                "kind": kind,
                "snapshot": relative,
                "status": "PASS" if not local_errors else "FAIL",
                "errors": local_errors,
            }
        )
        errors.extend(f"sources[{index}]: {item}" for item in local_errors)
    rules = payload.get("rules")
    if not isinstance(rules, dict):
        rules = {}
        errors.append("rules must be an object")
    family = profile_family(str(payload.get("profile") or ""))
    required = PROFILE_RULES.get(family, set())
    if family == "generic" and len(rules) < 5:
        errors.append("generic profile needs at least five explicit rule fields")
    for field in sorted(required):
        if field not in rules or rules[field] in {"", None}:
            errors.append(f"missing structured rule: {field}")
    latest_due_checkpoint = ""
    if str(payload.get("profile") or "").lower() == "cumcm-2026":
        missing_roles = sorted(CUMCM_2026_SOURCE_ROLES - source_roles)
        if missing_roles:
            errors.append("missing official source role(s): " + ", ".join(missing_roles))
        for role, required_kinds in sorted(CUMCM_2026_SOURCE_KINDS.items()):
            missing_kinds = sorted(required_kinds - source_role_kinds.get(role, set()))
            if missing_kinds:
                errors.append(
                    f"official source role {role} missing source kind(s): "
                    + ", ".join(missing_kinds)
                )
        expected_sources = CUMCM_2026_PROFILE.get("source_variants", {})
        for index, source in enumerate(sources, 1):
            if not isinstance(source, dict):
                continue
            role = str(source.get("role") or "").strip()
            kind = str(source.get("kind") or "").strip()
            expected_url = (expected_sources.get(role) or {}).get(kind)
            if expected_url is None:
                errors.append(
                    f"sources[{index}]: unknown CUMCM 2026 source role/kind {role}/{kind}"
                )
            elif str(source.get("url") or "").strip() != expected_url:
                errors.append(
                    f"sources[{index}]: CUMCM 2026 source URL does not match "
                    f"the bundled {role}/{kind} official source"
                )
        for index, source in enumerate(sources, 1):
            if not isinstance(source, dict):
                continue
            host = (urlparse(str(source.get("url") or "")).hostname or "").lower()
            if host != "mcm.edu.cn" and not host.endswith(".mcm.edu.cn"):
                errors.append(f"sources[{index}]: CUMCM 2026 source must use mcm.edu.cn")
        for field, expected in CUMCM_2026_RULES.items():
            if rules.get(field) != expected:
                errors.append(f"CUMCM 2026 structured rule {field} must equal {expected}")
        checkpoints = payload.get("freshness_checkpoints")
        if checkpoints != CUMCM_2026_CHECKPOINTS:
            errors.append("CUMCM 2026 freshness checkpoints must be T-30, T-7, and T-1")
        today = as_of_date or date.today()
        due = [item for item in CUMCM_2026_CHECKPOINTS if date.fromisoformat(item) <= today]
        latest_due_checkpoint = due[-1] if due else ""
        checked = parse_datetime(payload.get("created_at_utc"), "created_at_utc", errors)
        if checked is not None and latest_due_checkpoint:
            if checked.date() < date.fromisoformat(latest_due_checkpoint):
                errors.append(
                    "rules lock predates the latest freshness checkpoint "
                    f"{latest_due_checkpoint}; refresh official snapshots before use"
                )
    status = "FAIL" if errors else ("LIMITED" if warnings else "PASS")
    return {
        "status": status,
        "scope": "hash, freshness, official URL, and structured-rule verification",
        "profile_family": family,
        "mode": mode,
        "as_of_date": (as_of_date or date.today()).isoformat(),
        "latest_due_checkpoint": latest_due_checkpoint,
        "sources": source_reports,
        "errors": errors,
        "warnings": warnings,
    }


def parse_pairs(items: list[str], label: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise SystemExit(f"{label} must use key=value: {item}")
        key, value = item.split("=", 1)
        if not key.strip() or not value.strip():
            raise SystemExit(f"{label} must use non-empty key=value: {item}")
        values[key.strip()] = value.strip()
    return values


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def resolve_output(root: Path, value: Path, label: str, reports_only: bool) -> Path:
    path = (value if value.is_absolute() else root / value).resolve()
    try:
        path.relative_to(root / "reports" if reports_only else root)
    except ValueError as exc:
        location = "project reports directory" if reports_only else "project directory"
        raise SystemExit(f"{label} must stay inside the {location}") from exc
    return path


def same_file(left: Path, right: Path) -> bool:
    if left == right:
        return True
    try:
        return left.exists() and right.exists() and left.samefile(right)
    except OSError:
        return False


def bind_report(report: dict[str, Any], lock_path: Path, payload: Any) -> None:
    report["rules_lock_sha256"] = (
        sha256_file(lock_path) if lock_path.is_file() else ""
    )
    report["profile"] = (
        str(payload.get("profile") or "") if isinstance(payload, dict) else ""
    )
    report["valid_through"] = (
        str(payload.get("valid_through") or "") if isinstance(payload, dict) else ""
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create")
    create.add_argument("--project-dir", type=Path, required=True)
    create.add_argument("--contest", required=True)
    create.add_argument("--year", type=int, required=True)
    create.add_argument("--profile", required=True)
    create.add_argument("--valid-through", required=True)
    create.add_argument("--source-url", action="append", default=[])
    create.add_argument("--snapshot", action="append", default=[])
    create.add_argument("--source-role", action="append", default=[])
    create.add_argument("--source-kind", action="append", default=[])
    create.add_argument("--rule", action="append", default=[])
    create.add_argument("--checked-at")
    create.add_argument("--mode", choices=["precontest", "live"], default="precontest")
    create.add_argument("--out", type=Path, default=Path("rules.lock.json"))
    create.add_argument(
        "--report",
        type=Path,
        default=Path("reports/rules_lock_verification.json"),
    )
    validate = subparsers.add_parser("validate")
    validate.add_argument("--project-dir", type=Path, required=True)
    validate.add_argument("--lock", type=Path, default=Path("rules.lock.json"))
    validate.add_argument("--as-of-date", type=date.fromisoformat)
    validate.add_argument("--mode", choices=["precontest", "live"], default="precontest")
    validate.add_argument(
        "--out",
        type=Path,
        default=Path("reports/rules_lock_verification.json"),
    )
    args = parser.parse_args()
    root = args.project_dir.resolve()
    if args.command == "create":
        lock_path = resolve_output(root, args.out, "rules lock output", False)
        report_path = resolve_output(root, args.report, "verification report", True)
        if same_file(lock_path, report_path):
            raise SystemExit("rules lock and verification report must use different files")
        if len(args.source_url) != len(args.snapshot) or not args.source_url:
            raise SystemExit(
                "provide the same non-zero number of --source-url and --snapshot values"
            )
        if args.source_role and len(args.source_role) != len(args.source_url):
            raise SystemExit("--source-role must be omitted or match the source count")
        if args.source_kind and len(args.source_kind) != len(args.source_url):
            raise SystemExit("--source-kind must be omitted or match the source count")
        if args.profile.lower() == "cumcm-2026" and not args.source_role:
            raise SystemExit("cumcm-2026 requires --source-role for every official source")
        if args.profile.lower() == "cumcm-2026" and not args.source_kind:
            raise SystemExit("cumcm-2026 requires --source-kind for every official source")
        rules = parse_pairs(args.rule, "--rule")
        sources: list[dict[str, Any]] = []
        roles = args.source_role or [""] * len(args.source_url)
        kinds = args.source_kind or [""] * len(args.source_url)
        for role, kind, url, raw_path in zip(
            roles, kinds, args.source_url, args.snapshot
        ):
            path = safe_project_file(root, raw_path)
            if path is None or not path.is_file():
                raise SystemExit(f"snapshot must be an existing project file: {raw_path}")
            if same_file(path.resolve(), lock_path) or same_file(
                path.resolve(), report_path
            ):
                raise SystemExit("rules lock outputs must not overwrite a source snapshot")
            sources.append(
                {
                    "role": role,
                    "kind": kind,
                    "url": url,
                    "snapshot": path.relative_to(root).as_posix(),
                    "sha256": sha256_file(path),
                    "size_bytes": path.stat().st_size,
                }
            )
        checked_at = args.checked_at or datetime.now(timezone.utc).isoformat()
        checked = parse_datetime(checked_at, "--checked-at", [])
        if checked is None:
            raise SystemExit("--checked-at must be an ISO-8601 datetime with timezone")
        payload = {
            "schema_version": 2,
            "contest": args.contest,
            "year": args.year,
            "profile": args.profile,
            "created_at_utc": checked.isoformat(),
            "valid_through": args.valid_through,
            "sources": sources,
            "rules": rules,
        }
        if args.profile.lower() == "cumcm-2026":
            payload["freshness_checkpoints"] = CUMCM_2026_CHECKPOINTS
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        report = validate_lock(root, payload, mode=args.mode)
    else:
        lock_path = resolve_output(root, args.lock, "rules lock input", False)
        report_path = resolve_output(root, args.out, "verification report", True)
        if same_file(lock_path, report_path):
            raise SystemExit("verification report must not overwrite the rules lock")
        try:
            payload = json.loads(lock_path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            payload = {}
            report = {
                "status": "FAIL",
                "scope": "hash, freshness, official URL, and structured-rule verification",
                "sources": [],
                "errors": [f"cannot read rules lock: {exc}"],
                "warnings": [],
            }
        else:
            report = validate_lock(
                root, payload, as_of_date=args.as_of_date, mode=args.mode
            )
            for source in payload.get("sources") or []:
                if not isinstance(source, dict):
                    continue
                snapshot = safe_project_file(
                    root, str(source.get("snapshot") or "")
                )
                if snapshot is not None and same_file(report_path, snapshot):
                    raise SystemExit(
                        "verification report must not overwrite a rule snapshot"
                    )
    bind_report(report, lock_path, payload)
    write_report(report_path, report)
    print(report["status"])
    return {"PASS": 0, "FAIL": 1, "LIMITED": 2}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
