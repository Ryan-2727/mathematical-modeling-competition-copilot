# Evidence-Triggered Paper Narrative Design

## Objective

Reduce formulaic, generic, or visibly machine-produced prose in mathematical
modeling papers by making the paper expose the team's real decision trail. The
paper should explain why a model was selected, where decisive parameters came
from, what genuinely failed, how the solution path developed, and where the
conclusion stops being reliable.

This design does not claim to detect AI authorship or guarantee a similarity
score. It improves originality and reader trust through independent wording,
evidence-bound reasoning, and mandatory human review.

## Chosen Approach

Use an evidence-triggered narrative audit. Do not require the same headings or
paragraph pattern for every subproblem. Require content only when the underlying
project evidence creates the corresponding obligation.

Rejected alternatives:

- Text-only reminders are too easy to omit and cannot be audited.
- Generated paragraph templates increase structural completeness but create the
  repetitive style this change is intended to reduce.

## Trigger Rules

Every core subproblem must expose a concise modeling path from problem signal to
verified conclusion. Additional obligations are conditional:

- Explain model A versus model B when a credible competitor or parent model was
  actually evaluated, or when the final choice is otherwise non-obvious.
- Explain a parameter or threshold when it materially affects a claim. Bind it
  to one of four source classes: verified literature, observed/test data,
  declared expert assumption, or official rule/constant.
- Describe a failed route only when an executed command, diagnostic, or frozen
  artifact proves that it was attempted. Never invent failure history to make
  the paper appear thoughtful.
- State an abnormal or boundary condition when feasibility, numerical stability,
  identifiability, extrapolation, or the recommendation changes near that
  boundary.

## Evidence and Data Flow

Reuse the existing project ledgers as source evidence:

- `reports/model_decision_log.csv` and `reports/model_challenge.json` for model
  promotion or rejection;
- `reports/parameter_registry.csv`, bibliography evidence, result artifacts, and
  official snapshots for parameter provenance;
- `reports/model_simplification_log.csv` and `reports/fallback_plan.csv` for
  executed failures and degradation routes;
- `reports/claims.csv`, independent routes, stress tests, and result
  reconciliation for boundary statements and final claims.

Add `reports/paper_reasoning_map.csv` as a paper-location map, not a duplicate
database. Each row identifies a subproblem, paper location, linked model decision
IDs, parameter IDs, failure IDs when applicable, route evidence, boundary
evidence, human reviewer, and status.

The flow is:

```text
executed evidence -> existing ledgers -> paper reasoning map -> natural prose
-> narrative verifier -> human review -> final LaTeX/PDF checks
```

## Paper-Writing Behavior

Integrate the reasoning naturally into problem analysis, model construction,
result interpretation, or model evaluation. Do not create mandatory visible
headings such as "Why A Not B" or "Failed Attempts".

The paper should:

- state the decisive mechanism and the shortest credible path to the result;
- compare alternatives with an executed metric, diagnostic, feasibility result,
  or data-demand argument instead of generic praise;
- explain whether each claim-sensitive parameter is cited, calibrated, assumed,
  or rule-bound, including uncertainty or sensitivity where needed;
- turn a genuine failed attempt into a specific lesson and fallback, without
  narrating routine trial-and-error;
- interpret anomalies and boundary cases in the context of the original
  decision;
- preserve variation in paragraph structure and sentence openings while keeping
  technical claims precise.

No component may auto-rewrite the final prose. The Skill may locate weak passages
and explain the issue; a team member must make and approve the final wording.

## Deterministic Checks

Add `scripts/verify_paper_reasoning_narrative.py` to validate cross-file evidence
and paper locations. It should fail for missing required evidence, stale hashes,
unsafe paths, nonexistent IDs, invented failure references, or an unreviewed
final map. Absence of a non-triggered alternative or failed route must not fail.

Extend the advisory Chinese prose checker with located findings for:

- repeated paragraph openings or sentence stems;
- excessive mechanical transitions;
- generic model praise without a nearby evidence locator;
- repeated conclusion sentences and detached method catalogues;
- unsupported universal claims that omit an applicability boundary.

These findings remain advisory by default because style and authorship cannot be
reliably inferred from word frequency alone. The checker must never label text
as "AI-generated".

## Skill and Documentation Integration

- Keep `SKILL.md` below its line budget by adding only a concise routing rule.
- Put detailed behavior in the paper-writing, result-first, depth-budget, and
  evidence-gate references without duplicating ownership.
- Update the workflow map, contract, README mirrors, project initializer, and
  relevant paper template comments.
- Keep the reasoning map and style reports in the complete delivery/evidence
  package; do not add them to the official submission unless current rules
  require them.

## Failure Handling

- If a source ledger is absent, report the exact missing trigger evidence and do
  not fabricate prose.
- If literature does not support a threshold, reclassify it as data-calibrated
  or assumed only when that classification is true, then add sensitivity.
- If a failed route lacks executable evidence, omit the claim that it was tried.
- If a boundary cannot be quantified, state a qualitative applicability limit
  and mark the claim as conditional.
- If human review is incomplete, keep the paper gate at `LIMITED` or `FAIL`
  according to the selected verification profile.

## Verification Plan

Use test-driven changes with fixtures that prove:

1. A core model with a real competitor fails when the selection rationale has no
   linked evidence and passes after the paper location is bound.
2. A literature threshold requires verified citation evidence; a calibrated
   threshold requires data and result locators; an assumption requires an
   explicit label and sensitivity evidence.
3. A recorded failed route requires an executable failure artifact, while a
   project with no failed route is not forced to invent one.
4. Boundary-sensitive claims require an applicability or abnormal-condition
   statement.
5. Natural prose can pass without fixed headings or prescribed sentences.
6. Repetitive openings and mechanical transitions produce located advisory
   findings and never an AI-authorship verdict.
7. Existing contract, full unit tests, model-library checks, Skill validation,
   README mirror equality, and local-installation hash verification still pass.

## Success Criteria

- The paper records real modeling judgment instead of a method catalogue.
- Every claim-sensitive model choice and parameter source is traceable.
- Failed attempts and boundary conditions appear only when supported and useful.
- The workflow discourages repetitive generated prose without prescribing a new
  repetitive template.
- A human reviewer remains the authority for final wording.
- Existing contest, privacy, LaTeX, evidence, and delivery mechanisms remain
  unchanged except for the new narrative gate.

## Non-Goals

- Guaranteeing a plagiarism percentage or bypassing similarity systems.
- Claiming that an automated detector can identify AI-written text.
- Inflating paper length with fabricated alternatives, failures, or boundaries.
- Replacing the team's mathematical judgment or final prose review.
