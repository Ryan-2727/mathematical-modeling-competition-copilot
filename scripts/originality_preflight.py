#!/usr/bin/env python3
"""Run a local, text-only originality preflight on a complete LaTeX paper."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable


TEXT_SUFFIXES = {".pdf", ".tex", ".md", ".txt"}
EXCLUDED_ENVS = {
    "equation", "equation*", "align", "align*", "gather", "gather*",
    "multline", "multline*", "lstlisting", "verbatim", "thebibliography",
}
EXCLUDED_FILES = {"ai_declaration.tex", "references.bib"}
# Character bigrams retain useful recall for short Chinese modeling paragraphs
# where a few connective-word edits can break most 4-gram overlaps.
NGRAM_SIZE = 2
MIN_PARAGRAPH_CHARS = 12
SOURCE_EXCERPT_LIMIT = 160
MAX_CANDIDATES = 50
REVIEW_FIELDS = (
    "finding_id", "draft_sha256", "disposition", "reason", "reviewer", "status",
)
VALID_DISPOSITIONS = {"resolved", "accepted_with_citation", "false_positive"}


@dataclass(frozen=True)
class Paragraph:
    text: str
    normalized: str
    source: str
    line_start: int | None = None
    line_end: int | None = None
    page: int | None = None


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def safe_project_path(root: Path, value: Path, label: str) -> Path:
    path = value.resolve() if value.is_absolute() else (root / value).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{label} must stay inside the project directory") from exc
    return path


def strip_comment(line: str) -> str:
    result: list[str] = []
    escaped = False
    for char in line:
        if char == "%" and not escaped:
            break
        result.append(char)
        if char == "\\":
            escaped = not escaped
        else:
            escaped = False
    return "".join(result)


def normalize(value: str) -> str:
    return "".join(re.findall(r"[A-Za-z0-9\u4e00-\u9fff]", value.lower()))


def clean_latex_line(line: str) -> str:
    line = strip_comment(line).strip()
    if not line or re.match(r"\\(?:part|chapter|section|subsection|subsubsection)\*?\s*\{", line):
        return ""
    line = re.sub(r"\$[^$]*\$", " ", line)
    line = re.sub(r"\\\([^)]*\\\)", " ", line)
    line = re.sub(r"\\(?:cite\w*|ref|eqref|label|bibliography|bibliographystyle)\s*\{[^{}]*\}", " ", line)
    line = re.sub(r"\\(?:input|include)\s*\{[^{}]*\}", " ", line)
    line = re.sub(
        r"\\(?:includegraphics|lstinputlisting|url|path)\*?(?:\[[^\]]*\])?\s*\{[^{}]*\}",
        " ",
        line,
    )
    for _ in range(4):
        updated = re.sub(
            r"\\[A-Za-z@]+\*?(?:\[[^\]]*\])?\s*\{([^{}]*)\}", r"\1", line
        )
        if updated == line:
            break
        line = updated
    line = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^\]]*\])?", " ", line)
    line = line.replace("{", " ").replace("}", " ").replace("~", " ")
    return re.sub(r"\s+", " ", line).strip()


def text_paragraphs(
    text: str,
    source: str,
    *,
    latex: bool = False,
    page: int | None = None,
) -> list[Paragraph]:
    paragraphs: list[Paragraph] = []
    current: list[str] = []
    start: int | None = None
    end: int | None = None
    excluded_depth = 0
    display_math = False

    def flush() -> None:
        nonlocal current, start, end
        value = " ".join(current).strip()
        normalized = normalize(value)
        if len(normalized) >= MIN_PARAGRAPH_CHARS:
            paragraphs.append(Paragraph(value, normalized, source, start, end, page))
        current, start, end = [], None, None

    for number, raw in enumerate(text.splitlines(), 1):
        visible = strip_comment(raw) if latex else raw
        if latex:
            begins = re.findall(r"\\begin\{([^{}]+)\}", visible)
            ends = re.findall(r"\\end\{([^{}]+)\}", visible)
            excluded_begins = sum(item in EXCLUDED_ENVS for item in begins)
            excluded_ends = sum(item in EXCLUDED_ENVS for item in ends)
            if excluded_depth:
                excluded_depth = max(0, excluded_depth - excluded_ends)
                continue
            if excluded_begins:
                flush()
                excluded_depth = max(0, excluded_begins - excluded_ends)
                continue
            if display_math:
                if r"\]" in visible or visible.count("$$") % 2 == 1:
                    display_math = False
                continue
            if r"\[" in visible or "$$" in visible:
                flush()
                if not (r"\[" in visible and r"\]" in visible) and visible.count("$$") != 2:
                    display_math = True
                continue
            cleaned = clean_latex_line(visible)
        else:
            cleaned = re.sub(r"\s+", " ", visible).strip()
        if not cleaned:
            flush()
            continue
        if start is None:
            start = number
        end = number
        current.append(cleaned)
    flush()
    return paragraphs


def latex_paper_paragraphs(root: Path, main: Path) -> tuple[list[Paragraph], list[str]]:
    paragraphs: list[Paragraph] = []
    errors: list[str] = []
    visited: set[Path] = set()
    visiting: set[Path] = set()

    def visit(path: Path) -> None:
        resolved = path.resolve()
        try:
            relative = resolved.relative_to(root).as_posix()
        except ValueError:
            errors.append(f"LaTeX include is outside the project directory: {resolved}")
            return
        if resolved in visiting:
            errors.append(f"LaTeX include cycle detected at {relative}")
            return
        if resolved in visited:
            return
        if not resolved.is_file():
            errors.append(f"LaTeX source is missing: {relative}")
            return
        visiting.add(resolved)
        visited.add(resolved)
        try:
            source = resolved.read_text(encoding="utf-8-sig", errors="strict")
        except (OSError, UnicodeError) as exc:
            errors.append(f"cannot read LaTeX source {relative}: {exc}")
            visiting.remove(resolved)
            return
        if resolved.name not in EXCLUDED_FILES and "generated" not in resolved.parts:
            paragraphs.extend(text_paragraphs(source, relative, latex=True))
        for raw in source.splitlines():
            line = strip_comment(raw)
            for match in re.finditer(r"\\(?:input|include)\s*\{([^{}]+)\}", line):
                value = match.group(1).strip()
                candidate = Path(value)
                if candidate.suffix == "":
                    candidate = candidate.with_suffix(".tex")
                if candidate.is_absolute():
                    errors.append(f"LaTeX include is outside the project directory: {candidate}")
                    continue
                visit(resolved.parent / candidate)
        visiting.remove(resolved)

    visit(main)
    return paragraphs, errors


def extract_pdf(path: Path) -> tuple[list[Paragraph], str | None]:
    text_pages: list[str] = []
    executable = shutil.which("pdftotext")
    if executable:
        completed = subprocess.run(
            [executable, "-layout", "-enc", "UTF-8", str(path), "-"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if completed.returncode == 0:
            text_pages = completed.stdout.split("\f")
    if not text_pages:
        try:
            from pypdf import PdfReader  # type: ignore[import-not-found]

            text_pages = [(page.extract_text() or "") for page in PdfReader(str(path)).pages]
        except Exception:  # Parser failures make this corpus file explicitly LIMITED.
            text_pages = []
    paragraphs = [
        paragraph
        for page_number, text in enumerate(text_pages, 1)
        for paragraph in text_paragraphs(text, str(path), page=page_number)
    ]
    if sum(len(item.normalized) for item in paragraphs) < 40:
        return [], "no adequate local text extraction; OCR and images were not used"
    return paragraphs, None


def corpus_paragraphs(paths: Iterable[Path]) -> tuple[list[Paragraph], list[dict[str, str]], int]:
    paragraphs: list[Paragraph] = []
    unreadable: list[dict[str, str]] = []
    files = 0
    for root in paths:
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            files += 1
            if path.suffix.lower() == ".pdf":
                extracted, reason = extract_pdf(path)
            else:
                try:
                    text = path.read_text(encoding="utf-8-sig", errors="strict")
                except (OSError, UnicodeError) as exc:
                    extracted, reason = [], str(exc)
                else:
                    extracted = text_paragraphs(
                        text, str(path), latex=path.suffix.lower() == ".tex"
                    )
                    reason = None if extracted else "no adequate extractable prose"
            if reason:
                unreadable.append({"path": str(path), "reason": reason})
            paragraphs.extend(extracted)
    return paragraphs, unreadable, files


def ngrams(value: str, size: int = NGRAM_SIZE) -> set[str]:
    if len(value) < size:
        return set()
    return {value[index:index + size] for index in range(len(value) - size + 1)}


def matching_coverage(blocks: list[Any], target_length: int) -> tuple[float, int]:
    intervals = sorted((item.a, item.a + item.size) for item in blocks if item.size >= 6)
    merged: list[list[int]] = []
    for start, end in intervals:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    covered = sum(end - start for start, end in merged)
    independent = sum(1 for item in blocks if item.size >= 12)
    return covered / max(1, target_length), independent


def classify(longest: int, jaccard: float, coverage: float, windows: int, comparable: int) -> str | None:
    if (
        longest >= 24
        or (comparable >= 40 and jaccard >= 0.65)
        or (coverage >= 0.35 and windows > 1)
    ):
        return "HIGH"
    if longest >= 12 or (comparable >= 40 and jaccard >= 0.45) or coverage >= 0.20:
        return "MEDIUM"
    if longest >= 8 or (comparable >= 40 and jaccard >= 0.30):
        return "LOW"
    return None


def source_excerpt(source: Paragraph, block: Any) -> str:
    normalized = source.normalized
    if len(normalized) <= SOURCE_EXCERPT_LIMIT:
        return source.text[:SOURCE_EXCERPT_LIMIT]
    center = block.b + block.size // 2
    start = max(0, center - SOURCE_EXCERPT_LIMIT // 2)
    return normalized[start:start + SOURCE_EXCERPT_LIMIT]


def find_matches(draft: list[Paragraph], corpus: list[Paragraph]) -> list[dict[str, Any]]:
    gram_sets = [ngrams(item.normalized) for item in corpus]
    index: dict[str, set[int]] = defaultdict(set)
    for index_number, grams in enumerate(gram_sets):
        for gram in grams:
            index[gram].add(index_number)
    findings: list[dict[str, Any]] = []
    for paragraph in draft:
        target_grams = ngrams(paragraph.normalized)
        candidate_counts: Counter[int] = Counter()
        for gram in target_grams:
            candidate_counts.update(index.get(gram, ()))
        best: dict[str, Any] | None = None
        for candidate, _ in candidate_counts.most_common(MAX_CANDIDATES):
            source = corpus[candidate]
            source_grams = gram_sets[candidate]
            union = target_grams | source_grams
            jaccard = len(target_grams & source_grams) / len(union) if union else 0.0
            matcher = SequenceMatcher(None, paragraph.normalized, source.normalized, autojunk=False)
            blocks = matcher.get_matching_blocks()
            longest_block = max(blocks, key=lambda item: item.size)
            coverage, windows = matching_coverage(blocks, len(paragraph.normalized))
            risk = classify(
                longest_block.size,
                jaccard,
                coverage,
                windows,
                min(len(paragraph.normalized), len(source.normalized)),
            )
            if risk is None:
                continue
            score = ({"HIGH": 3, "MEDIUM": 2, "LOW": 1}[risk], coverage, jaccard, longest_block.size)
            if best is None or score > best["_score"]:
                reasons: list[str] = []
                if longest_block.size >= 24:
                    reasons.append("exact normalized run >= 24 characters")
                elif longest_block.size >= 12:
                    reasons.append("exact normalized run is 12--23 characters")
                if min(len(paragraph.normalized), len(source.normalized)) >= 40:
                    if jaccard >= 0.65:
                        reasons.append("character-bigram Jaccard >= 0.65")
                    elif jaccard >= 0.45:
                        reasons.append("character-bigram Jaccard >= 0.45")
                if coverage >= 0.35 and windows > 1:
                    reasons.append("matched coverage >= 35% across multiple windows")
                elif coverage >= 0.20:
                    reasons.append("matched coverage >= 20%")
                draft_hash = sha256_text(paragraph.text)
                identity = "|".join(
                    (
                        draft_hash,
                        paragraph.source,
                        str(paragraph.line_start or ""),
                        source.source,
                        str(source.page or source.line_start or ""),
                    )
                )
                best = {
                    "finding_id": sha256_text(identity)[:20],
                    "risk": risk,
                    "draft_path": paragraph.source,
                    "draft_line_start": paragraph.line_start,
                    "draft_line_end": paragraph.line_end,
                    "draft_sha256": draft_hash,
                    "draft_paragraph": paragraph.text,
                    "corpus_path": source.source,
                    "corpus_page": source.page,
                    "corpus_line_start": source.line_start,
                    "corpus_line_end": source.line_end,
                    "source_excerpt": source_excerpt(source, longest_block),
                    "longest_exact_run": longest_block.size,
                    "ngram_jaccard": round(jaccard, 6),
                    "matched_coverage": round(coverage, 6),
                    "independent_matching_windows": windows,
                    "risk_reasons": reasons,
                    "remediation": (
                        "Cite the true source, remove boilerplate, or rewrite from the "
                        "team's own mechanism, model-choice, parameter, computation, and validation evidence."
                    ),
                    "_score": score,
                }
        if best is not None and best["risk"] in {"HIGH", "MEDIUM"}:
            best.pop("_score", None)
            findings.append(best)
    order = {"HIGH": 0, "MEDIUM": 1}
    findings.sort(key=lambda item: (order[item["risk"]], item["draft_path"], item["draft_line_start"] or 0))
    return findings


def read_reviews(path: Path) -> tuple[dict[str, dict[str, str]], list[str]]:
    if not path.is_file():
        return {}, []
    errors: list[str] = []
    reviews: dict[str, dict[str, str]] = {}
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            missing = set(REVIEW_FIELDS) - set(reader.fieldnames or [])
            if missing:
                errors.append("originality_review.csv missing columns: " + ", ".join(sorted(missing)))
            for line, row in enumerate(reader, 2):
                finding_id = str(row.get("finding_id") or "").strip()
                if not finding_id or finding_id in reviews:
                    errors.append(f"originality_review.csv:{line} blank or duplicate finding_id")
                reviews[finding_id] = {key: str(row.get(key) or "").strip() for key in REVIEW_FIELDS}
    except (OSError, UnicodeError, csv.Error) as exc:
        errors.append(f"cannot read originality_review.csv: {exc}")
    return reviews, errors


def apply_reviews(findings: list[dict[str, Any]], reviews: dict[str, dict[str, str]]) -> tuple[list[str], list[str]]:
    unresolved: list[str] = []
    active = {item["finding_id"] for item in findings}
    stale = sorted(set(reviews) - active)
    for finding in findings:
        review = reviews.get(finding["finding_id"])
        accepted = bool(
            review
            and review["draft_sha256"] == finding["draft_sha256"]
            and review["disposition"] in VALID_DISPOSITIONS
            and review["reason"]
            and review["reviewer"]
            and review["status"] == "complete"
        )
        finding["review_status"] = "complete" if accepted else "pending"
        if not accepted:
            unresolved.append(finding["finding_id"])
    return unresolved, stale


def markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# 本地原创性预检报告",
        "",
        f"状态：**{report['status']}**",
        "",
        "> 本报告仅用于本地人工复核，不是知网查重率，也不替代官方双指标报告。",
        "",
        "## 必须人工处理的段落",
        "",
    ]
    if not report["findings"]:
        lines.append("未发现达到本地 HIGH/MEDIUM 阈值的段落。")
    for number, item in enumerate(report["findings"], 1):
        source_location = (
            f"第 {item['corpus_page']} 页"
            if item["corpus_page"]
            else f"第 {item['corpus_line_start']}--{item['corpus_line_end']} 行"
        )
        lines.extend(
            [
                "",
                f"### {number}. {item['risk']} — `{item['draft_path']}:{item['draft_line_start']}`",
                "",
                f"- 处置状态：`{item['review_status']}`",
                f"- 命中来源：`{item['corpus_path']}`，{source_location}",
                f"- 最长精确连续字符：{item['longest_exact_run']}",
                f"- n-gram Jaccard：{item['ngram_jaccard']:.3f}",
                f"- 本段匹配覆盖：{item['matched_coverage']:.1%}",
                f"- 命中原因：{'；'.join(item['risk_reasons'])}",
                "- 待人工优化段落：",
                "",
                item["draft_paragraph"],
                "",
                "- 来源核对短片段：",
                "",
                item["source_excerpt"],
                "",
                "- 修复方向：补充准确引用、删除无信息套话，或依据本队模型、参数、计算与验证证据重新组织论证。",
            ]
        )
    lines.extend(["", "## 未读取语料", ""])
    if report["unreadable_corpus"]:
        for item in report["unreadable_corpus"]:
            lines.append(f"- `{item['path']}`：{item['reason']}")
    else:
        lines.append("无。")
    lines.extend(
        [
            "",
            "## 阈值说明",
            "",
            "HIGH：精确连续字符不少于 24，或近似相似度不少于 0.65，或多窗口覆盖不少于 35%。",
            "MEDIUM：精确连续字符为 12--23，或近似相似度不少于 0.45，或覆盖不少于 20%。",
            "这些数值是本地段落风险启发式指标，不是整篇论文查重率。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--main-tex", type=Path)
    parser.add_argument("--corpus-dir", type=Path, action="append", default=[])
    parser.add_argument("--config", type=Path)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    parser.add_argument("--review-csv", type=Path, default=Path("reports/originality_review.csv"))
    parser.add_argument("--historical-corpus-confirmed", action="store_true")
    args = parser.parse_args()

    root = args.project_dir.resolve()
    errors: list[str] = []
    config: dict[str, Any] = {}
    try:
        out_json = safe_project_path(root, args.out_json, "--out-json")
        out_md = safe_project_path(root, args.out_md, "--out-md")
        review_csv = safe_project_path(root, args.review_csv, "--review-csv")
        config_path = (
            safe_project_path(root, args.config, "--config") if args.config else None
        )
        for label, output in (("--out-json", out_json), ("--out-md", out_md)):
            output.relative_to(root / "reports")
    except (ValueError, OSError) as exc:
        raise SystemExit(str(exc)) from exc

    if config_path:
        try:
            loaded = json.loads(config_path.read_text(encoding="utf-8-sig"))
            if not isinstance(loaded, dict):
                raise ValueError("configuration must be a JSON object")
            config = loaded
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"cannot read originality configuration: {exc}")
    main_value = args.main_tex or Path(str(config.get("main_tex") or "paper/main.tex"))
    try:
        main_tex = safe_project_path(root, main_value, "--main-tex")
    except (ValueError, OSError) as exc:
        errors.append(str(exc))
        main_tex = root / "paper" / "main.tex"

    mode = "unknown"
    try:
        manifest = json.loads((root / "contest_manifest.json").read_text(encoding="utf-8-sig"))
        mode = str(manifest.get("mode") or "unknown")
    except (OSError, json.JSONDecodeError, TypeError):
        pass
    historical_confirmed = args.historical_corpus_confirmed or config.get(
        "historical_corpus_confirmed"
    ) is True
    if mode == "live" and not historical_confirmed:
        errors.append(
            "live mode requires --historical-corpus-confirmed before reading a private corpus"
        )

    corpora: list[Path] = []
    configured_corpora = config.get("corpus_dirs", [])
    if not isinstance(configured_corpora, list) or not all(
        isinstance(item, str) for item in configured_corpora
    ):
        errors.append("originality configuration corpus_dirs must be a list of paths")
        configured_corpora = []
    raw_corpora = [Path(item) for item in configured_corpora] + list(args.corpus_dir)
    for raw in raw_corpora:
        corpus = raw.resolve() if raw.is_absolute() else (root / raw).resolve()
        if not corpus.is_dir():
            errors.append(f"corpus directory is missing: {corpus}")
            continue
        try:
            corpus.relative_to(root)
        except ValueError:
            pass
        else:
            errors.append(f"corpus directory must be outside the current project: {corpus}")
            continue
        try:
            root.relative_to(corpus)
        except ValueError:
            pass
        else:
            errors.append(f"corpus directory must not contain the project: {corpus}")
            continue
        corpora.append(corpus)

    draft, latex_errors = latex_paper_paragraphs(root, main_tex)
    errors.extend(latex_errors)
    if not draft:
        errors.append("no readable draft prose was resolved from the LaTeX paper")
    corpus, unreadable, corpus_files = corpus_paragraphs(corpora) if corpora else ([], [], 0)
    findings = find_matches(draft, corpus) if draft and corpus else []
    reviews, review_errors = read_reviews(review_csv)
    errors.extend(review_errors)
    unresolved, stale = apply_reviews(findings, reviews)

    limitations: list[str] = []
    if corpus_files == 0:
        limitations.append("no supported corpus files were found")
    if not corpus:
        limitations.append("no readable historical corpus prose was extracted")
    if unreadable:
        limitations.append(f"{len(unreadable)} corpus file(s) were not adequately extracted")
    if errors:
        status = "FAIL"
    elif unresolved:
        status = "REVIEW"
    elif limitations:
        status = "LIMITED"
    else:
        status = "PASS"
    report: dict[str, Any] = {
        "status": status,
        "scope": "local_text_only_originality_risk_preflight",
        "official_similarity_equivalent": False,
        "historical_corpus_confirmed": historical_confirmed,
        "project_dir": str(root),
        "main_tex": main_tex.relative_to(root).as_posix(),
        "draft_paragraphs": len(draft),
        "corpus_files": corpus_files,
        "corpus_paragraphs": len(corpus),
        "thresholds": {
            "high_exact_run": 24,
            "medium_exact_run": 12,
            "high_ngram_jaccard": 0.65,
            "medium_ngram_jaccard": 0.45,
            "high_matched_coverage": 0.35,
            "medium_matched_coverage": 0.20,
        },
        "findings": findings,
        "unresolved_findings": unresolved,
        "stale_reviews": stale,
        "unreadable_corpus": unreadable,
        "limitations": limitations,
        "errors": errors,
        "note": (
            "No network, OCR, image generation, official percentage estimation, "
            "or automatic replacement prose is part of this scan."
        ),
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(markdown_report(report), encoding="utf-8")
    print(status)
    return 1 if status == "FAIL" else 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
