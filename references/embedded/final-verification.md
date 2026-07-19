# Final Verification

Use this module before claiming that the modeling work or paper is complete.

## Evidence Rule

Do not claim completion without fresh verification evidence.

The verification loop:

1. Identify what would prove the claim.
2. Run or perform the check.
3. Read the output or inspect the artifact.
4. Decide whether the evidence supports the claim.
5. State the claim only with the evidence.

## Required Checks

- Every subproblem is answered.
- Assumptions are listed and used consistently.
- Variables and units are consistent.
- `reports/model_decision_log.csv` explains the selected route against a credible baseline for every subproblem.
- Formulas match the model explanation.
- Code, notebook, or spreadsheet execution status is recorded.
- Result tables match paper values.
- Every decisive subproblem claim has a completed, failure-oriented entry in `reports/stress_tests.csv` and a preserved result file.
- Figures match source data and are referenced.
- At least 10 unique, relevant scholarly works are cited in the LaTeX body; each
  key is present in `paper/references.bib` and `reports/bibliography.csv`, with
  authoritative metadata verification, an exact-title Google Scholar query, a
  supported claim, and a source locator. The cited passages have been read.
- Submission format matches contest requirements.
- For CUMCM 2026, run `verify_submission.py --profile cumcm-2026`; explicitly record main-text pages, visual abstract-first/no-TOC checks, and the support archive result.
- Run `verify_paper_depth.py` with the visually confirmed main-text and appendix
  counts. Confirm every numbered subproblem has its own completed depth-plan row;
  a long code appendix does not compensate for an abbreviated main argument.
- For Chinese 2025-format contests, `paper-writing-zh-cn-format2025.md` checks are complete: abstract is first in the electronic paper, commitment and number pages are excluded from the electronic paper, appendix and support-material rules are satisfied, and identity information is absent.
- Missing plugin/runtime limitations are recorded.
- The contest rules snapshot is current and all critical fields are verified.
- AI use/non-use declaration and required detail report match the actual workflow.
- Data source permissions, transformations, hashes, environment, command, seed, solver status, and validation evidence are recorded.
- Submission state, final hashes, anonymity scan, artifact size, and receipt are recorded when submission is in scope.
- `reports/claims.csv` and `reports/argument_coverage.csv` pass `scripts/verify_claims.py`.
- `paper/main.tex` compiles to the inspected `paper/main.pdf`; source and PDF are
  both retained as the first deliverable.
- `support.zip` contains the allow-listed code, data or legal retrieval evidence,
  environment, exact commands, results, licenses, and hashes as the second
  deliverable. `scripts/verify_paper_delivery.py` returns `PASS`.

## Verification Report

Create or update `reports/verification_report.md` with:

- checks performed
- commands run, if any
- files inspected
- pass/fail status
- unresolved risks
- final submission readiness
- `reports/paper_delivery.json`, including its structural-only scope and the
  separate human checks of source content and rendered PDF layout

## Optional award-focused review

After this baseline verification and before the submission freeze, ask the user
whether they want the optional post-paper award review. If they opt in and
accept revisions, repeat this verification module after rebuilding the affected
results and paper, complete `reports/reviewer_scorecard.csv`, and run
`scripts/verify_award_readiness.py`.

## Red Flags

Stop and verify when about to write:

- "should be correct"
- "looks done"
- "probably passes"
- "final version"
- "ready to submit"

These phrases require evidence.
