# Executable Kernels and Paper Audits Design

## Scope

Implement the first four approved improvements without changing the Skill's
explicit-invocation rule or its phase order:

1. executable reference kernels for five high-risk CUMCM B/C structures;
2. synthetic hidden-truth and metamorphic regression tests;
3. measured compute-budget evidence with a tested fallback route; and
4. an advisory Chinese academic-prose audit.

The implementation must keep contest statements, attachments, private
regression cases, and answers outside the repository. It must not turn a
reference kernel into evidence that the same model fits a future problem.
GitHub publication is outside this change; local repository and installed-Skill
synchronization follow successful verification.

## Chosen approach

Use a hybrid, dependency-bounded design. Every kernel has a deterministic
standard-library path for portability. NumPy/SciPy may provide a stronger or
faster path when already available, and CI exercises that path with pinned
minimum-compatible dependencies. Contest mode never installs packages or
silently changes backends.

Do not add another large section to `SKILL.md`. Put deterministic behavior in
scripts, method-specific contracts in the model library, and operating guidance
in one-level embedded references. Add only short routing requirements to the
main workflow.

## Components

### Executable model-kernel package

Add `scripts/model_kernels/` with one bounded module per structure and a shared
result contract. Cover:

- bearing-only localization and observability;
- geometric coverage and path-length checking;
- compositional closure, zero replacement, and log-ratio transforms;
- interval-censored event-time estimation; and
- robust binary allocation on auditable small instances.

Add a dispatcher that accepts a kernel ID, JSON input, backend selection, and
JSON output. A successful result records the kernel/version, backend actually
used, input hash, parameters, diagnostics, result, warnings, and status. A
missing optional dependency either selects the declared standard-library path
or returns `LIMITED`; it must never pretend to run the scientific backend.

Extend each relevant model card with an `implementation` object containing the
dispatcher path, kernel ID, example input, supported backends, input/output
contract, required diagnostics, and declared fallback. The remaining four model
cards retain explanatory routing and explicitly declare that no bundled kernel
is provided. The model-library validator checks both cases.

### Synthetic truth and metamorphic regression

Store only small synthetic JSON fixtures under
`assets/model-library/fixtures/`. Each fixture contains a generator seed or
fully specified input, hidden truth, metric, tolerance, and transformations.
The regression runner must test:

- recovery of a known location, event-time distribution, composition, coverage
  property, or robust feasible decision;
- coordinate translation/rotation where applicable;
- unit scaling and input-order invariance where applicable;
- feasibility residuals and independently recomputed objectives;
- declared degradation or uncertainty widening under added noise or weaker
  information; and
- a degenerate case that must be reported as weakly identified, infeasible, or
  limited instead of producing false precision.

Write a hash-bound JSON report with one record per check. These tests validate
the bundled kernel on synthetic microcases; they do not validate a contest
model or replace problem-specific checks.

### Measured compute budget

Add a cross-platform command profiler. It runs an explicit tokenized command,
applies a timeout, records exit status, wall time, repetitions, input scale,
stdout/stderr hashes, and result-artifact hash. Peak resident memory is measured
with `psutil` when available; otherwise the report marks memory evidence
`LIMITED` while retaining wall-time evidence.

Initialize `reports/compute_budget.csv` for project-level declarations and
append immutable raw measurements to `reports/compute_runs.jsonl`. The verifier
requires, for every selected primary route:

- at least two measured input scales or a documented reason only one exists;
- a successful representative or full-scale run;
- solver status and gap when an optimizer exposes them;
- an explicit timeout and remaining-time comparison; and
- a linked fallback run that completes within its declared budget.

The verifier binds declarations to profiler output and result hashes. It does
not infer asymptotic complexity from two timings or call a heuristic optimum.

### Advisory Chinese academic-prose audit

Add a LaTeX-aware audit for reachable Chinese manuscript sections. Strip
comments and non-prose commands while preserving file and line locations. Emit
severity-tagged findings for:

- unusually long sentences or paragraphs;
- undefined uppercase abbreviations on first use;
- exact or near-duplicate conclusion sentences;
- vague evaluative terms without nearby numeric, figure, table, citation, or
  verified-value evidence;
- causal verbs without nearby identification or limitation language;
- repeated raw quantities with inconsistent decimal precision or units; and
- excessive use of generic self-reference such as “本文”.

Style findings are advisory by default: readable input produces a `PASS` report
with warnings and an `advisory_status`. Unreadable sources, missing target
sections, or an invalid exemption ledger are hard failures. A training-only
`--fail-on` option may promote selected severities to failure. Human-reviewed
exceptions live in `reports/prose_style_exemptions.csv` with rule, locator,
reason, reviewer, and status.

## Data flow

1. Model routing selects a card from structural signals.
2. The card points to a runnable baseline kernel and synthetic regression.
3. The team adapts the method to local contest data and records problem-specific
   evidence separately from the bundled synthetic result.
4. The compute profiler captures actual primary and fallback executions.
5. The compute-budget verifier binds measurements to declared model decisions.
6. Paper generation consumes verified project results, not bundled fixture
   values.
7. The prose audit examines the reachable LaTeX source and emits locatable
   warnings for human review.

## Workflow integration

- Phase 2 requires model-card implementation and synthetic-regression evidence
  when a bundled kernel is used.
- Phase 4 requires measured compute-budget and fallback evidence for decisive
  computational routes.
- Phase 7 runs the Chinese prose audit after abstract and conclusion drafting.
- Phase 9 reruns all three verifiers and treats unresolved compute failures as
  blocking, while prose warnings remain advisory unless explicitly promoted.
- `init_contest.py` creates only project ledgers and no fabricated run rows.
- Strict orchestration adds specialist nodes and stale-report bindings without
  changing existing phase semantics.

## Error handling

- Invalid JSON, unsafe output paths, non-finite values, or schema mismatch fail
  with a nonzero exit code and a written report when possible.
- Degenerate mathematics returns a typed diagnostic status rather than a
  precise-looking answer.
- A requested unavailable backend never falls through silently.
- Profiler timeouts terminate the child process tree when supported, preserve
  partial logs, and mark the run `TIMEOUT`.
- Missing memory instrumentation is `LIMITED`, not zero memory.
- Prose heuristics never rewrite LaTeX automatically.

## Verification and acceptance

Add unit and integration tests for:

- dispatcher input/output contracts and all five kernels;
- standard-library and scientific backends;
- hidden-truth recovery, invariance, degradation, and degenerate cases;
- profiler success, timeout, fallback linkage, stale hashes, and missing memory
  instrumentation;
- prose finding locations, exemptions, false-positive boundaries, and advisory
  versus strict behavior;
- model-card schema, initializer outputs, orchestration nodes, report bindings,
  UTF-8 paths, and existing phase compatibility.

CI adds one bounded scientific-kernel job installing NumPy, SciPy, and psutil.
The existing dependency-light jobs continue to exercise portable fallbacks.
Acceptance requires the full test suite, Skill contract validator, model-library
validator, both kernel regression backends, and a semantic comparison after
syncing the installed local Skill.

## Non-goals

- No general-purpose optimization or statistics framework.
- No claim that five kernels cover every B/C problem.
- No automatic model selection from keywords.
- No publication of private statements, data, outputs, or regression scores.
- No automatic rewriting of paper prose.
- No award prediction or guarantee.
