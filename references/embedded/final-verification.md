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
- Formulas match the model explanation.
- Code, notebook, or spreadsheet execution status is recorded.
- Result tables match paper values.
- Figures match source data and are referenced.
- Literature claims have sources.
- Submission format matches contest requirements.
- For CUMCM 2026, run `verify_submission.py --profile cumcm-2026`; explicitly record main-text pages, visual abstract-first/no-TOC checks, and the support archive result.
- For Chinese 2025-format contests, `paper-writing-zh-cn-format2025.md` checks are complete: abstract is first in the electronic paper, commitment and number pages are excluded from the electronic paper, appendix and support-material rules are satisfied, and identity information is absent.
- Missing plugin/runtime limitations are recorded.
- The contest rules snapshot is current and all critical fields are verified.
- AI use/non-use declaration and required detail report match the actual workflow.
- Data source permissions, transformations, hashes, environment, command, seed, solver status, and validation evidence are recorded.
- Submission state, final hashes, anonymity scan, artifact size, and receipt are recorded when submission is in scope.
- `reports/claims.csv` and `reports/argument_coverage.csv` pass `scripts/verify_claims.py`.

## Verification Report

Create or update `reports/verification_report.md` with:

- checks performed
- commands run, if any
- files inspected
- pass/fail status
- unresolved risks
- final submission readiness

## Red Flags

Stop and verify when about to write:

- "should be correct"
- "looks done"
- "probably passes"
- "final version"
- "ready to submit"

These phrases require evidence.
