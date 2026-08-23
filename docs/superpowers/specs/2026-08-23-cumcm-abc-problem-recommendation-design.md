# CUMCM A/B/C Problem Recommendation Design

## Scope

Add an evidence-backed CUMCM A/B/C recommendation stage to the existing six-hour
problem audition. The stage must compare all three problems, describe strengths
and weaknesses, estimate which problem best matches the current AI/Codex
capabilities, and require user confirmation before the H6 problem lock.

This feature evaluates the AI only. It does not score the student team, and every
report must state that team expertise can change the best final choice. It must
not claim to know the official judging outcome or guarantee an award.

## Confirmed product decisions

- Always produce a relative ranking and confidence assessment.
- Produce award-probability intervals only when calibration evidence passes
  explicit sufficiency gates.
- Score current AI capability from a bundled prior updated by same-day
  executable audition evidence.
- Use a staged six-hour audition: screen all three problems, then deepen the top
  two, and lock by H6.
- Estimate mutually exclusive national first, national second, provincial
  award, and no-award outcomes when calibration is available.
- Rank probability-backed recommendations by national-award probability,
  defined as national first plus national second.
- Use verified public award statistics as a weak prior and local private
  historical outcomes as an on-device adjustment.
- Never upload private statements, attachments, solutions, scores, or
  calibration records.
- Generate a recommendation, then ask the user. Never auto-lock a problem.

## Chosen architecture

Keep recommendation generation separate from the existing H6 evidence
validator. The system has four layers:

1. **Inputs**: AI capability prior, runtime snapshot, A/B/C screening evidence,
   executable audition artifacts, public prior, and optional private
   calibration records.
2. **Evaluation**: deterministic criteria, capability updating, time fairness,
   fatal-risk gates, weight scenarios, and optional probability calibration.
3. **Recommendation**: hash-bound JSON plus a Chinese Markdown decision report.
4. **Confirmation**: a separate confirmation action binds the user's decision
   to the exact recommendation hash before `verify_problem_audition.py` accepts
   the H6 lock.

Do not fold recommendation prose or probability estimation into
`verify_problem_audition.py`. That script remains the final evidence and lock
validator, with only the additional stale-report and confirmation checks needed
for integration.

## Six-hour operating sequence

| Window | Required action | Comparable evidence |
| --- | --- | --- |
| H0-H0.75 | Screen A, B, and C for 15 minutes each | structure, attachments, semantics, deliverables, required model families |
| H0.75-H2.25 | Run a 30-minute micro-baseline for each problem | command, result or typed failure, elapsed time, minimum diagnostic |
| H2.25 | Rank the three and remove one | preliminary scores, fatal risks, evidence coverage |
| H2.25-H5.25 | Give the top two 90 minutes each | deeper baseline, validation, one paper-grade figure, fallback route |
| H5.25-H6 | Recompute scenarios and calibration, render reports, ask the user | recommendation hash, confidence, confirmation or documented alternative |

Timing is compared from measured run evidence rather than an AI assertion. A
candidate that receives more than 20% extra micro-baseline time without a typed
early failure or documented exception makes the comparison `LIMITED`. The top
two must receive equal declared deep-trial budgets. A recommendation may still
be rendered under `LIMITED`, but it cannot be labeled high confidence.

## Evaluation model

Each candidate receives an integer evidence rating from 0 to 4 for every
criterion. Zero means failed or contradicted; one means weak; two means partial;
three means supported; four means strong. Unknown is distinct from zero and is
never imputed as a favorable value. Every rating requires at least one safe,
project-relative evidence locator and its SHA-256 hash.

The base composite uses these normalized weights:

| Criterion | Weight |
| --- | ---: |
| subproblem closure and result production | 0.25 |
| result verifiability | 0.20 |
| current AI capability fit | 0.20 |
| data and semantic controllability | 0.10 |
| compute-time and fallback reliability | 0.10 |
| paper and figure potential | 0.10 |
| evidence-backed innovation headroom | 0.05 |

The AI capability-fit rating combines 30% bundled prior and 70% observed
same-day evidence. Observed evidence includes successful parsing, runnable
baselines, required model-family coverage, diagnostics, and typed failures. If
the prior and live evidence disagree materially, the report flags the conflict
and live evidence controls the final rating.

