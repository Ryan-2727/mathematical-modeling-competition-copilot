# Local Originality Preflight Design

## Objective

Upgrade the current single-file exact-phrase advisory into a complete, local,
evidence-located originality preflight for a multi-file LaTeX contest paper and
a private historical-paper corpus. The report must tell the user exactly which
draft paragraphs need human attention, why they were flagged, and where the
closest corpus match came from.

This feature reduces accidental copying and formulaic reuse. It must not claim
to reproduce Tongfang/CNKI, predict an official percentage, or generate evasive
paraphrases.

## Chosen Approach

Use a deterministic local hybrid detector:

1. exact normalized phrase matching;
2. character n-gram near-duplicate matching; and
3. target-paragraph matched-coverage measurement.

This provides useful recall without downloading an embedding model or sending
the paper and corpus to a service. Keep the official two-metric verifier as an
independent final gate.

Rejected alternatives:

- Extending exact phrases alone remains blind to small insertions, deletions,
  and sentence reordering.
- A local embedding model adds downloads, runtime variance, opaque thresholds,
  and semantic false positives immediately before the contest.
- An online checker would violate the local-only material boundary unless the
  user separately authorizes a permitted official workflow.

## Inputs and Safety Boundary

Add `scripts/originality_preflight.py` with these primary inputs:

- `--project-dir`: the contest project root;
- `--main-tex`: optional, default `paper/main.tex`;
- one or more `--corpus-dir`: private local historical-paper directories;
- `--out-json`: machine-readable report under project `reports/`; and
- `--out-md`: human-readable report under project `reports/`.

Corpus formats are `.pdf`, `.tex`, `.md`, and `.txt`. The scanner is read-only:
it must not copy corpus files into the project, modify the draft, use network
access, or generate images. A live-contest run requires a recorded declaration
that the corpus is historical and contains no current-problem discussion or
current contestant work.

## Complete LaTeX Draft Resolution

Resolve the paper from `main.tex`, following `\input` and `\include`
recursively while retaining source-file and line mappings. Add `.tex` when the
extension is omitted. Reject path escape, include cycles, unreadable files, and
missing required sections.

Normalize prose for matching while preserving the original paragraph for the
user report:

- remove comments and non-prose LaTeX control syntax;
- exclude displayed equations, code listings, bibliography entries, generated
  value files, and official fixed declarations from scored prose;
- retain section prose, captions, footnotes, and table-cell narrative;
- normalize whitespace and punctuation without deleting Chinese characters,
  Latin letters, or digits; and
- discard fragments too short to support a meaningful comparison.

The report must identify excluded and unreadable sources so an incomplete scan
cannot silently return `PASS`.

## Historical Corpus Extraction

For text formats, preserve file and line ranges. For PDF files, prefer the local
`pdftotext` executable and split its output on page boundaries. If unavailable,
use an already-installed local Python PDF text extractor. Do not download a
runtime during a scan. A PDF with insufficient extractable text is listed as an
unreadable coverage gap; OCR is not performed and no page image is created.

Cache only normalized derived text and source hashes under project `reports/`
when explicitly enabled. Never copy the original PDF corpus into the project or
official submission package.

## Matching and Risk Classification

Index normalized corpus paragraphs by character n-grams to avoid comparing
every paragraph pair. For each eligible draft paragraph, calculate:

- longest exact normalized run;
- count and locations of shared exact windows;
- character n-gram Jaccard similarity;
- proportion of draft characters covered by matched windows; and
- closest source file, page or line range, and a short source excerpt.

Use conservative defaults stored in the script and printed in the report:

- `HIGH`: an exact normalized run of at least 24 characters, or near-duplicate
  similarity at least 0.65 with at least 40 comparable characters, or matched
  coverage at least 0.35 with more than one independent matching window;
- `MEDIUM`: an exact run of 12--23 characters, near-duplicate similarity at
  least 0.45 with at least 40 characters, or matched coverage at least 0.20;
- `LOW`: a weaker candidate retained only for optional inspection; and
- unscored: short, formula-only, or approved fixed text.

These are local review heuristics, not percentages of the full paper and not
official plagiarism thresholds. Thresholds may be exposed as CLI options for
testing, but the report must always record their actual values.

## User-Facing Findings

