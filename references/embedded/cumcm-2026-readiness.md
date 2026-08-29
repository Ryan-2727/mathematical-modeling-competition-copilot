# CUMCM 2026 live operations and readiness

Use this reference only for CUMCM 2026 after `cumcm-2026-rules.md` and the local
rules lock have been verified.

## Contents

- [Local-only online boundary](#local-only-online-boundary)
- [Six-hour problem audition](#six-hour-problem-audition)
- [Exact 74-hour schedule](#exact-74-hour-schedule)
- [Timed training readiness](#timed-training-readiness)

## Local-only online boundary

Keep the current statement, attachments, data, screenshots, solution ideas,
code, results, paper fragments, and summaries on the local machine. Do not use
this skill to upload them to a website, repository, cloud drive, online compiler,
online execution service, or external AI service. The team performs the final
official submission manually after local verification.

Generic research on official, scholarly, and static-reference sources is
permitted. During the live contest, do not browse, read, open a search result,
post, upload, or discuss current-problem content on a communication platform,
including repositories, forums, Q&A sites, group chats, social blogs, and live
streams. Do not impose a lexical restriction on search terms. Record content
relation, destination category, planned/completed action, and classification
evidence in `reports/online_actions.csv`, then run
`scripts/verify_online_actions.py`. If either classification is uncertain,
pause and ask the user; continue only after recording the reply. The reply
cannot override an action already known to violate the official rule. This is a
declaration audit, not an operating-system network interceptor.

## Six-hour problem audition

Compare all A/B/C problems with the same staged budget. This engine evaluates
the current AI/Codex capability only; it never substitutes a guessed student-team
score.

| Window | Required evidence |
| --- | --- |
| H0-H0.75 | Screen A, B, and C for 15 minutes each: structure, attachments, semantics, outputs, and required model families |
| H0.75-H2.25 | Give each problem a 30-minute executable micro-baseline; preserve a result or typed failure and diagnostic |
| H2.25 | Rank all three and mark one as eliminated; do not erase its evidence |
| H2.25-H5.25 | Give the top two equal 90-minute deep-trial budgets, including validation, a paper-grade figure, and fallback |
| H5.25-H6 | Generate the hash-bound recommendation, show it to the user, record their declaration, and verify the lock |

Fill `reports/problem_screening.csv` and one 0--4 evidence rating for each of the
seven criteria in `reports/problem_selection_evidence.csv`: closure/results,
verifiability, current AI fit, data semantics, compute/fallback, paper/figures,
and innovation. `unknown` is different from zero and needs a local diagnostic
locator just like any other rating. Every locator must be project-relative and
match its recorded SHA-256. Continue to fill `reports/problem_audition.csv` with
commands, executable outputs, figures, closure evidence, fallback, fatal risk,
and legacy sensitivity fields. In schema 3 those legacy weights remain diagnostic
only: `team_fit` cannot overrule the AI-only recommendation or create an exception
requirement. Record the H2.25 preliminary score and elimination reason, plus the
top two actual deep-trial times; zero, under-80%, over-120%, or materially unequal
times require a documented timing exception and cap confidence.
Use capability IDs from `assets/problem-selection/ai-capability-profile.json`
(for example `statistics`, `forecasting`, `optimization`, `simulation`,
`differential_equations`, and `graph_network`); an unmatched family remains an
explicit unknown rather than receiving a favorable prior.

The AI-fit criterion is computed from 30% bundled task-family prior and 70%
same-day executable evidence. First create a fresh local capability snapshot;
the standard/strict selection graph runs the kernel regression automatically:

```bash
python scripts/contestctl.py run --project-dir <project> --phase selection --profile standard
```

Inspect both `reports/problem_selection_recommendation.json` and the Chinese
`reports/problem_selection_recommendation.md`. The report lists each problem's
model-family fit, evidence-backed advantages, disadvantages, risks, fallback,
scenario rank, worst rank, margin, and confidence. A margin below three points,
weight instability, or unresolved prior/live conflict produces co-leaders rather
than a false winner. Unfair timing caps the result at `LIMITED`; an unresolved
fatal risk prevents a default recommendation.

Award probabilities are optional. `reports/public_award_prior.json` must bind a
saved, reviewed public source retrieved within 366 days and uses an effective
prior strength no greater than 10. Declare the covered population, denominator,
and four outcomes as mutually exclusive highest-award labels; incompatible
definitions suppress calibration. Private historical rows stay only in
`reports/problem_selection_calibration.csv`; its minimized schema excludes
statements, attachment values, prose, outputs, and paths. Percentages appear only
with a valid same-day capability snapshot, a verified applicable public prior,
at least three years, and effective local sample size at least 12. Otherwise the
report says `INSUFFICIENT_EVIDENCE` and prints no personalized percentages.
Internet search for public statistics follows the online-action ledger and must
never upload private calibration or current contest artifacts.

After showing the report, record the user's declared decision (this is an audit
record, not identity authentication):

```bash
python scripts/record_problem_selection_confirmation.py \
  --project-dir <project> --selected-problem A --selection-hour 5.8 \
  --rationale "evidence-backed reason"
python scripts/verify_problem_audition.py \
  --project-dir <project> --out <project>/reports/problem_audition_verification.json
```

The final verifier rejects a missing confirmation, changed recommendation hash,
different selected/confirmed problem, stale screening/audition/capability/prior/
calibration evidence, or confirmation recorded before recommendation generation.
A user-confirmed non-recommended problem remains possible only through the
existing evidence-backed `selection_exception`. Lock the selected problem by H6.
After H6, change it only for documented catastrophic infeasibility with local
evidence and team authorization. The validator verifies the evidence process; it
does not choose the problem.

## Exact 74-hour schedule

| Hours | Required outcome |
| --- | --- |
| H0-H2 | Verify local rule snapshots, roles, deliverables, and candidate criteria |
| H2-H6 | Execute comparable candidate baselines and lock the problem |
| H6-H24 | Give every subproblem a runnable baseline and provisional result |
| H24-H42 | Freeze the primary and competing models after validation and refutation |
| H42-H54 | Finish uncertainty, stress tests, core figures, and tables |
| H54-H64 | Complete the paper and support-material draft |
| H64-H70 | Run independent review, numerical traceability, and strict checks |
| H70-H73 | Finish local anonymity, AI evidence, packaging, hashes, and strict checks |
| H73-H74 | Freeze artifacts, compute and submit the final MD5 before 20:00, then verify the actual frozen bytes against the official-client MD5 evidence; make no later content edits |
| H74-H74.5 | Preserve the official half-hour gap; do not attempt an early upload |
| H74.5-H92 | The team performs the official upload and records receipt evidence before 2026-09-14 14:00 |

Stop losses:

- no runnable baseline by H12: simplify the abstraction;
- any subproblem without a result by H24: remove noncritical factors only after
  user authorization and preserve the stronger unexecuted route as model
  optimization;
- an enhancement without measured advantage by H42: reject it or narrow its
  claim;
- after H54: introduce no new model family unless repairing a veto;
- never consume H73-H74 for cosmetic revisions or alter an artifact after its
  final MD5 is submitted.

At hash lock, fill `reports/submission_md5_lock.json` and run
`scripts/verify_submission_md5_lock.py`. A local SHA-256 manifest or a recorded
deadline is not MD5 evidence. Any later save invalidates the lock and requires a
new official MD5 cycle before the deadline.

## Timed training readiness

Use unseen historical statements without solution papers in the solving context.
Run 8-hour selection/baseline, 24-hour result, 48-hour paper, and full 74-hour
rehearsals. Only after freezing the independent output may excellent papers be
used to extract general lessons.

Record runs in `reports/training_runs.csv` and evidence-located defects in
`reports/training_defects.csv`. Record selection, modeling, paper, and submission
role owners, distinct backups, planned/actual completion, and handoff evidence in
`reports/training_roles.csv`. Run `scripts/score_training_readiness.py` after
each rehearsal. Review median, nearest-rank P90, worst case, latest-three-run
trend, deadline margin, defect recurrence, and defects reopened after a prior
resolution, plus role/owner delay bottlenecks. A stable readiness pass requires
the latest two 74-hour rehearsals
to pass, including submission rehearsals, with no unresolved critical defect.
One passing full rehearsal is provisional evidence. Partial runs and these
metrics are training evidence, not an award prediction.
