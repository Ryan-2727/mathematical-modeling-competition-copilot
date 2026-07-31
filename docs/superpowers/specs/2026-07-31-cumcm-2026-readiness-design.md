# CUMCM 2026 Readiness Upgrade Design

## Goal

Upgrade the existing mathematical-modeling competition skill for the September
2026 CUMCM without removing current capabilities. The change covers four
selected areas: a current-rule lock, two-branch AI compliance, a six-hour
problem audition, and timed training/readiness tracking.

The skill remains explicit-invocation-only. This upgrade changes its source and
validators; it does not make the skill trigger automatically.

## Scope and safety boundary

Use a hybrid rules workflow. Before the live contest, official rule pages and
PDFs may be checked online and saved as local, hash-bound snapshots. During the
contest, the locked local snapshots are authoritative unless the user explicitly
authorizes a refresh.

All current-contest statements, attachments, data, screenshots, solution ideas,
code, results, paper fragments, and summaries remain local. Do not upload them
to websites, repositories, cloud drives, online compilers, online execution
services, or external AI services. Internet searching is allowed. Do not impose
a lexical ban on search terms. If it is unclear whether a proposed online action
would disclose contest material, pause and ask the user; continue only after the
user replies.

This safety boundary is represented in the workflow instructions and in a local
network-action audit contract. The scripts validate declared actions and local
evidence; they do not claim to intercept every external application or network
request on the operating system.

## Architecture

Extend existing components instead of adding another orchestration layer:

1. Extend `lock_contest_rules.py` and the CUMCM 2026 reference with exact 2026
   dates, official sources, freshness checkpoints, and local snapshot evidence.
2. Extend `verify_submission.py` with a required mutually exclusive
   `ai_mode=none|used` contract. The `none` branch checks the exact non-use
   declaration after the references. The `used` branch preserves the existing
   inline disclosure, bibliography, and `AI工具使用详情.pdf` checks.
3. Add one small local validator for the six-hour problem audition. It checks
   that every candidate has comparable execution evidence and that the selected
   problem is locked by H6 or has a documented catastrophic override.
4. Add one small readiness scorer for timed rehearsals. It aggregates local
   milestone evidence and repeated defect classes without reading exemplar
   solutions into the solving context.
5. Integrate these gates into `init_contest.py`, the strict workflow references,
   contract validation, tests, and bilingual README files. Compress repeated
   wording in `SKILL.md` when necessary, while preserving every existing
   requirement.

## Component contracts

### 1. CUMCM 2026 rule lock

The 2026 profile records the official notice, format rule, contest rule, and AI
policy URLs; competition start and end times; registration deadline; timezone;
submission channel; access time; snapshot path; SHA-256; and profile version.

Freshness checkpoints are T-30, T-7, and T-1 relative to contest start. A
pre-contest check may refresh official sources online. A live-mode check uses
local snapshots by default and reports a stale or missing lock as a failure. A
manual refresh requires explicit user authorization and produces a new hash
record rather than silently replacing evidence.

### 2. AI compliance branches

`ai_mode` is mandatory for CUMCM 2026 and has exactly two values:

- `none`: require the official non-use statement after the references and reject
  an AI-use detail report or contradictory AI-use evidence.
- `used`: require inline disclosures, an AI-tool bibliography entry, and
  `AI工具使用详情.pdf` in the support archive; reject the non-use declaration.

The submission report records which branch was checked and the evidence used.
The gate detects contradictions rather than guessing a mode from paper text.

### 3. Six-hour problem audition

Create `reports/problem_audition.csv` with one row per candidate problem. Required
evidence includes attachment parsing, runnable baseline command and result,
subproblem closure risk, result verifiability, model-upgrade headroom, team fit,
writing/visual potential, fatal risk, score, and status. Create
`reports/problem_selection.json` with the selected problem, selection time,
evidence-based rationale, and any override.

The validator fails when candidates are scored without executable evidence, the
selected candidate is not represented, selection occurs after H6 without a
catastrophic-infeasibility override, or scoring fields are incomplete. The gate
does not choose the problem for the team; it verifies the decision process.

### 4. Timed training and readiness

Create `reports/training_runs.csv` with one row per rehearsal and
`reports/training_defects.csv` with evidence-located defect observations. Support
8-hour, 24-hour, 48-hour, and 74-hour rehearsal types. Track at least selection
lock time, first verified result, all-subproblem result time, full-draft time,
strict-freeze time, submission rehearsal, unresolved vetoes, and repeated defect
classes.

The readiness scorer produces a local JSON report with milestone pass rates,
median completion times, repeated defects, trend direction, and readiness state.
It never predicts an award. A full-readiness pass requires a successful 74-hour
rehearsal and no unresolved critical defect; shorter rehearsals provide partial
evidence only.

## Workflow and error handling

At contest initialization, scaffold the new local evidence files without
overwriting existing work. During training, run the audition validator at H6 and
the readiness scorer after each rehearsal. During a live CUMCM 2026 project,
load the fresh local rules lock, verify the selected AI branch, and preserve the
network-action decision log.

Missing evidence is `FAIL`; environmental limitations that prevent a meaningful
machine check are `LIMITED` only when a manual evidence path is recorded. A
privacy-ambiguous online action is not auto-approved or auto-denied: it pauses
for the user's answer.

## Verification

Add unit tests for:

- exact 2026 schedule and freshness checkpoint behavior;
- stale/missing/changed rule snapshots;
- both valid AI branches and contradiction failures;
- six-hour audition completeness, H6 lock, and documented override;
- partial versus full rehearsal readiness and repeated-defect aggregation;
- preservation of explicit-invocation-only metadata and existing contracts.

Run the full test suite, skill contract validation, and a clean-tree diff review.
Synchronize installed local copies only after all checks pass. GitHub publication
is outside this change unless separately requested.
