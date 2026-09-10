# Local Originality Preflight Implementation Plan

## Goal

Deliver a local-only, text-only originality preflight that resolves a complete
multi-file LaTeX paper, scans private historical PDF/text corpora, locates exact
and near-duplicate paragraphs, and requires hash-bound human disposition before
paper freeze. Preserve the separate official similarity gate.

## Task 1: Establish executable contracts

Add focused tests for:

- recursive `\input`/`\include` resolution with line locations;
- include cycle and project-root escape rejection;
- exact, near-duplicate, reordered-fragment, and unrelated-prose fixtures;
- complete draft paragraph and bounded corpus excerpt in Markdown/JSON;
- stale versus current human-review dispositions;
- missing/unreadable corpus behavior and absence of image outputs; and
- live-mode historical-corpus confirmation.

Verify: new tests fail for missing implementation while existing legacy
similarity tests remain green.

## Task 2: Implement the local scanner

Create `scripts/originality_preflight.py` with isolated units for:

- safe LaTeX dependency traversal and source mapping;
- prose normalization and exclusions;
- text and PDF corpus extraction with local fallbacks;
- character n-gram candidate indexing;
- exact-run, Jaccard, matched-coverage, and risk calculation;
- review-ledger validation; and
- deterministic JSON/Markdown rendering.

Verify: focused tests pass, CLI exit/status semantics match the design, and no
network or image-generation path exists.

## Task 3: Integrate without breaking other contests

- Scaffold CUMCM 2026 `originality_config.json` and
  `originality_review.csv` only.
- Register a CUMCM-specific originality node in standard/strict paper workflow;
  do not add it to MCM/ICM.
- Keep `similarity_preflight.py` behavior compatible.
- Add the script and reference tokens to the Skill contract.

Verify: CUMCM workflow includes the node, MCM/ICM excludes it, and initializer
tests prove profile-specific files.

## Task 4: Update concise instructions

Update `SKILL.md`, bilingual README files, workflow map, CUMCM readiness, and
evidence-quality guidance. Require the agent to show the Markdown high-risk
list to the user before freeze and wait for human disposition. State that local
results are not an official percentage and that no automatic replacement prose
is generated.

Verify: contract checks find the new command and wording without expanding
`SKILL.md` beyond 500 lines.

## Task 5: Release verification and local sync

Run:

- focused originality tests;
- all repository unit tests;
- Python compile checks;
- JSON and Skill contract validation;
- Skill Creator `quick_validate.py`;
- `git diff --check`; and
- local Skill synchronization plus hash verification.

Commit implementation only after all checks pass. Do not push to GitHub unless
the user separately requests it.
