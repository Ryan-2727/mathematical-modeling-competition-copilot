# Training and evaluation loop

Use only in training or post-hoc mode. Historical excellent papers may teach
general structure after a baseline is frozen, but they must not become paired
inputs during independent solving.

## Blind benchmark

1. Select an unseen historical problem and hide all solution papers.
2. Run the full workflow under a declared time budget.
3. Freeze statement, data, code, result files, figures, paper, and logs.
4. Score the run with the internal four-dimension reviewer scorecard and record
   concrete failure evidence.
5. Only then inspect multiple excellent papers for general writing or validation
   patterns; never copy wording, values, models, or figure designs.
6. Change at most three reusable rules and rerun a different unseen problem.

Track across problems: subproblem completion, baseline completion time,
reproduction pass rate, decisive-claim stress-test coverage, numerical defects,
reviewer objections, paper rebuild time, and compliance failures. Promote a rule
only when it improves more than one problem type without leaking task-specific
answers.

For the 2026 CUMCM readiness sequence, use 8-, 24-, 48-, and 74-hour rehearsals.
Record `reports/training_runs.csv` and `reports/training_defects.csv`, then run
`scripts/score_training_readiness.py`. A `PASS` requires a successful full
74-hour run and no unresolved critical defect; shorter runs are `LIMITED`
readiness evidence.
