# Award-oriented workflow router

Use this module only after the skill has been explicitly invoked. It does not
promise an award. It turns the main judging dimensions into evidence gates:
reasonable assumptions, creative modeling, correct results, and clear writing.

## Route by phase

- At setup, read `contest-operations-72h.md` and freeze milestones.
- At decomposition, read `problem-structure-playbooks.md`; organize around the
  decision or explanation required by each subproblem, not around fashionable
  algorithms.
- Before selecting a model, record baseline, candidate, failure test, validation
  cost, and selection evidence in `reports/model_decision_log.csv`.
- Before accepting a conclusion, read `stress-testing-and-uncertainty.md` and
  record decisive tests in `reports/stress_tests.csv`.
- Before fitting or combining data, read `data-units-and-source-quality.md` and
  maintain `reports/units.csv`.
- After the complete paper passes baseline verification and the user opts into
  the optional review, read `reviewer-scorecard-and-presentation.md`.
- In training or post-hoc mode, read `training-evaluation-loop.md`.

## Creativity rule

Creativity means a problem-specific abstraction, mechanism, constraint,
diagnostic, or decision insight that improves the solution. A more complicated
algorithm is not creative by itself. Keep an interpretable baseline and add one
enhancement only when a stated failure test or validation target justifies it.

## Award-readiness gate

Run `scripts/verify_award_readiness.py`. A pass means the evidence artifacts are
complete; it does not certify mathematical truth or predict an award. Human
review remains mandatory.
