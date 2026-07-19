#!/usr/bin/env python3
"""Validate the skill's explicit invocation gate and local reference integrity."""
from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"
EVALS = ROOT / "evals" / "invocation-cases.json"


def fail(message: str) -> None:
    raise SystemExit(message)


def main() -> int:
    text = SKILL.read_text(encoding="utf-8")
    if not text.startswith("---\n"): fail("SKILL.md must start with YAML frontmatter")
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not match: fail("SKILL.md frontmatter is malformed")
    frontmatter = match.group(1)
    if "name: mathematical-modeling-competition-copilot" not in frontmatter: fail("skill name mismatch")
    description = next((line.split(":", 1)[1].strip() for line in frontmatter.splitlines() if line.startswith("description:")), "")
    required = ("Explicit-invocation-only", "Use ONLY", "$mathematical-modeling-competition-copilot", "Do not use it automatically")
    missing = [phrase for phrase in required if phrase not in description]
    if missing: fail("explicit invocation contract missing: " + ", ".join(missing))
    body_required = ("Do not infer invocation", "unless the user explicitly calls this skill")
    missing_body = [phrase for phrase in body_required if phrase not in text]
    if missing_body: fail("body invocation gate missing: " + ", ".join(missing_body))
    descriptor_checks = {
        "README.md": "Explicit Invocation Only",
        "README.en.md": "Explicit Invocation Only",
        "README.zh-CN.md": "仅限显式调用",
        "DESCRIPTION.md": "Explicit-invocation-only",
        "agents/openai.yaml": "Explicit-only",
    }
    for relative, phrase in descriptor_checks.items():
        if phrase not in (ROOT / relative).read_text(encoding="utf-8"):
            fail(f"{relative} does not preserve the explicit invocation contract")
    delivery_checks = {
        "SKILL.md": ("at least 10", "paper/main.pdf", "support.zip", "scripts/verify_paper_delivery.py", "scripts/verify_paper_depth.py", "scripts/verify_portable_latex.py"),
        "README.md": ("at least 10", "paper/main.pdf", "support.zip"),
        "README.en.md": ("at least 10", "paper/main.pdf", "support.zip"),
        "README.zh-CN.md": ("至少 10", "paper/main.pdf", "support.zip"),
        "references/embedded/verified-literature-and-two-part-delivery.md": (
            "Google Scholar", "reports/bibliography.csv", "support/materials_manifest.csv"
        ),
    }
    for relative, phrases in delivery_checks.items():
        path = ROOT / relative
        if not path.is_file(): fail(f"missing delivery contract file: {relative}")
        contents = path.read_text(encoding="utf-8")
        missing_delivery = [phrase for phrase in phrases if phrase not in contents]
        if missing_delivery:
            fail(f"{relative} missing delivery contract: " + ", ".join(missing_delivery))
    for relative in ("scripts/build_support_archive.py", "scripts/verify_paper_delivery.py", "scripts/verify_paper_depth.py", "scripts/verify_portable_latex.py"):
        if not (ROOT / relative).is_file(): fail(f"missing delivery script: {relative}")
    portable_reference = ROOT / "references" / "embedded" / "latex-paper-pipeline.md"
    for phrase in (".vscode/settings.json", ".latexmkrc", "%DOCFILE%", "Ctrl+Alt+V", "verify_portable_latex.py"):
        if phrase not in portable_reference.read_text(encoding="utf-8"):
            fail(f"latex-paper-pipeline.md missing portable LaTeX contract: {phrase}")
    references = set(re.findall(r"`(references/embedded/[^`]+\.md)`", text))
    for relative in references:
        if not (ROOT / relative).is_file(): fail(f"missing referenced file: {relative}")
    payload = json.loads(EVALS.read_text(encoding="utf-8"))
    cases = payload.get("cases", [])
    if not cases or {item.get("expected") for item in cases} != {"invoke", "do_not_invoke"}: fail("invocation evals need positive and negative cases")
    for item in cases:
        prompt = item.get("prompt", "")
        explicit = "$mathematical-modeling-competition-copilot" in prompt or "mathematical-modeling-competition-copilot\\SKILL.md" in prompt
        if (item.get("expected") == "invoke") != explicit: fail(f"invalid invocation case: {item.get('id')}")
    print(f"PASS references={len(references)} cases={len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