In addition to the base weights, run at least closure-first,
verification-first, AI-fit-first, and paper-presentation scenarios. Report each
candidate's scenario win rate, worst rank, and minimum score margin. High
confidence requires all of the following:

- no unresolved fatal risk;
- no unknown decisive criterion;
- fair audition timing;
- scenario win rate of 1.0; and
- minimum score margin of at least five points.

Medium confidence requires a scenario win rate of at least 0.75 and no fatal
risk. Otherwise confidence is low or the result is a tie. A margin below three
points or unresolved evidence conflict must render co-leading candidates rather
than a false single winner.

## Capability prior and snapshot

Bundle `assets/problem-selection/ai-capability-profile.json`. It describes
capability by model family and task, not by problem letter. At minimum it covers
data parsing, statistics, forecasting, optimization, simulation, differential
equations, graph/network methods, uncertainty, visualization, reproducible code,
and LaTeX paper organization. Every entry contains a profile version, rating,
limitations, evidence type, and review date.

Generate `reports/ai_capability_snapshot.json` for the current run. Bind the
profile version to observed Python/runtime capabilities, bundled kernel
regressions, available solvers, and Skill commit or content hash. A missing or
stale snapshot prevents calibrated probabilities and lowers recommendation
confidence; it must never be silently replaced by the bundled prior alone.

## Probability calibration

Probability output is optional and subordinate to evidence ranking. Use four
mutually exclusive labels:

- `national_first`
- `national_second`
- `provincial_award`
- `no_award`

Store verified public statistics in `reports/public_award_prior.json` with
source URL, retrieval date, competition scope, applicable years, category
counts, and reviewer status. Convert the public proportions to a weak Dirichlet
prior with configurable effective strength no greater than 10; the default is
8. Reject a prior that lacks a saved source, uses incompatible definitions, or
falls outside its declared applicability.

Store private calibration rows in
`reports/problem_selection_calibration.csv`. Rows contain only a portable case
ID, year, task-family tags, AI profile version, seven criterion ratings,
composite score, final selected problem type, award label, evidence hash, and
verification status. They must not contain statement text, attachment values,
paper prose, solution output, or absolute paths.

For each current candidate, compute local comparison weights from task-family
overlap, AI-profile compatibility, and composite-score proximity. Define
effective local sample size as `(sum(w)^2) / sum(w^2)`. Calibrated probabilities
are permitted only when:

- effective local sample size is at least 12;
- verified rows cover at least three distinct competition years;
- every included row has one recognized award label;
- the public prior is verified and applicable; and
- the current capability snapshot is valid.

Add weighted local outcome counts to the public Dirichlet prior. Use a
deterministic seed derived from the bound input hashes to draw 10,000 Dirichlet
samples with the Python standard library. Report posterior means and central
80% intervals. The four posterior means must sum to one. Rank probability-backed
candidates by `P(national_first) + P(national_second)`; use robust composite
ranking when calibration is unavailable.

If any probability gate fails, emit `INSUFFICIENT_EVIDENCE`, list the failed
gates, and omit numerical percentages. Do not fall back to invented values or
generic national rates presented as personalized estimates.

## Data contracts

Initialize these project-local artifacts:

- `reports/problem_screening.csv`: one A/B/C row with timing, task families,
  attachment state, semantic risk, expected deliverables, and evidence locators.
- `reports/ai_capability_snapshot.json`: current prior/runtime/Skill binding and
  observed capability evidence.
- `reports/problem_selection_calibration.csv`: empty private calibration ledger.
- `reports/public_award_prior.json`: empty source-backed prior object.
- `reports/problem_selection_recommendation.json`: generated recommendation.
- `reports/problem_selection_recommendation.md`: generated Chinese reader report.

Retain `reports/problem_audition.csv` for executable baselines and deepen its
evidence through additive fields or a companion structured artifact. Migration
must be additive and idempotent. Existing projects remain readable; strict mode
requires the new contracts only after migration to the new orchestration schema.

The JSON recommendation contains:

- input hashes and schema/profile versions;
- candidate criterion ratings and evidence locators;
- base and scenario scores, ranks, win rates, margins, and fatal risks;
- strengths, weaknesses, unresolved unknowns, and fallback route;
- calibration-gate results and optional four-outcome distributions;
- recommended problem or co-leading set;
- confidence, limitations, and `requires_user_confirmation=true`.

