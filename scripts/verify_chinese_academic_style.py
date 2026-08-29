#!/usr/bin/env python3
"""Emit an advisory, artifact-located audit of Chinese academic LaTeX prose."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from verify_latex_compatibility import reachable_tex_files, source_fingerprint


EXEMPTION_FIELDS = {
    "finding_sha256",
    "rule",
    "source_file",
    "line",
    "reason",
    "reviewer",
    "status",
}
COMPLETE = {"verified", "pass", "complete", "accepted"}
SEVERITY_RANK = {"minor": 1, "major": 2}
TARGETS = (
    "paper/sections/abstract.tex",
    "paper/sections/conclusion.tex",
)
VALUE_COMMAND = re.compile(r"\\VerifiedValue(?:WithUnit)?\s*\{[^{}]+\}")
EVIDENCE_COMMAND = re.compile(
    r"\\(?:ref|eqref|autoref|cref|Cref|cite|citep|citet|parencite|textcite)"
    r"\*?(?:\s*\[[^\]]*\]){0,2}\s*\{[^{}]+\}"
)
MATH = re.compile(r"\$[^$]*\$|\\\([^)]*\\\)|\\\[[^]]*\\\]", re.DOTALL)
HEADING_COMMAND = re.compile(
    r"\\(?:part|chapter|section|subsection|subsubsection|paragraph)"
    r"\*?(?:\[[^\]]*\])?\{[^{}]*\}"
)
COMMAND_WITH_TEXT = re.compile(r"\\[A-Za-z@]+\*?(?:\[[^\]]*\])?\{([^{}]*)\}")
COMMAND = re.compile(r"\\[A-Za-z@]+\*?(?:\[[^\]]*\])?")
ABBREVIATION = re.compile(r"(?<![A-Za-z0-9])([A-Z][A-Z0-9-]{1,})(?![A-Za-z0-9])")
VAGUE = re.compile(r"显著|明显|较好|有效|优异|较高|大幅|具有优势|表现良好")
MECHANICAL_OPENING = re.compile(
    r"^(首先|其次|再次|最后|综上所述|由此可见|值得注意的是|需要指出的是)[，,]?"
)
METHOD_OPENING = re.compile(
    r"^(?:(?:首先|其次|再次|最后)[，,]?)?(?:我们)?(?:建立|采用|使用|引入|构建)"
)
GENERIC_MODEL_PRAISE = re.compile(
    r"(?:模型|方法|方案).{0,12}(?:显著优势|明显优势|优异|表现良好|效果较好)"
)
UNBOUNDED_SCOPE = re.compile(r"适用于所有|在任何情况下|完全适用|普遍适用|无论.{0,20}均")
SCOPE_QUALIFIER = re.compile(r"条件|范围内|边界|仅|当|若|除外|限制|测试区间")
CAUSAL = re.compile(r"导致|造成|促进|抑制|驱动|使得|决定了")
CAUSAL_QUALIFIER = re.compile(
    r"可能|相关|关联|证据不足|无法识别|不能识别|因果图|混杂|反事实|"
    r"工具变量|随机试验|断点|双重差分|识别假设|因果效应"
)
PRECISION = re.compile(
    r"(?<![A-Za-z0-9])[-+]?\d+\.(\d+)\s*"
    r"(%|％|mm|cm|km|kg|mg|m|s|h|元|万元|人|次|度|℃)"
)
SENTENCE_SPLIT = re.compile(r"[^。！？!?；;]+[。！？!?；;]?")
CHINESE = re.compile(r"[\u3400-\u9fff]")


@dataclass(frozen=True)
class Sentence:
    source_file: str
    line: int
    text: str


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def strip_comment(line: str) -> str:
    for index, character in enumerate(line):
        if character != "%":
            continue
        slashes = 0
        cursor = index - 1
        while cursor >= 0 and line[cursor] == "\\":
            slashes += 1
            cursor -= 1
        if slashes % 2 == 0:
            return line[:index]
    return line


def prose_line(raw: str) -> str:
    text = strip_comment(raw).replace("\\%", "%")
    text = VALUE_COMMAND.sub("【已验证数值】", text)
    text = EVIDENCE_COMMAND.sub("【证据】", text)
    text = MATH.sub(" ", text)
    text = HEADING_COMMAND.sub(" ", text)
    previous = None
    while previous != text:
        previous = text
        text = COMMAND_WITH_TEXT.sub(r"\1", text)
    text = COMMAND.sub(" ", text)
    text = text.replace("~", " ").replace("{", " ").replace("}", " ")
    return re.sub(r"\s+", " ", text).strip()


def normalize_sentence(text: str) -> str:
    return re.sub(r"[\s，。！？；、,:：;.!?（）()【】\[\]“”\"'—-]+", "", text)


def finding(
    rule: str,
    severity: str,
    source_file: str,
    line: int,
    message: str,
    excerpt: str,
) -> dict[str, Any]:
    normalized_excerpt = normalize_sentence(excerpt)[:240]
    digest = hashlib.sha256(
        f"{rule}\0{source_file}\0{line}\0{normalized_excerpt}".encode("utf-8")
    ).hexdigest()
    return {
        "finding_sha256": digest,
        "rule": rule,
        "severity": severity,
        "source_file": source_file,
        "line": line,
        "message": message,
        "excerpt": excerpt[:200],
    }


def read_exemptions(path: Path) -> tuple[list[dict[str, str]], set[str], str | None]:
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            return list(reader), set(reader.fieldnames or []), None
    except (OSError, UnicodeError, csv.Error) as exc:
        return [], set(), str(exc)


def paragraphs_and_sentences(
    source_file: str, records: list[tuple[int, str]]
) -> tuple[list[tuple[int, str]], list[Sentence]]:
    paragraphs: list[tuple[int, str]] = []
    current: list[str] = []
    start = 1
    for line, text in records + [(-1, "")]:
        if text:
            if not current:
                start = line
            current.append(text)
        elif current:
            paragraphs.append((start, " ".join(current)))
            current = []
    sentences: list[Sentence] = []
    for line, paragraph in paragraphs:
        for match in SENTENCE_SPLIT.finditer(paragraph):
            text = match.group(0).strip()
            if text and CHINESE.search(text):
                sentences.append(Sentence(source_file, line, text))
    return paragraphs, sentences


def collect_findings(
    files: list[Path], root: Path, max_sentence: int, max_paragraph: int
) -> tuple[list[dict[str, Any]], dict[str, str], int]:
    findings: list[dict[str, Any]] = []
    hashes: dict[str, str] = {}
    all_sentences: list[Sentence] = []
    abbreviation_seen: set[str] = set()
    precision_groups: dict[str, list[tuple[int, str, int]]] = {}
    self_references: list[tuple[str, int, str]] = []
    all_paragraphs: list[tuple[str, int, str]] = []
    chinese_characters = 0

    for path in files:
        relative = path.relative_to(root).as_posix()
        hashes[relative] = sha256(path)
        raw_lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
        records = [(line, prose_line(raw)) for line, raw in enumerate(raw_lines, 1)]
        chinese_characters += sum(len(CHINESE.findall(text)) for _, text in records)
        paragraphs, sentences = paragraphs_and_sentences(relative, records)
        all_paragraphs.extend((relative, line, paragraph) for line, paragraph in paragraphs)
        all_sentences.extend(sentences)
        for line, paragraph in paragraphs:
            visible = len(re.sub(r"\s+", "", paragraph))
            if visible > max_paragraph:
                findings.append(
                    finding(
                        "long_paragraph",
                        "minor",
                        relative,
                        line,
                        f"paragraph has {visible} visible characters; review information density",
                        paragraph,
                    )
                )
        for line, text in records:
            for match in ABBREVIATION.finditer(text):
                abbreviation = match.group(1)
                definition = re.search(
                    rf"[\u3400-\u9fff]{{2,24}}[（(]\s*{re.escape(abbreviation)}\s*[）)]",
                    text,
                )
                if abbreviation not in abbreviation_seen and definition is None:
                    findings.append(
                        finding(
                            "undefined_abbreviation",
                            "major",
                            relative,
                            line,
                            f"define {abbreviation} at first use",
                            text,
                        )
                    )
                abbreviation_seen.add(abbreviation)
            for match in PRECISION.finditer(text):
                decimals = len(match.group(1))
                unit = match.group(2)
                precision_groups.setdefault(unit, []).append((decimals, relative, line))
            for match in re.finditer("本文", text):
                self_references.append((relative, line, text))

    for sentence in all_sentences:
        visible = len(re.sub(r"\s+", "", sentence.text))
        if visible > max_sentence:
            findings.append(
                finding(
                    "long_sentence",
                    "minor",
                    sentence.source_file,
                    sentence.line,
                    f"sentence has {visible} visible characters; consider splitting it",
                    sentence.text,
                )
            )
        has_evidence = bool(
            re.search(r"【已验证数值】|【证据】|\d", sentence.text)
        )
        if VAGUE.search(sentence.text) and not has_evidence:
            findings.append(
                finding(
                    "vague_claim",
                    "major",
                    sentence.source_file,
                    sentence.line,
                    "replace evaluative wording with a measured result or nearby evidence",
                    sentence.text,
                )
            )
        if CAUSAL.search(sentence.text) and not CAUSAL_QUALIFIER.search(sentence.text):
            findings.append(
                finding(
                    "causal_overclaim",
                    "major",
                    sentence.source_file,
                    sentence.line,
                    "qualify the causal verb or add identification evidence",
                    sentence.text,
                )
            )
        if GENERIC_MODEL_PRAISE.search(sentence.text) and not has_evidence:
            findings.append(
                finding(
                    "generic_model_praise",
                    "major",
                    sentence.source_file,
                    sentence.line,
                    "replace generic praise with the comparison metric and its evidence",
                    sentence.text,
                )
            )
        if UNBOUNDED_SCOPE.search(sentence.text) and not SCOPE_QUALIFIER.search(sentence.text):
            findings.append(
                finding(
                    "unbounded_scope_claim",
                    "major",
                    sentence.source_file,
                    sentence.line,
                    "state the tested scope and abnormal boundary conditions",
                    sentence.text,
                )
            )

    opening_groups: dict[str, list[tuple[str, int, str]]] = {}
    for relative, line, paragraph in all_paragraphs:
        normalized_opening = normalize_sentence(paragraph)[:7]
        if len(normalized_opening) >= 5:
            opening_groups.setdefault(normalized_opening, []).append((relative, line, paragraph))
    for occurrences in opening_groups.values():
        if len(occurrences) >= 3:
            relative, line, paragraph = occurrences[2]
            findings.append(
                finding(
                    "repetitive_paragraph_opening",
                    "minor",
                    relative,
                    line,
                    "three or more paragraphs repeat the same opening stem",
                    paragraph,
                )
            )

    mechanical = [sentence for sentence in all_sentences if MECHANICAL_OPENING.search(sentence.text)]
    if len(mechanical) >= 4 and len(mechanical) / max(len(all_sentences), 1) >= 0.4:
        sentence = mechanical[3]
        findings.append(
            finding(
                "mechanical_transition_density",
                "minor",
                sentence.source_file,
                sentence.line,
                "transition words dominate the prose; connect steps through problem-specific reasoning",
                sentence.text,
            )
        )
    catalogue = [sentence for sentence in all_sentences if METHOD_OPENING.search(sentence.text)]
    catalogue_without_evidence = [
        sentence
        for sentence in catalogue
        if not re.search(r"【已验证数值】|【证据】|\d", sentence.text)
    ]
    if len(catalogue_without_evidence) >= 4:
        sentence = catalogue_without_evidence[3]
        findings.append(
            finding(
                "method_catalogue",
                "minor",
                sentence.source_file,
                sentence.line,
                "the prose lists methods without linking each choice to evidence, diagnostics, or results",
                sentence.text,
            )
        )

    normalized: list[tuple[Sentence, str]] = [
        (sentence, normalize_sentence(sentence.text)) for sentence in all_sentences
    ]
    buckets: dict[str, list[tuple[Sentence, str]]] = {}
    for sentence, value in normalized:
        if len(value) < 12:
            continue
        candidates = buckets.setdefault(value[:8], [])
        duplicate = next(
            (
                prior
                for prior in candidates
                if value == prior[1]
                or (
                    min(len(value), len(prior[1])) >= 20
                    and SequenceMatcher(None, value, prior[1]).ratio() >= 0.92
                )
            ),
            None,
        )
        if duplicate is not None:
            findings.append(
                finding(
                    "duplicate_sentence",
                    "major",
                    sentence.source_file,
                    sentence.line,
                    f"sentence duplicates or nearly duplicates {duplicate[0].source_file}:{duplicate[0].line}",
                    sentence.text,
                )
            )
        candidates.append((sentence, value))

    for unit, occurrences in precision_groups.items():
        precisions = {item[0] for item in occurrences}
        if len(precisions) > 1:
            _, relative, line = occurrences[-1]
            findings.append(
                finding(
                    "precision_consistency",
                    "minor",
                    relative,
                    line,
                    f"raw quantities with unit {unit} use decimal precisions {sorted(precisions)}",
                    f"unit={unit}; precisions={sorted(precisions)}",
                )
            )

    reference_rate = 1000.0 * len(self_references) / max(chinese_characters, 1)
    if len(self_references) >= 4 and reference_rate > 8.0:
        relative, line, text = self_references[0]
        findings.append(
            finding(
                "excessive_self_reference",
                "minor",
                relative,
                line,
                f"本文 appears {len(self_references)} times ({reference_rate:.1f} per 1000 Chinese characters)",
                text,
            )
        )
    unique = {item["finding_sha256"]: item for item in findings}
    return list(unique.values()), hashes, chinese_characters


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--exemptions", default="reports/prose_style_exemptions.csv")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--max-sentence-chars", type=int, default=80)
    parser.add_argument("--max-paragraph-chars", type=int, default=450)
    parser.add_argument("--fail-on", choices=["none", "minor", "major"], default="none")
    args = parser.parse_args()

    root = args.project_dir.resolve()
    paper = root / "paper"
    out = args.out if args.out.is_absolute() else root / args.out
    errors: list[str] = []
    warnings: list[str] = []
    try:
        manifest = json.loads((root / "contest_manifest.json").read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        manifest = {}
    if isinstance(manifest, dict) and manifest.get("latex_template") == "mcm-icm":
        payload = {
            "schema_version": 1,
            "status": "PASS",
            "advisory_status": "NOT_APPLICABLE",
            "paper_source_sha256": source_fingerprint(paper) if paper.is_dir() else "",
            "source_sha256": {},
            "exemptions_sha256": "",
            "findings": [],
            "unresolved_findings": [],
            "exempted_findings": [],
            "errors": [],
            "warnings": ["Chinese academic-style audit is not applicable to the MCM/ICM template."],
        }
        write_report(out, payload)
        print("PASS")
        return 0
    if args.max_sentence_chars < 20 or args.max_paragraph_chars < 100:
        errors.append("sentence and paragraph thresholds are implausibly small")
    files = reachable_tex_files(paper) if paper.is_dir() else []
    if not files:
        errors.append("no reachable LaTeX source was found")
    reachable = {path.relative_to(root).as_posix() for path in files}
    for target in TARGETS:
        if target not in reachable:
            errors.append(f"required Chinese paper section is missing or unreachable: {target}")
    findings: list[dict[str, Any]] = []
    source_hashes: dict[str, str] = {}
    chinese_characters = 0
    if files:
        findings, source_hashes, chinese_characters = collect_findings(
            files, root, args.max_sentence_chars, args.max_paragraph_chars
        )
    if files and chinese_characters == 0:
        errors.append("reachable Chinese-paper sources contain no Chinese prose")

    exemption_path = root / args.exemptions
    exemption_rows, exemption_fields, exemption_error = read_exemptions(exemption_path)
    if exemption_error:
        errors.append(f"cannot read prose exemptions: {exemption_error}")
    if missing := EXEMPTION_FIELDS - exemption_fields:
        errors.append("prose_style_exemptions.csv missing fields: " + ", ".join(sorted(missing)))
    finding_by_hash = {item["finding_sha256"]: item for item in findings}
    exempted_hashes: set[str] = set()
    for row_number, row in enumerate(exemption_rows, 2):
        digest = str(row.get("finding_sha256") or "").strip().lower()
        if digest in exempted_hashes:
            errors.append(f"prose_style_exemptions.csv:{row_number} duplicates a finding")
        exempted_hashes.add(digest)
        current = finding_by_hash.get(digest)
        if current is None:
            errors.append(f"prose_style_exemptions.csv:{row_number} is stale or does not match a current finding")
            continue
        if (
            str(row.get("rule") or "").strip() != current["rule"]
            or str(row.get("source_file") or "").strip().replace("\\", "/")
            != current["source_file"]
            or str(row.get("line") or "").strip() != str(current["line"])
        ):
            errors.append(f"prose_style_exemptions.csv:{row_number} locator does not match the finding")
        if not str(row.get("reason") or "").strip() or not str(row.get("reviewer") or "").strip():
            errors.append(f"prose_style_exemptions.csv:{row_number} needs reason and reviewer")
        if str(row.get("status") or "").strip().casefold() not in COMPLETE:
            errors.append(f"prose_style_exemptions.csv:{row_number} is not verified")

    exempted = [item for item in findings if item["finding_sha256"] in exempted_hashes]
    unresolved = [item for item in findings if item["finding_sha256"] not in exempted_hashes]
    if unresolved:
        warnings.append(f"{len(unresolved)} advisory prose findings require human review")
    if args.fail_on != "none":
        threshold = SEVERITY_RANK[args.fail_on]
        promoted = [
            item for item in unresolved if SEVERITY_RANK[item["severity"]] >= threshold
        ]
        if promoted:
            errors.append(
                f"--fail-on {args.fail_on} promoted {len(promoted)} unresolved style findings"
            )
    status = "FAIL" if errors else "PASS"
    advisory_status = "REVIEW" if unresolved else "PASS"
    payload = {
        "schema_version": 1,
        "status": status,
        "advisory_status": advisory_status,
        "scope": "Heuristic Chinese prose review with human exceptions; findings are not automatic rewrites or judgments of mathematical truth.",
        "paper_source_sha256": source_fingerprint(paper) if paper.is_dir() else "",
        "source_sha256": source_hashes,
        "exemptions_sha256": sha256(exemption_path) if exemption_path.is_file() else "",
        "counts": {
            "reachable_tex_files": len(files),
            "chinese_characters": chinese_characters,
            "findings": len(findings),
            "unresolved": len(unresolved),
            "exempted": len(exempted),
        },
        "findings": findings,
        "unresolved_findings": unresolved,
        "exempted_findings": exempted,
        "errors": errors,
        "warnings": warnings,
    }
    write_report(out, payload)
    print(status)
    for error in errors:
        print(f"ERROR {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