Write both JSON and Markdown. The Markdown report contains no figures or image
links. Sort findings by `HIGH`, then `MEDIUM`, then source order. For every high
or medium finding show:

- risk level and detector signals;
- draft source path and exact line range;
- the complete user-owned draft paragraph;
- closest corpus file and PDF page or text line range;
- only the shortest source excerpt needed to verify the match;
- matched spans or coverage explanation; and
- a remediation category.

Permitted remediation categories are:

- add or correct a citation for a genuinely sourced claim;
- replace generic model exposition with the team's problem-specific mechanism,
  model-choice evidence, parameter provenance, computation, and validation;
- shorten or remove boilerplate that adds no argument;
- quote a necessary short passage according to the contest's citation rules; or
- remove a claim that the team cannot independently support.

The tool must not output a replacement paragraph, synonym substitution, or any
instruction intended to evade a detector. `HIGH` and `MEDIUM` findings remain
pending until a named team reviewer records `resolved`, `accepted_with_citation`,
or `false_positive` with a reason in `reports/originality_review.csv`.

## Status Semantics

- `FAIL`: invalid paths, unsafe LaTeX includes, malformed configuration, or no
  readable draft prose.
- `LIMITED`: material corpus files could not be read or corpus coverage is empty.
- `REVIEW`: at least one unresolved `HIGH` or `MEDIUM` finding exists.
- `PASS`: all configured corpus files were adequately processed and every high
  or medium finding has a current, hash-bound human disposition.

A local `PASS` does not satisfy the official similarity gate. After the final
PDF is frozen, `scripts/verify_similarity_risk.py` still requires the actual
two official metrics and the matching paper hash.

## Workflow Integration and Compatibility

- Keep `scripts/similarity_preflight.py` as a compatibility entry point for its
  current arguments and output; route new project-level use to
  `scripts/originality_preflight.py`.
- Add `reports/originality_config.json` and
  `reports/originality_review.csv` for CUMCM 2026 initialization.
- Add the preflight to the CUMCM 2026 paper/freeze guidance workflow only when a
  corpus is configured. An empty corpus produces `LIMITED`, not a false pass.
- Require the Skill to display the Markdown high-risk list to the user before
  paper freeze and wait for human edits or dispositions.
- Keep detailed instructions in the originality/evidence reference; add only a
  concise routing rule to `SKILL.md` and bilingual README descriptions.

Recommended command:

```powershell
python scripts/originality_preflight.py `
  --project-dir "<project>" `
  --corpus-dir "F:\数学建模国赛\高教社杯全国大学生数学建模竞赛优秀论文" `
  --out-json "<project>\reports\originality_preflight.json" `
  --out-md "<project>\reports\originality_preflight.md"
```

## Testing

Use test-first implementation with fixtures that prove:

1. nested `\input` and `\include` files produce correct path and line locators;
2. include cycles and project-path escape fail safely;
3. exact copies, small edits, reordered fragments, and high coverage are found;
4. unrelated technical prose and approved fixed text do not create high-risk
   false positives;
5. PDF page boundaries are retained when `pdftotext` is available;
6. an unreadable or image-only PDF makes the result `LIMITED` without creating
   an image;
7. Markdown lists the complete draft paragraph but only a short corpus excerpt;
8. no finding contains an automatic replacement paragraph;
9. stale review dispositions fail after the draft paragraph changes;
10. legacy `similarity_preflight.py` behavior remains compatible;
11. local and official similarity reports remain separate; and
12. all existing unit, Skill contract, and local-installation checks pass.

## Success Criteria

- A multi-file LaTeX paper is scanned as one complete, source-mapped draft.
- Private historical PDFs and text sources are processed entirely locally.
- The user receives a direct, text-only list of high-risk paragraphs and source
  locators before freeze.
- Near-duplicate risk is detected without inventing an official percentage.
- Human review is mandatory, traceable, and invalidated by later edits.
- The final official two-metric, hash-bound gate remains authoritative.

## Non-Goals

- Reproducing, bypassing, or reverse-engineering Tongfang/CNKI.
- Guaranteeing a zero similarity score or an award.
- Automatically rewriting flagged prose.
- Scanning current-problem discussions or solution material during the live
  contest.
- OCR, screenshots, charts, or any other image output.
