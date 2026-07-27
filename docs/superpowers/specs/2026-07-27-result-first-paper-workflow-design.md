# Result-First Paper Workflow Design

## Goal

Make a contest paper answer-focused: a concise abstract explains analysis,
method, and result; every subproblem produces a verified deliverable; and visual
communication shows mechanism, results, comparison, and validation without
decorative volume.

## Design

### Structured abstract

Add a lightweight abstract-structure verifier. The abstract must contain three
short, explicit blocks: problem analysis, method, and results. The result block
must contain a quantitative output or direct recommendation; the existing
answer-density verifier continues to require validation and a conclusion. A
configurable upper content-unit limit protects concision without assuming a
single contest's page limit.

### Result-first simplification gate

Create `reports/model_simplification_log.csv` and a result-story verifier. For
each answered subproblem, the log records whether the primary route produced a
verified result. If it did not, the workflow must stop and ask the user whether
to remove specified noncritical factors. Only an explicit authorization permits
a simplified route. The log records retained mechanism, removed factors,
failure diagnostic, result file, paper boundary, and marks the original route
as `model_optimization` rather than a delivered result. No number may be
invented to avoid this gate.

### Visual storyboard and model comparison

Create `reports/visual_storyboard.csv`. Each visual has an artifact type,
subproblem, question, claim, source result, rationale, and paper location.
Every answered subproblem receives a result chart; a mechanism diagram,
path/network diagram, comparison figure, or validation chart is required only
when it is relevant. A baseline/candidate entry in `model_challenge.json`
requires a model-comparison visual or table. The design system continues to
protect style consistency and readable presentation.

## Integration

Add `verify_abstract_structure.py` and `verify_result_story.py`; initialize the
two ledgers; require their reports at submission freeze; add concise workflow
instructions and an embedded reference. Update tests, contract validation, and
both English and Chinese READMEs. Keep the Skill's explicit-invocation rule and
do not claim that more figures automatically improve a paper.

## Verification

Cover pass/fail paths for three-block abstracts, user-authorized simplification,
missing verified results, missing result visuals, and missing comparison visuals.
Run the full unit suite, contract validator, README mirror check, and diff check.
