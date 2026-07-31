#!/usr/bin/env python3
"""Validate invocation, capability, reference, and mirror contracts."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"
EVALS = ROOT / "evals" / "invocation-cases.json"
CONTRACT = ROOT / "assets" / "skill-contract.json"


def fail(message: str) -> None:
    raise SystemExit(message)


def load_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(f"cannot read {label}: {exc}")


def require_phrases(relative: str, phrases: list[str]) -> None:
    path = ROOT / relative
    if not path.is_file():
        fail(f"missing contract file: {relative}")
    contents = path.read_text(encoding="utf-8")
    missing = [phrase for phrase in phrases if phrase not in contents]
    if missing:
        fail(f"{relative} missing contract: " + ", ".join(missing))


def main() -> int:
    contract = load_json(CONTRACT, "skill contract")
    if not isinstance(contract, dict) or contract.get("schema_version") != 1:
        fail("unsupported skill contract schema")
    text = SKILL.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        fail("SKILL.md must start with YAML frontmatter")
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not match:
        fail("SKILL.md frontmatter is malformed")
    frontmatter = match.group(1)
    expected_name = f"name: {contract['skill_name']}"
    if expected_name not in frontmatter:
        fail("skill name mismatch")
    description = next(
        (
            line.split(":", 1)[1].strip()
            for line in frontmatter.splitlines()
            if line.startswith("description:")
        ),
        "",
    )
    missing = [
        phrase for phrase in contract["description_phrases"] if phrase not in description
    ]
    if missing:
        fail("explicit invocation contract missing: " + ", ".join(missing))
    missing = [phrase for phrase in contract["body_phrases"] if phrase not in text]
    if missing:
        fail("SKILL.md missing core capability: " + ", ".join(missing))
    if len(text.splitlines()) >= 400:
        fail("SKILL.md must stay below the 400-line routing budget")

    for relative, phrases in contract["descriptor_checks"].items():
        require_phrases(relative, phrases)
    for relative, phrases in contract["content_checks"].items():
        require_phrases(relative, phrases)
    for relative in contract["required_files"]:
        if not (ROOT / relative).is_file():
            fail(f"missing required resource: {relative}")

    readme = (ROOT / "README.md").read_bytes()
    if readme != (ROOT / "README.en.md").read_bytes():
        fail("README.md and README.en.md must remain identical English mirrors")

    references = set(re.findall(r"`(references/embedded/[^`]+\.md)`", text))
    embedded = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "references" / "embedded").glob("*.md")
    }
    missing_files = sorted(relative for relative in references if not (ROOT / relative).is_file())
    if missing_files:
        fail("missing referenced file(s): " + ", ".join(missing_files))
    not_direct = sorted(embedded - references)
    if not_direct:
        fail("embedded references not directly routed by SKILL.md: " + ", ".join(not_direct))
    for relative in sorted(embedded):
        contents = (ROOT / relative).read_text(encoding="utf-8")
        if len(contents.splitlines()) > 100 and "## Contents" not in contents:
            fail(f"long reference needs a Contents section: {relative}")

    payload = load_json(EVALS, "invocation evals")
    cases = payload.get("cases", []) if isinstance(payload, dict) else []
    if not cases or {item.get("expected") for item in cases} != {"invoke", "do_not_invoke"}:
        fail("invocation evals need positive and negative cases")
    for item in cases:
        prompt = item.get("prompt", "")
        explicit = (
            "$mathematical-modeling-competition-copilot" in prompt
            or re.search(
                r"mathematical-modeling-competition-copilot[\\/]SKILL\.md",
                prompt,
                re.IGNORECASE,
            )
            is not None
        )
        if (item.get("expected") == "invoke") != explicit:
            fail(f"invalid invocation case: {item.get('id')}")
    print(f"PASS references={len(references)} cases={len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
