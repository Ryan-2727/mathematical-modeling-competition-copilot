# Decision and delivery gates design

## Objective

Increase the reliability and reviewability of competition papers without pretending
that a generic script can judge mathematical quality.  The workflow will require
auditable evidence for decisive recommendations, figures, time allocation, first
impressions, and the LaTeX build environment.

## Chosen approach

Use small declarative ledgers plus deterministic validators.  Every validator
creates a JSON report and is included in `contestctl freeze`; the freeze report
binds the report to its inputs with SHA-256 digests.  Tests include a valid fixture
and deliberately invalid records so a validator cannot pass only ideal inputs.

This was selected over PDF/image semantic scoring, which is expensive and fragile
across topics, and over prompt-only advice, which cannot be audited at submission
time.

## New gates

| Gate | Ledger / output | Requirement |
|---|---|---|
| Decision stability | `reports/decision_stability.csv` | Every material recommendation has a baseline and at least one perturbation; a flipped recommendation must carry a conditional conclusion and limitation. |
| Figure numeric contract | `reports/figure_numeric_contract.csv` | Every core figure declares its data digest, axes, limits, transform, and decisive values traceable to verified results. |
| Model budget | `reports/model_budget.csv` | Each subproblem has an executable baseline, an explicitly selected route, time/risk/validation-cost estimates, and a documented fallback. |
| Three-minute review | `reports/three_minute_review.csv` | Abstract, route figure, core result, recommendation, and limitation each have a reader-facing answer and evidence location. |
| LaTeX dependency lock | `reports/latex_dependency_lock.json` | The compiler, packages, fonts, build/editor configuration, and source digests are frozen for local/Overleaf diagnosis. |
| Negative testing | unit tests | Each new validator rejects missing, inconsistent, or unsupported evidence. |

## Integration

`init_contest.py` supplies the ledgers with explanatory comments and safe
placeholders.  Five validators emit reports under `reports/`; `contestctl.py`
registers them in the freeze profile and binds their evidence files.  The concise
Skill routes detailed instructions to a new embedded reference so it remains under
the line budget.  English and Chinese READMEs list the gates and their commands.

## Non-goals and safeguards

- Validators do not fabricate numerical reruns, citations, conclusions, or model
  superiority.
- A gate may require a conditional conclusion, but it cannot decide whether the
  underlying model is mathematically correct.
- The budget is an explicit planning record, not an automatic productivity score.
- The LaTeX lock reports unavailable tools honestly instead of treating a missing
  compiler as a successful cross-platform build.

## Verification

Run contract validation, the full unit suite, whitespace checks, and a smoke run of
each new validator against both valid and negative fixtures before committing.