The Chinese Markdown report presents, for every problem, its suitable model
families, evidence-backed advantages, disadvantages, fatal risks, fallback
route, ranking, and probability status. It must show at least three supported
strength/weakness/risk observations in total per problem. If evidence cannot
support three, state the shortfall instead of inventing content.

## Confirmation and lock

Provide a narrow confirmation command that records a declared user decision
after the Skill has asked the user. It writes the selected problem,
recommendation file and SHA-256, confirmation time, and optional note into
`reports/problem_selection.json`. It does not authenticate identity and must
describe itself as an audit record, not proof of who clicked or typed.

Enhance `verify_problem_audition.py` to reject:

- no confirmation;
- a recommendation hash that no longer matches;
- selected problem different from the confirmed problem;
- recommendation inputs stale relative to current evidence; or
- confirmation recorded before recommendation generation.

A confirmed non-recommended problem is allowed only with the existing
evidence-backed selection-exception mechanism. Any change to screening,
audition, capability, prior, or calibration inputs invalidates both the
recommendation and confirmation.

## Privacy and network boundary

All recommendation and calibration computation is local. The runtime script
contains no network client. A separate allowed search step may gather public
statistics without sending private records or contest artifacts. If a proposed
online action has ambiguous disclosure risk, follow the existing rule: pause
and ask the user, then record the decision locally.

Repository fixtures and CI use only synthetic A/B/C candidates and synthetic
award labels. Never commit generated recommendation reports, private
calibration rows, current statements, attachments, results, or papers. Output
portable relative locators and hashes; redact machine-specific command paths.

## Error handling and honest degradation

- Missing any A/B/C screening row blocks a claim of three-problem comparison.
- Missing evidence produces `unknown`, not a favorable default.
- Typed baseline failures remain visible disadvantages.
- Unresolved fatal risk prevents default recommendation of that candidate.
- Unfair timing caps confidence at `LIMITED`.
- Inapplicable public statistics or insufficient local calibration suppress all
  percentages.
- Weight instability or a margin below three produces co-leading candidates.
- Invalid, stale, unsafe, or absolute evidence locators fail verification.
- The report always states that team ability is outside the model and can change
  the real best choice.

## Workflow integration

- `init_contest.py` creates empty contracts without fabricated evidence.
- Add a recommendation node after comparable candidate baselines and before
  selection confirmation.
- Standard and strict profiles bind recommendation outputs to all input hashes.
- The H6 lock remains in `verify_problem_audition.py` and requires confirmation.
- Keep `SKILL.md` changes short and route detailed instructions to the existing
  CUMCM readiness reference.
- Update the workflow map, Skill contract, and English/Chinese README sections.
- Preserve the explicit-invocation-only trigger and all current phase order.

## Testing and acceptance

Add unit tests for rating normalization, 30/70 capability updating, scenario
scores, ties, fatal risks, unknown evidence, timing fairness, deterministic
calibration, effective sample size, interval ordering, and probability sums.

Add integration tests for:

- A/B/C initialization and idempotent migration;
- no percentages below the calibration threshold;
- valid synthetic calibration across three years;
- stale public priors and capability snapshots;
- recommendation/confirmation hash binding;
- a confirmed non-recommended selection with and without an exception;
- relative-path and private-content protections;
- standard and strict orchestration placement; and
- compatibility with existing audition and H6 tests.

Forward-test the explicit Skill on three purely synthetic candidate statements.
The run must generate JSON and Chinese Markdown reports, withhold or produce
probabilities according to evidence, ask for confirmation, and complete the H6
gate only after a declared response.

Acceptance requires the full existing test suite, new targeted tests, Skill
contract validator, Skill Creator validator, clean diff checks, privacy scans,
and semantic hash equality after syncing the installed local Skill.

## Non-goals

- No automatic problem lock.
- No team-skill scoring in the recommendation score.
- No online processing of private contest or calibration material.
- No claim that a probability predicts official judging with certainty.
- No complex general-purpose award-prediction platform.
- No model choice based only on A/B/C letters, keywords, or historical topic
  stereotypes.
