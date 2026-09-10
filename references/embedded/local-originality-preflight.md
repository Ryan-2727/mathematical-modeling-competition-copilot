# Local originality preflight

This gate compares the complete local LaTeX manuscript with a user-supplied
historical-paper corpus. It is a text-only, offline review aid: it uploads no
contest material and creates no images. It is not an official
Tongfang/CNKI plagiarism check or a prediction of either official percentage.

## Configure the corpus

CUMCM 2026 initialization creates `reports/originality_config.json`:

```json
{
  "schema_version": 1,
  "enabled": true,
  "main_tex": "paper/main.tex",
  "corpus_dirs": ["F:/path/to/local/historical-papers"],
  "historical_corpus_confirmed": true
}
```

Use only a historical corpus that the team is authorized to inspect locally.
`historical_corpus_confirmed` records the human confirmation that the folder
does not contain the current live problem or another team's live work. The
corpus must remain outside the contest project. Supported files are `.pdf`,
`.tex`, `.md`, and `.txt`. PDF text extraction uses an already-installed
`pdftotext` or `pypdf`; OCR, screenshots, network calls, and dependency
downloads are prohibited. Unreadable or image-only PDFs are listed as
uncovered corpus and make the result `LIMITED`.

## Run

From the skill repository:

```bash
python scripts/originality_preflight.py \
  --project-dir <project> \
  --config <project>/reports/originality_config.json \
  --out-json <project>/reports/originality_preflight.json \
  --out-md <project>/reports/originality_preflight.md
```

For a one-off training scan, repeat `--corpus-dir <folder>` for each corpus and
add `--historical-corpus-confirmed`. Once the CUMCM configuration is enabled and
contains a corpus directory, `contestctl.py run --phase paper --profile
standard` and the strict freeze graph run this node automatically.

The scanner recursively expands `\input` and `\include` from `paper/main.tex`,
rejects cycles and paths outside the project, and preserves the source file and
line range. It excludes comments, displayed formulas, code/verbatim,
bibliography blocks, generated result files, and the AI declaration. Narrative
captions and table prose remain eligible for review.

## Read and resolve the report

Open `reports/originality_preflight.md` before freezing. Every HIGH or MEDIUM
item provides:

- exact draft file and line range;
- the full draft paragraph that needs human review;
- historical source file plus PDF page or text-line range;
- a short source excerpt and the exact-run, character-bigram Jaccard, and
  matched-coverage signals;
- a remediation direction: add the true citation, remove generic boilerplate,
  or rewrite the reasoning from the team's own model choice, parameter source,
  computation, validation, and boundary evidence.

The tool deliberately does not generate replacement prose, synonym swaps, or
detector-evasion text. A team member must inspect the source and edit the paper.
Then copy each finding's ID and paragraph SHA-256 into
`reports/originality_review.csv` and choose exactly one disposition:

```csv
finding_id,draft_sha256,disposition,reason,reviewer,status
..., ...,resolved,rewritten from executed team evidence,student-2,complete
..., ...,accepted_with_citation,quotation or close idea now cited precisely,student-2,complete
..., ...,false_positive,shared technical term only,student-2,complete
```

Accepted rows require a reason, named human reviewer, and `complete` status.
Any paragraph edit changes its hash and makes the previous review stale; rerun
the scan after every revision.

## Status and thresholds

- `FAIL`: invalid or unsafe input, malformed review/configuration, or no draft
  prose.
- `LIMITED`: missing or unreadable corpus coverage.
- `REVIEW`: unresolved HIGH/MEDIUM findings.
- `PASS`: adequate local coverage and every finding has a current human review.

HIGH is triggered by an exact normalized run of at least 24 characters,
character-bigram Jaccard at least 0.65 on comparable paragraphs, or at least
35% matched coverage across multiple windows. MEDIUM uses a 12--23 character
run, Jaccard at least 0.45, or at least 20% coverage. These are paragraph-level
heuristics for prioritizing manual review, not whole-paper similarity rates.

For CUMCM 2026, the final, separate official gate remains
`scripts/verify_similarity_risk.py`, populated only from the actual two-metric
Tongfang/CNKI report. A local `PASS` can never satisfy or replace that gate.
