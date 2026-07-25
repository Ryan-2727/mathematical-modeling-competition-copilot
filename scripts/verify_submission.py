#!/usr/bin/env python3
"""Verify submission artifacts against executable contest-rule profiles."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


CUMCM_FORMAT_URL = (
    "https://www.mcm.edu.cn/html_cn/node/"
    "4cd596519c9eb9fbd866398f6df0caa3.html"
)
CUMCM_AI_URL = (
    "https://www.mcm.edu.cn/html_cn/node/"
    "eebcfb6dc37fd2de9603dc16026fdf01.html"
)
MCM_RULES_URL = (
    "https://contest.comap.com/undergraduate/contests/mcm/instructions.php"
)
MCM_AI_URL = (
    "https://www.contest.comap.com/undergraduate/contests/mcm/"
    "flyer/Contest_AI_Policy.pdf"
)


PROFILES: dict[str, dict[str, Any]] = {
    "generic": {
        "paper_suffixes": {".pdf"},
        "support_suffixes": {".zip", ".rar"},
        "max_paper_mb": 20,
        "max_support_mb": 20,
    },
    "cumcm-2026": {
        "paper_suffixes": {".pdf", ".doc", ".docx"},
        "support_suffixes": {".zip", ".rar"},
        "max_paper_mb": 20,
        "max_support_mb": 20,
        "max_main_text_pages": 30,
        "toc_forbidden": True,
        "snapshot": {
            "profile_version": "cumcm-2026.2026-07-24",
            "verified_at": "2026-07-24",
            "valid_through": "2026-12-31",
            "source_urls": [CUMCM_FORMAT_URL, CUMCM_AI_URL],
        },
    },
    "mcm-icm-current": {
        "paper_suffixes": {".pdf"},
        "support_suffixes": set(),
        "max_paper_mb": 25,
        "max_counted_pages": 25,
        "minimum_font_pt": 12,
        "summary_first": True,
        "control_header_required": True,
        "support_forbidden": True,
        "ai_report_outside_count": True,
        "snapshot": {
            "profile_version": "mcm-icm-2027.2026-07-24",
            "verified_at": "2026-07-24",
            "valid_through": "2027-02-01",
            "source_urls": [MCM_RULES_URL, MCM_AI_URL],
        },
    },
}
PROFILES["mcm-icm-2027"] = PROFILES["mcm-icm-current"]
PROFILES["mcm-icm"] = PROFILES["mcm-icm-current"]


@dataclass
class PdfInspection:
    page_count: int | None
    page_texts: list[str] | None
    tools: dict[str, dict[str, Any]]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def profile_parameters(profile: dict[str, Any]) -> dict[str, Any]:
    return {
        key: sorted(value) if isinstance(value, set) else value
        for key, value in profile.items()
        if key != "snapshot"
    }


def profile_snapshot(profile: dict[str, Any]) -> dict[str, Any] | None:
    snapshot = profile.get("snapshot")
    if not snapshot:
        return None
    result = dict(snapshot)
    encoded = json.dumps(
        profile_parameters(profile),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    result["parameters_sha256"] = hashlib.sha256(encoded).hexdigest()
    return result


def inspect_pdf(path: Path) -> PdfInspection:
    tools: dict[str, dict[str, Any]] = {}
    page_count: int | None = None
    page_texts: list[str] | None = None

    pdfinfo = shutil.which("pdfinfo.exe") or shutil.which("pdfinfo")
    tools["pdfinfo"] = {
        "available": bool(pdfinfo),
        "scope": "PDF page count",
    }
    if pdfinfo:
        result = subprocess.run(
            [pdfinfo, str(path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        tools["pdfinfo"]["returncode"] = result.returncode
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if line.startswith("Pages:"):
                    try:
                        page_count = int(line.split(":", 1)[1].strip())
                    except ValueError:
                        pass
                    break
        if page_count is None:
            tools["pdfinfo"]["error"] = "page count was not returned"

    pdftotext = shutil.which("pdftotext.exe") or shutil.which("pdftotext")
    tools["pdftotext"] = {
        "available": bool(pdftotext),
        "scope": "first-page, contents, header, appendix, and AI text evidence",
    }
    if pdftotext and page_count is not None:
        extracted: list[str] = []
        extraction_error: str | None = None
        for page in range(1, page_count + 1):
            result = subprocess.run(
                [
                    pdftotext,
                    "-f",
                    str(page),
                    "-l",
                    str(page),
                    "-layout",
                    str(path),
                    "-",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            if result.returncode != 0:
                extraction_error = f"page {page} extraction returned {result.returncode}"
                break
            extracted.append(result.stdout)
        if extraction_error is None:
            page_texts = extracted
            tools["pdftotext"]["returncode"] = 0
        else:
            tools["pdftotext"]["returncode"] = result.returncode
            tools["pdftotext"]["error"] = extraction_error
    elif pdftotext and page_count is None:
        tools["pdftotext"]["error"] = "pdfinfo page count is unavailable"
    return PdfInspection(page_count=page_count, page_texts=page_texts, tools=tools)


def extract_docx_text(path: Path) -> str | None:
    if path.suffix.lower() != ".docx":
        return None
    try:
        with zipfile.ZipFile(path) as archive:
            content = archive.read("word/document.xml")
    except (KeyError, OSError, zipfile.BadZipFile):
        return None
    try:
        root = ElementTree.fromstring(content)
    except ElementTree.ParseError:
        return None
    return "\n".join(
        node.text or ""
        for node in root.iter()
        if node.tag.endswith("}t")
    )


def zip_names(path: Path) -> list[str] | None:
    if path.suffix.lower() != ".zip":
        return None
    try:
        with zipfile.ZipFile(path) as archive:
            return archive.namelist()
    except zipfile.BadZipFile:
        return []


def load_evidence(path: Path | None, paper: Path) -> tuple[dict[str, Any], list[str]]:
    if path is None:
        return {}, []
    errors: list[str] = []
    try:
        evidence = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"compliance evidence cannot be read: {exc}"]
    if not isinstance(evidence, dict):
        return {}, ["compliance evidence must be a JSON object"]
    expected_hash = evidence.get("paper_sha256")
    if expected_hash != sha256(paper):
        errors.append("compliance evidence paper_sha256 does not match the paper")
    if not evidence.get("reviewer"):
        errors.append("compliance evidence lacks reviewer")
    if not evidence.get("recorded_at"):
        errors.append("compliance evidence lacks recorded_at")
    return evidence, errors


def add_check(
    checks: list[dict[str, Any]],
    errors: list[str],
    limitations: list[str],
    check_id: str,
    passed: bool | None,
    message: str,
    scope: str,
    *,
    limited: bool = False,
) -> None:
    if passed is False:
        status = "FAIL"
        errors.append(message)
    elif limited:
        status = "LIMITED"
        limitations.append(message)
    elif passed is True:
        status = "PASS"
    else:
        status = "NOT_APPLICABLE"
    checks.append(
        {
            "id": check_id,
            "status": status,
            "scope": scope,
            "evidence": message,
        }
    )


def first_nonempty_lines(text: str, limit: int = 12) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines[:limit])


def has_toc(text: str) -> bool:
    return bool(
        re.search(
            r"(?im)^\s*(?:目\s*录|table\s+of\s+contents|contents)\s*$",
            text,
        )
    )


def has_abstract_marker(text: str) -> bool:
    return bool(re.search(r"(?im)^\s*(?:摘\s*要|abstract)(?:\b|$)", text))


def has_appendix_manifest(text: str, support_supplied: bool) -> tuple[bool, bool]:
    appendix = re.search(
        r"(?im)^\s*(?:[A-Z]\s+)?(?:附\s*录|appendix)(?:\s|$|[：:])",
        text,
    )
    if appendix is None:
        return False, False
    text = text[appendix.start() :]
    has_list = bool(
        re.search(
            r"(?:支撑材料.{0,12}文件列表|支撑材料.{0,12}清单|"
            r"support(?:ing)?\s+materials?.{0,20}(?:file\s+list|manifest))",
            text,
            re.IGNORECASE | re.DOTALL,
        )
    )
    has_code_or_declaration = bool(
        re.search(
            r"(?:完整.{0,8}(?:源程序|程序代码)|源程序代码|代码清单|"
            r"本论文没有用到程序|complete\s+(?:source\s+)?code|"
            r"source\s+code\s+listing|no\s+(?:source\s+)?code\s+was\s+used)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
    )
    if not support_supplied:
        has_list = has_list or bool(
            re.search(r"(?:本论文没有支撑材料|no supporting materials)", text, re.I)
        )
    return has_list, has_code_or_declaration


def has_ai_inline_disclosure(text: str) -> bool:
    patterns = (
        r"(?:AI|人工智能|ChatGPT|DeepSeek|Copilot).{0,50}"
        r"(?:生成|辅助|润色|翻译|编程|使用|produce|assist|translate|generate|use)",
        r"(?:生成|辅助|润色|翻译|编程|使用|produce|assist|translate|generate|use)"
        r".{0,50}(?:AI|人工智能|ChatGPT|DeepSeek|Copilot)",
    )
    return any(re.search(pattern, text, re.I | re.S) for pattern in patterns)


def has_ai_reference(text: str) -> bool:
    reference = re.search(
        r"(?:参考文献|references|bibliography)([\s\S]*)",
        text,
        re.IGNORECASE,
    )
    if not reference:
        return False
    return bool(
        re.search(
            r"(?:OpenAI|ChatGPT|DeepSeek|Copilot|Claude|Gemini|"
            r"人工智能工具|AI\s+tool)",
            reference.group(1),
            re.IGNORECASE,
        )
    )


def evidence_bool(evidence: dict[str, Any], key: str) -> bool:
    return evidence.get(key) is True


def verify_cumcm(
    *,
    paper: Path,
    support: Path | None,
    main_text_pages: int | None,
    require_ai_report: bool,
    inspection: PdfInspection | None,
    docx_text: str | None,
    evidence: dict[str, Any],
    checks: list[dict[str, Any]],
    errors: list[str],
    warnings: list[str],
    limitations: list[str],
) -> None:
    profile = PROFILES["cumcm-2026"]
    if main_text_pages is None:
        warnings.append(
            "main-text page count was not supplied; visual counting remains required"
        )
    else:
        add_check(
            checks,
            errors,
            limitations,
            "cumcm.main_text_pages",
            main_text_pages <= profile["max_main_text_pages"],
            (
                f"main text is {main_text_pages} pages; limit is "
                f"{profile['max_main_text_pages']}"
            ),
            "declared main-text count; appendix excluded",
        )

    page_texts = inspection.page_texts if inspection else None
    all_text = "\n".join(page_texts) if page_texts is not None else docx_text
    if page_texts:
        first_ok = has_abstract_marker(page_texts[0])
        add_check(
            checks,
            errors,
            limitations,
            "cumcm.first_page_abstract",
            first_ok,
            (
                "electronic paper first page contains an abstract marker"
                if first_ok
                else "electronic paper first page does not contain an abstract marker"
            ),
            "pdftotext first-page text",
        )
    elif evidence:
        first_ok = evidence_bool(evidence, "first_page_abstract")
        add_check(
            checks,
            errors,
            limitations,
            "cumcm.first_page_abstract",
            first_ok,
            (
                "hash-bound visual evidence records abstract as the first page"
                if first_ok
                else "visual evidence does not confirm abstract as the first page"
            ),
            "recorded visual evidence",
            limited=first_ok,
        )
    elif paper.suffix.lower() == ".pdf":
        add_check(
            checks,
            errors,
            limitations,
            "cumcm.first_page_abstract",
            False,
            "first-page abstract check requires pdftotext or hash-bound visual evidence",
            "PDF first-page content",
        )
    else:
        warnings.append(
            "Word first-page layout was not machine-inspected; preserve legacy "
            "CUMCM Word workflow and inspect it visually"
        )

    if all_text is not None:
        toc_ok = not has_toc(all_text)
        add_check(
            checks,
            errors,
            limitations,
            "cumcm.toc_forbidden",
            toc_ok,
            "no table-of-contents heading found" if toc_ok else "table of contents is forbidden",
            "extracted electronic-paper text",
        )
        manifest_ok, code_ok = has_appendix_manifest(
            all_text, support is not None and support.is_file()
        )
        add_check(
            checks,
            errors,
            limitations,
            "cumcm.appendix_support_manifest",
            manifest_ok,
            (
                "appendix contains support-file list or no-support declaration"
                if manifest_ok
                else "appendix lacks support-file list or no-support declaration"
            ),
            "extracted appendix text",
        )
        add_check(
            checks,
            errors,
            limitations,
            "cumcm.appendix_code_evidence",
            code_ok,
            (
                "appendix contains complete-code evidence or a no-program declaration"
                if code_ok
                else "appendix lacks complete-code evidence or a no-program declaration"
            ),
            "extracted appendix text",
        )
    elif evidence:
        for check_id, key, message in (
            (
                "cumcm.toc_forbidden",
                "toc_absent",
                "hash-bound visual evidence records no table of contents",
            ),
            (
                "cumcm.appendix_support_manifest",
                "appendix_support_manifest",
                "hash-bound evidence records the appendix support manifest",
            ),
            (
                "cumcm.appendix_code_evidence",
                "appendix_code_or_no_program",
                "hash-bound evidence records complete code or a no-program declaration",
            ),
        ):
            passed = evidence_bool(evidence, key)
            add_check(
                checks,
                errors,
                limitations,
                check_id,
                passed,
                message if passed else f"compliance evidence does not confirm {key}",
                "recorded visual evidence",
                limited=passed,
            )
    elif paper.suffix.lower() == ".pdf":
        for check_id, description in (
            ("cumcm.toc_forbidden", "no-table-of-contents check"),
            ("cumcm.appendix_support_manifest", "appendix support-manifest check"),
            ("cumcm.appendix_code_evidence", "appendix code-evidence check"),
        ):
            add_check(
                checks,
                errors,
                limitations,
                check_id,
                False,
                f"{description} requires pdftotext or hash-bound evidence",
                "PDF content",
            )

    if require_ai_report:
        if support is None or not support.is_file():
            add_check(
                checks,
                errors,
                limitations,
                "cumcm.ai_report",
                False,
                "AI use requires a support archive containing AI工具使用详情.pdf",
                "support archive contents",
            )
        else:
            names = zip_names(support)
            if names is None:
                add_check(
                    checks,
                    errors,
                    limitations,
                    "cumcm.ai_report",
                    True,
                    "RAR contents were not inspected; confirm AI工具使用详情.pdf manually",
                    "RAR archive content inspection unavailable",
                    limited=True,
                )
            else:
                present = any(
                    Path(name).name == "AI工具使用详情.pdf" for name in names
                )
                add_check(
                    checks,
                    errors,
                    limitations,
                    "cumcm.ai_report",
                    present,
                    (
                        "support archive contains AI工具使用详情.pdf"
                        if present
                        else "support ZIP lacks AI工具使用详情.pdf"
                    ),
                    "ZIP archive member names",
                )
        if all_text is not None:
            inline_ok = has_ai_inline_disclosure(all_text)
            reference_ok = has_ai_reference(all_text)
            add_check(
                checks,
                errors,
                limitations,
                "cumcm.ai_inline_disclosure",
                inline_ok,
                (
                    "paper contains inline AI-use disclosure evidence"
                    if inline_ok
                    else "paper lacks inline AI-use disclosure evidence"
                ),
                "extracted electronic-paper text",
            )
            add_check(
                checks,
                errors,
                limitations,
                "cumcm.ai_reference",
                reference_ok,
                (
                    "reference section contains an AI-tool entry"
                    if reference_ok
                    else "reference section lacks an AI-tool entry"
                ),
                "extracted reference-section text",
            )
        elif evidence:
            for check_id, key, description in (
                (
                    "cumcm.ai_inline_disclosure",
                    "ai_inline_disclosure",
                    "inline AI disclosure",
                ),
                ("cumcm.ai_reference", "ai_reference_entry", "AI reference entry"),
            ):
                passed = evidence_bool(evidence, key)
                add_check(
                    checks,
                    errors,
                    limitations,
                    check_id,
                    passed,
                    (
                        f"hash-bound evidence records {description}"
                        if passed
                        else f"compliance evidence does not confirm {description}"
                    ),
                    "recorded content evidence",
                    limited=passed,
                )
        elif paper.suffix.lower() == ".pdf":
            for check_id, description in (
                ("cumcm.ai_inline_disclosure", "inline AI disclosure"),
                ("cumcm.ai_reference", "AI reference entry"),
            ):
                add_check(
                    checks,
                    errors,
                    limitations,
                    check_id,
                    False,
                    f"{description} check requires pdftotext or hash-bound evidence",
                    "PDF content",
                )
        else:
            warnings.append(
                "Word AI inline-disclosure and reference entries were not machine-inspected"
            )


def find_ai_report_start(page_texts: list[str]) -> int | None:
    for page_number, text in enumerate(page_texts, start=1):
        if re.search(r"report\s+on\s+use\s+of\s+ai(?:\s+tools)?", text, re.I):
            return page_number
    return None


def control_header_pages(
    page_texts: list[str], control_number: str, pages_to_check: int
) -> list[int]:
    missing: list[int] = []
    for page_number, text in enumerate(page_texts[:pages_to_check], start=1):
        header = first_nonempty_lines(text)
        if control_number not in header or not re.search(
            rf"(?:page\s*)?{page_number}\b", header, re.I
        ):
            missing.append(page_number)
    return missing


def verify_mcm_icm(
    *,
    paper: Path,
    support: Path | None,
    solution_pages: int | None,
    font_size_pt: float | None,
    control_number: str | None,
    require_ai_report: bool,
    inspection: PdfInspection | None,
    evidence: dict[str, Any],
    checks: list[dict[str, Any]],
    errors: list[str],
    limitations: list[str],
) -> None:
    profile = PROFILES["mcm-icm-current"]
    add_check(
        checks,
        errors,
        limitations,
        "mcm.support_forbidden",
        support is None,
        (
            "no additional support package supplied"
            if support is None
            else "MCM/ICM prohibits additional program, data, or support files"
        ),
        "submission artifact set",
    )

    declared_font = font_size_pt
    if declared_font is None and isinstance(evidence.get("font_size_pt"), (int, float)):
        declared_font = float(evidence["font_size_pt"])
    add_check(
        checks,
        errors,
        limitations,
        "mcm.minimum_font",
        declared_font is not None and declared_font >= profile["minimum_font_pt"],
        (
            f"declared body font is {declared_font:g}pt"
            if declared_font is not None and declared_font >= profile["minimum_font_pt"]
            else "declare a readable body font of at least 12pt with --font-size-pt"
        ),
        "explicit font-size declaration; visual typography still requires review",
    )

    control_ok = bool(control_number and re.fullmatch(r"\d{7}", control_number))
    add_check(
        checks,
        errors,
        limitations,
        "mcm.control_number",
        control_ok,
        (
            f"declared seven-digit control number is {control_number}"
            if control_ok
            else "MCM/ICM requires a seven-digit --control-number"
        ),
        "declared control-number format",
    )
    if control_ok:
        add_check(
            checks,
            errors,
            limitations,
            "mcm.filename",
            paper.stem == control_number,
            (
                "PDF filename matches the control number"
                if paper.stem == control_number
                else "PDF filename must equal the control number"
            ),
            "submission filename",
        )

    page_texts = inspection.page_texts if inspection else None
    page_count = inspection.page_count if inspection else None
    evidence_page_count = evidence.get("pdf_pages")
    if page_count is None and isinstance(evidence_page_count, int):
        page_count = evidence_page_count
        add_check(
            checks,
            errors,
            limitations,
            "mcm.pdf_page_count_tool",
            True,
            "pdfinfo unavailable; using hash-bound recorded page count",
            "recorded visual evidence",
            limited=True,
        )
    elif page_count is None:
        add_check(
            checks,
            errors,
            limitations,
            "mcm.pdf_page_count_tool",
            False,
            "MCM/ICM page counting requires pdfinfo or hash-bound pdf_pages evidence",
            "whole PDF page count",
        )

    if page_texts:
        summary_ok = bool(
            re.search(r"summary\s+sheet", page_texts[0], re.IGNORECASE)
        )
        add_check(
            checks,
            errors,
            limitations,
            "mcm.summary_first",
            summary_ok,
            (
                "Summary Sheet appears on the first page"
                if summary_ok
                else "the first PDF page must be the Summary Sheet"
            ),
            "pdftotext first-page text",
        )
    elif evidence:
        summary_ok = evidence_bool(evidence, "summary_sheet_first")
        add_check(
            checks,
            errors,
            limitations,
            "mcm.summary_first",
            summary_ok,
            (
                "hash-bound evidence records the Summary Sheet as page one"
                if summary_ok
                else "compliance evidence does not confirm Summary Sheet as page one"
            ),
            "recorded visual evidence",
            limited=summary_ok,
        )
    else:
        add_check(
            checks,
            errors,
            limitations,
            "mcm.summary_first",
            False,
            "Summary Sheet first-page check requires pdftotext or hash-bound evidence",
            "PDF first-page content",
        )

    ai_start = find_ai_report_start(page_texts) if page_texts else None
    if ai_start is None and isinstance(evidence.get("ai_report_start_page"), int):
        ai_start = evidence["ai_report_start_page"]
        add_check(
            checks,
            errors,
            limitations,
            "mcm.ai_boundary_source",
            True,
            "AI report start page comes from hash-bound evidence",
            "recorded visual evidence",
            limited=True,
        )
    if require_ai_report and ai_start is None:
        add_check(
            checks,
            errors,
            limitations,
            "mcm.ai_report",
            False,
            "AI use requires a Report on Use of AI after the counted solution",
            "PDF page text or recorded AI boundary",
        )
    elif ai_start is not None:
        add_check(
            checks,
            errors,
            limitations,
            "mcm.ai_report",
            True,
            f"Report on Use of AI starts on PDF page {ai_start}",
            "AI report count boundary",
        )

    inferred_counted = None
    if page_count is not None:
        inferred_counted = ai_start - 1 if ai_start is not None else page_count
    counted_pages = solution_pages if solution_pages is not None else inferred_counted
    if (
        solution_pages is not None
        and inferred_counted is not None
        and solution_pages != inferred_counted
    ):
        add_check(
            checks,
            errors,
            limitations,
            "mcm.page_count_consistency",
            False,
            (
                f"declared counted pages ({solution_pages}) do not match PDF/AI "
                f"boundary ({inferred_counted})"
            ),
            "declared count versus PDF boundary",
        )
    if counted_pages is None:
        add_check(
            checks,
            errors,
            limitations,
            "mcm.counted_pages",
            False,
            "counted solution pages could not be established",
            "Summary, solution, references, contents, notes, appendices, and code",
        )
    else:
        add_check(
            checks,
            errors,
            limitations,
            "mcm.counted_pages",
            counted_pages <= profile["max_counted_pages"],
            (
                f"counted solution is {counted_pages} pages; limit is "
                f"{profile['max_counted_pages']}"
            ),
            "all pages before the AI report, or the whole PDF when no AI report exists",
        )

    if ai_start is not None and page_count is not None:
        boundary_ok = 2 <= ai_start <= page_count
        add_check(
            checks,
            errors,
            limitations,
            "mcm.ai_report_boundary",
            boundary_ok,
            (
                "AI report follows the counted solution and is excluded from its page count"
                if boundary_ok
                else "AI report start page is outside the PDF or precedes the solution"
            ),
            "PDF page boundary",
        )

    if control_ok and counted_pages is not None:
        pages_to_check = page_count if page_count is not None else counted_pages
        if page_texts:
            missing = control_header_pages(page_texts, control_number, pages_to_check)
            add_check(
                checks,
                errors,
                limitations,
                "mcm.control_header",
                not missing,
                (
                    "control number and page number appear in every extracted page header"
                    if not missing
                    else f"control/page header evidence missing on PDF pages: {missing}"
                ),
                "first extracted lines on every PDF page, including any AI report",
            )
        elif evidence:
            header_pages = evidence.get("control_header_pages")
            expected = list(range(1, pages_to_check + 1))
            passed = header_pages == expected or header_pages == "all_pages"
            add_check(
                checks,
                errors,
                limitations,
                "mcm.control_header",
                passed,
                (
                    "hash-bound evidence records headers on every PDF page"
                    if passed
                    else "compliance evidence does not cover every PDF page header"
                ),
                "recorded visual evidence",
                limited=passed,
            )
        else:
            add_check(
                checks,
                errors,
                limitations,
                "mcm.control_header",
                False,
                "page-header checks require pdftotext or hash-bound visual evidence",
                "control number and page number at top of every PDF page",
            )

    if require_ai_report and page_texts and ai_start is not None:
        counted_text = "\n".join(page_texts[: ai_start - 1])
        inline_ok = has_ai_inline_disclosure(counted_text)
        reference_ok = has_ai_reference(counted_text)
        add_check(
            checks,
            errors,
            limitations,
            "mcm.ai_inline_disclosure",
            inline_ok,
            (
                "counted solution contains inline AI-use disclosure"
                if inline_ok
                else "counted solution lacks inline AI-use disclosure"
            ),
            "text before the AI report",
        )
    elif require_ai_report and evidence:
        for check_id, key, description in (
            ("mcm.ai_inline_disclosure", "ai_inline_disclosure", "inline AI disclosure"),
            ("mcm.ai_reference", "ai_reference_entry", "AI reference entry"),
        ):
            passed = evidence_bool(evidence, key)
            add_check(
                checks,
                errors,
                limitations,
                check_id,
                passed,
                (
                    f"hash-bound evidence records {description}"
                    if passed
                    else f"compliance evidence does not confirm {description}"
                ),
                "recorded content evidence",
                limited=passed,
            )
    elif require_ai_report:
        for check_id, description in (
            ("mcm.ai_inline_disclosure", "inline AI disclosure"),
            ("mcm.ai_reference", "AI reference entry"),
        ):
            add_check(
                checks,
                errors,
                limitations,
                check_id,
                False,
                f"{description} check requires pdftotext or hash-bound evidence",
                "counted PDF content",
            )
        add_check(
            checks,
            errors,
            limitations,
            "mcm.ai_reference",
            reference_ok,
            (
                "counted solution reference section lists an AI tool"
                if reference_ok
                else "counted solution reference section lacks an AI-tool entry"
            ),
            "text before the AI report",
        )


def verify_submission(
    *,
    paper: Path,
    support: Path | None,
    profile_name: str,
    main_text_pages: int | None = None,
    solution_pages: int | None = None,
    require_ai_report: bool = False,
    max_paper_mb: float | None = None,
    max_support_mb: float | None = None,
    font_size_pt: float | None = None,
    control_number: str | None = None,
    evidence_path: Path | None = None,
) -> dict[str, Any]:
    profile = PROFILES[profile_name]
    paper_limit = (
        max_paper_mb if max_paper_mb is not None else profile["max_paper_mb"]
    )
    support_limit = (
        max_support_mb
        if max_support_mb is not None
        else profile.get("max_support_mb")
    )
    errors: list[str] = []
    warnings: list[str] = []
    limitations: list[str] = []
    checks: list[dict[str, Any]] = []
    artifacts: list[dict[str, Any]] = []
    inspection: PdfInspection | None = None
    evidence: dict[str, Any] = {}

    if not paper.is_file():
        errors.append("paper is missing")
    elif paper.suffix.lower() not in profile["paper_suffixes"]:
        errors.append(f"paper type is not allowed by {profile_name}")
    if paper.is_file():
        size = paper.stat().st_size
        if profile_name in {"mcm-icm", "mcm-icm-current", "mcm-icm-2027"}:
            if size >= paper_limit * 1024 * 1024:
                errors.append(f"paper must be smaller than {paper_limit} MB")
        elif size > paper_limit * 1024 * 1024:
            errors.append(f"paper exceeds {paper_limit} MB")
        if paper.suffix.lower() == ".pdf":
            inspection = inspect_pdf(paper)
        artifacts.append(
            {
                "role": "paper",
                "file": paper.name,
                "source_path": str(paper.resolve()),
                "bytes": size,
                "sha256": sha256(paper),
                "pages": inspection.page_count if inspection else None,
            }
        )
        evidence, evidence_errors = load_evidence(evidence_path, paper)
        errors.extend(evidence_errors)

    if support is not None:
        if profile.get("support_forbidden"):
            pass
        elif not support.is_file():
            errors.append("support is missing")
        elif support.suffix.lower() not in profile["support_suffixes"]:
            errors.append(f"support type is not allowed by {profile_name}")
        else:
            size = support.stat().st_size
            if support_limit is not None and size > support_limit * 1024 * 1024:
                errors.append(f"support exceeds {support_limit} MB")
            artifacts.append(
                {
                    "role": "support",
                    "file": support.name,
                    "source_path": str(support.resolve()),
                    "bytes": size,
                    "sha256": sha256(support),
                    "pages": None,
                }
            )

    snapshot = profile_snapshot(profile)
    if snapshot:
        stale = date.today() > date.fromisoformat(snapshot["valid_through"])
        add_check(
            checks,
            errors,
            limitations,
            "profile.rules_snapshot",
            not stale,
            (
                f"rule profile {snapshot['profile_version']} is current through "
                f"{snapshot['valid_through']}"
                if not stale
                else (
                    f"rule profile expired on {snapshot['valid_through']}; "
                    "refresh official sources before use"
                )
            ),
            "versioned profile parameters and official source URLs",
        )

    if paper.is_file() and paper.suffix.lower() in profile["paper_suffixes"]:
        if profile_name == "cumcm-2026":
            verify_cumcm(
                paper=paper,
                support=support,
                main_text_pages=main_text_pages,
                require_ai_report=require_ai_report,
                inspection=inspection,
                docx_text=extract_docx_text(paper),
                evidence=evidence,
                checks=checks,
                errors=errors,
                warnings=warnings,
                limitations=limitations,
            )
        elif profile_name in {"mcm-icm", "mcm-icm-current", "mcm-icm-2027"}:
            verify_mcm_icm(
                paper=paper,
                support=support,
                solution_pages=solution_pages,
                font_size_pt=font_size_pt,
                control_number=control_number,
                require_ai_report=require_ai_report,
                inspection=inspection,
                evidence=evidence,
                checks=checks,
                errors=errors,
                limitations=limitations,
            )

    status = "FAIL" if errors else ("LIMITED" if limitations else "PASS")
    return {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "profile": profile_name,
        "profile_snapshot": snapshot,
        "status": status,
        "scope": (
            "artifact type/size/hash plus profile checks listed in checks; "
            "LIMITED identifies checks supported only by recorded evidence or "
            "blocked by unavailable tools"
        ),
        "errors": errors,
        "limitations": limitations,
        "warnings": warnings,
        "checks": checks,
        "tools": inspection.tools if inspection else {},
        "artifacts": artifacts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper", type=Path, required=True)
    parser.add_argument("--support", type=Path)
    parser.add_argument("--profile", choices=sorted(PROFILES), default="generic")
    parser.add_argument("--main-text-pages", type=int)
    parser.add_argument("--solution-pages", type=int)
    parser.add_argument("--require-ai-report", action="store_true")
    parser.add_argument("--max-paper-mb", type=float)
    parser.add_argument("--max-support-mb", type=float)
    parser.add_argument("--font-size-pt", type=float)
    parser.add_argument("--control-number")
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    payload = verify_submission(
        paper=args.paper,
        support=args.support,
        profile_name=args.profile,
        main_text_pages=args.main_text_pages,
        solution_pages=args.solution_pages,
        require_ai_report=args.require_ai_report,
        max_paper_mb=args.max_paper_mb,
        max_support_mb=args.max_support_mb,
        font_size_pt=args.font_size_pt,
        control_number=args.control_number,
        evidence_path=args.evidence,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(payload["status"])
    if payload["status"] == "PASS":
        return 0
    return 1 if payload["status"] == "FAIL" else 2


if __name__ == "__main__":
    raise SystemExit(main())
