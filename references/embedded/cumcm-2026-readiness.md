# CUMCM 2026 live operations and readiness

Use this reference only for CUMCM 2026 after `cumcm-2026-rules.md` and the local
rules lock have been verified.

## Local-only online boundary

Keep the current statement, attachments, data, screenshots, solution ideas,
code, results, paper fragments, and summaries on the local machine. Do not use
this skill to upload them to a website, repository, cloud drive, online compiler,
online execution service, or external AI service. The team performs the final
official submission manually after local verification.

Internet searching is allowed. Do not impose a lexical restriction on search
terms. Record planned and completed online actions in
`reports/online_actions.csv` and run `scripts/verify_online_actions.py`. If it is
unclear whether an online action would disclose contest material, pause and ask
the user. Continue only after recording the reply. This is a declaration audit,
not an operating-system network interceptor.

## Six-hour problem audition

Before H6, run a small executable baseline for each serious candidate. Record:

- attachment parsing status and local evidence;
- baseline command and result artifact;
- subproblem closure risk and result verifiability;
- model-upgrade headroom and team fit;
- writing and visual potential;
- fatal risk and comparable score.

Complete `reports/problem_audition.csv` and `reports/problem_selection.json`,
then run `scripts/verify_problem_audition.py`. Lock the selected problem by H6.
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
| H70-H72 | Rehearse packaging, hashes, AI branch, anonymity, and submission steps |
| H72-H74 | Preserve buffer; the team performs official upload and verifies receipt |

Stop losses:

- no runnable baseline by H12: simplify the abstraction;
- any subproblem without a result by H24: remove noncritical factors only after
  user authorization and preserve the stronger unexecuted route as model
  optimization;
- an enhancement without measured advantage by H42: reject it or narrow its
  claim;
- after H54: introduce no new model family unless repairing a veto;
- never consume H72-H74 for cosmetic revisions.

## Timed training readiness

Use unseen historical statements without solution papers in the solving context.
Run 8-hour selection/baseline, 24-hour result, 48-hour paper, and full 74-hour
rehearsals. Only after freezing the independent output may excellent papers be
used to extract general lessons.

Record runs in `reports/training_runs.csv` and evidence-located defects in
`reports/training_defects.csv`. Run `scripts/score_training_readiness.py` after
each rehearsal. A full readiness pass requires a successful 74-hour rehearsal,
a submission rehearsal, and no unresolved critical defect. Partial runs are
training evidence, not an award prediction.
