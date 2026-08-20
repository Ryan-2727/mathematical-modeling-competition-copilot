# Executable contest profiles

Use `scripts/verify_submission.py` only after selecting the contest and checking
the official rule pages again. The script records hashes and enforces the rules
that can be supported by artifact text, archive members, declared counts, or
hash-bound review evidence. It does not replace final visual inspection.

## Contents

- [Status contract](#status-contract)
- [CUMCM 2026](#cumcm-2026)
- [MCM/ICM 2027](#mcmicm-2027)
- [Hash-bound fallback evidence](#hash-bound-fallback-evidence)

## Status contract

- `PASS`: every applicable automated check passed.
- `LIMITED`: no check failed, but at least one result relies on hash-bound human
  evidence because a required extractor was unavailable.
- `FAIL`: an artifact violates a rule, evidence is stale, or a mandatory check
  cannot be established.

The JSON report lists each check, its scope, tool availability, warnings,
limitations, file hashes, and the SHA-256 digest of the active profile
parameters. A profile expires at `valid_through`; refresh its official URLs and
parameters before using it after that date.

## CUMCM 2026

Snapshot verified 2026-08-20:

Executable values come from `assets/contest-profiles/cumcm-2026.json` through
`scripts/contest_profile.py`; this section explains the profile and is checked
for parity rather than acting as another executable source.

- [First 2026 notice](https://www.mcm.edu.cn/html_cn/node/d6fd7a0ee8f3a3d525e30af1c365fcec.html)
- [Paper format rules](https://www.mcm.edu.cn/html_cn/node/4cd596519c9eb9fbd866398f6df0caa3.html)
- [Contest rules](https://www.mcm.edu.cn/html_cn/node/9d8e511fe7a1447b35f53a82c908e2e0.html)
- [AI tool rules](https://www.mcm.edu.cn/html_cn/node/fef94648f2836ab6cc81586f4c38512b.html)
- [Official rules index and source locator](https://www.mcm.edu.cn/html_cn/block/44e92058f537729c6b6a62a3662ee417.html)

The `cumcm-2026` profile preserves PDF/Word paper and ZIP/RAR support-package
handling, both 20 MB limits, and the declared 30-page main-text count. For a
text-extractable PDF or DOCX it also checks:

- competition window 2026-09-10 18:00 through 2026-09-13 20:00;
- final MD5 deadline 2026-09-13 20:00;
- upload window 2026-09-13 20:30 through 2026-09-14 14:00;

- the first PDF page has an abstract marker;
- no table-of-contents heading is present;
- the appendix contains a support-file list or no-support declaration;
- the appendix contains complete-code evidence or a no-program declaration;
- exactly one AI branch is selected and its exact 2026 declaration appears
  before the references: `none` verifies the official non-use declaration;
  `used` verifies a non-empty purpose in the use declaration and
  `AI工具使用详情.pdf` in the support ZIP.

Example:

```powershell
python scripts/verify_submission.py `
  --profile cumcm-2026 `
  --paper paper/main.pdf `
  --support support.zip `
  --main-text-pages 30 `
  --ai-mode used `
  --out reports/submission_manifest.json
```

Use `--ai-mode none` when no AI tool was used.

Legacy Word documents remain allowed. If their page layout or text cannot be
parsed, the report names the uninspected scope and requires visual review.
Supplying a valid DOCX enables XML text checks; invalid placeholder files do not
become evidence.

## MCM/ICM 2027

Snapshot verified 2026-07-24:

- [Contest instructions](https://contest.comap.com/undergraduate/contests/mcm/instructions.php)
- [AI policy](https://www.contest.comap.com/undergraduate/contests/mcm/flyer/Contest_AI_Policy.pdf)

The official instructions identify the contest as January 28--February 1, 2027
and list the 25-page rule under the 2027 changes. The versioned profile therefore
expires at the February 1, 2027 contest close and must be refreshed afterward.

Use `mcm-icm-current` or its versioned alias `mcm-icm-2027`. The legacy
`mcm-icm` name remains a compatibility alias. Do not use a prior-year alias for
the current rules. The profile enforces:

- one PDF smaller than 25 MB and no additional support package;
- a Summary Sheet on PDF page 1;
- a declared readable body font of at least 12 pt;
- a seven-digit control number used as the PDF filename;
- control number and page number evidence on every PDF page, including the AI
  report when present;
- at most 25 counted pages, including Summary Sheet, solution, contents,
  references, notes, appendices, code, and problem-specific requirements;
- when AI was used, an inline disclosure and AI reference inside the counted
  solution, followed by `Report on Use of AI Tools`;
- AI-report pages begin after the counted solution and are excluded from the
  25-page count.

Example:

```powershell
python scripts/verify_submission.py `
  --profile mcm-icm-current `
  --paper 1234567.pdf `
  --font-size-pt 12 `
  --control-number 1234567 `
  --require-ai-report `
  --out reports/submission_manifest.json
```

`pdfinfo` supplies the physical page count. `pdftotext -layout` supplies
first-page, header, AI-boundary, and content evidence. A supplied
`--solution-pages` value is cross-checked against the PDF and AI boundary rather
than trusted silently.

## Hash-bound fallback evidence

Use `--evidence reports/submission_visual_evidence.json` only when an extractor
cannot establish a visual requirement. The JSON object must contain
`paper_sha256`, `reviewer`, and `recorded_at`. Its hash must match the submitted
paper. Relevant optional fields are:

```json
{
  "paper_sha256": "<sha256>",
  "reviewer": "team visual inspection",
  "recorded_at": "2026-07-24T20:00:00+08:00",
  "first_page_abstract": true,
  "toc_absent": true,
  "appendix_support_manifest": true,
  "appendix_code_or_no_program": true,
  "ai_use_declaration_before_references": true,
  "ai_non_use_declaration_before_references": true,
  "summary_sheet_first": true,
  "font_size_pt": 12,
  "pdf_pages": 26,
  "control_header_pages": "all_pages",
  "ai_report_start_page": 26
}
```

A check satisfied only this way is `LIMITED`, not `PASS`. Missing `pdfinfo` is a
`FAIL` for MCM/ICM page counting unless `pdf_pages` is supplied. Missing
`pdftotext` is a `FAIL` for mandatory text/header checks unless the matching
hash-bound fields are supplied.
