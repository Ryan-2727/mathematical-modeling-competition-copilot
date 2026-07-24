# Award-readiness execution design

## Objective

Upgrade the skill from a strong structural workflow into an evidence-backed
competition system that catches compliance, numerical, reproducibility, visual,
and evaluation failures before submission. Preserve the explicit-invocation-only
gate and the rule that optional award review is offered only after modeling,
paper writing, and baseline verification are complete.

## Design principles

1. Official current rules override historical profiles and exemplar statistics.
2. Deterministic scripts enforce fragile requirements; references explain
   problem-dependent judgment.
3. Every `PASS` names its scope. Missing tools produce `LIMITED` or `FAIL`, never
   an unqualified success.
4. Decisive paper values originate in machine-readable results, not duplicated
   prose.
5. Benchmark evaluation uses statements and raw inputs without paired excellent
   papers or hidden expected answers in the solving context.
6. Keep `SKILL.md` as a router. Put detailed contracts in one-level references.

## Track A: executable contest profiles

Add versioned profiles for CUMCM and MCM/ICM with official source URL, verified
date, source digest, artifact types, size/page limits, page-order rules, identity
rules, support-file policy, and AI disclosure policy. Extend submission
verification to:

- fail when a declared profile is stale or missing an official snapshot;
- enforce CUMCM first-page abstract, no table of contents, main-text page count,
  appendix support-file list/code evidence, size/type rules, and AI inline
  disclosure/reference/report evidence;
- enforce current MCM/ICM PDF-only submission, whole-solution page limit,
  Summary Sheet first, readable font declaration, control-number/page headers,
  no extra support files, and AI report placement;
- distinguish text-extractable checks from visual checks and require recorded
  visual evidence for the latter.

Create separate portable LaTeX templates for CUMCM and MCM/ICM. The CUMCM
template includes an appendix manifest and code-listing path. The MCM/ICM
template includes a Summary Sheet entrypoint, English 12-point layout, control
number header, page numbering, and an AI report section outside the counted
solution when the verified rules permit it.

## Track B: quality regression and numerical integrity

Create an end-to-end benchmark manifest covering evaluation, prediction,
optimization, mechanism, network, and simulation tasks. The harness validates
artifact presence and scoring evidence without distributing problem statements
or expected solutions. Each case records:

- problem family and allowed inputs;
- required subproblems and expected artifact classes;
- commands, runtime budget, and result location;
- blinded rubric dimensions for correctness evidence, validation,
  reproducibility, writing, and visual communication;
- baseline score and accepted regression tolerance.

Add a result registry and LaTeX macro generator. Decisive values live in
`results/verified_values.csv`; the generator creates
`paper/generated/results.tex`. A verifier cross-checks unique keys, types,
units, source files, hashes, values, and use in reachable LaTeX. Manual decisive
numbers remain allowed only when explicitly classified and justified.

Add model-family validation adapters driven by a CSV/JSON manifest:

- regression/forecast: split order, leakage, residuals, baseline, holdout;
- classification: class balance, confusion metrics, calibration or threshold;
- optimization: feasibility, constraint audit, solver status/gap, baseline;
- simulation/stochastic: seed set, replication count, convergence/uncertainty;
- network/ranking/evaluation: connectivity or consistency, perturbation,
  normalization and weight sensitivity;
- mechanism/dynamics: units, boundary/initial conditions, limiting cases,
  numerical stability.

Adapters verify declared evidence and numeric thresholds; they do not choose a
model or certify mathematical truth.

## Track C: PDF, anonymity, and CI

Add PDF visual QA that uses `pdfinfo`, `pdftotext`, and page rendering when
available. Check page count/size, blank or text-sparse pages, first-page markers,
forbidden table-of-contents markers, missing figure/table references, suspicious
low-resolution raster assets, metadata/path disclosure, and rendered-page
availability. OCR is optional; unavailable OCR is reported as a limitation.

Strengthen anonymity scanning for image metadata, rendered-page OCR text when
available, archive contents, and contest-specific allowed identifiers.

Expand GitHub Actions:

- fast Python contract/unit job;
- Linux TeX job installing XeLaTeX, latexmk, Chinese fonts, BibTeX, and Poppler;
- compile both bundled templates through project-root, VS Code `build/`, and
  portable ZIP paths;
- keep Windows-specific behavior covered by pure-Python path tests and local
  verification because hosted TeX setup cost is disproportionate.

## Track D: reproducibility and corpus portability

Replace arbitrary shell execution with an argv-file or explicit shell opt-in.
Run reproductions from a clean copied project, capture environment and input
hashes, support repeated runs, and compare output hashes or tolerance-aware CSV
values. Preserve logs for every run.

Replace machine-specific corpus paths with a portable corpus manifest containing
relative identifiers, source category, inspection date, PDF hash, page metrics,
and limitations. Corpus PDFs stay outside the repository. Observations reference
manifest IDs rather than a drive path.

## Track E: independent post-paper review

Keep the user opt-in gate. Add a blinded review packet schema and aggregation
script for independent model, evidence, and writing reviewers. Each reviewer
must cite artifact locations, list one strongest objection, and avoid award
predictions. Aggregation reports disagreement, veto-level findings, accepted
limitations, and whether revisions require rerunning baseline verification.

## Data flow

```text
official snapshot -> contest profile -> initialization/template selection
statement + data -> model/code -> result registry -> generated LaTeX values
model validation + reproduction -> evidence reports -> paper
paper + support -> LaTeX/PDF/submission/anonymity gates
completed baseline -> optional blinded reviewers -> revisions -> rerun gates
benchmark cases -> regression score -> skill release decision
```

## Failure behavior

- Compliance ambiguity, stale rules, missing decisive evidence, source-hash
  mismatch, numerical inconsistency, compile failure, or unresolved anonymity
  finding is `FAIL`.
- Optional renderer/OCR absence is `LIMITED` only when no mandatory rule depends
  on it; otherwise it is `FAIL`.
- Benchmark regression beyond tolerance blocks release but does not modify
  benchmark baselines automatically.
- Reviewer disagreement never blocks baseline delivery by itself; unresolved
  veto findings are shown to the user before freeze.

## Verification and acceptance

1. Unit tests cover positive and negative paths for every new script.
2. Bundled CUMCM and MCM/ICM templates compile with XeLaTeX/latexmk.
3. Portable ZIP verification recompiles both templates from extraction.
4. Submission fixtures exercise page/order/AI/support rules.
5. Reproduction fixtures prove repeated-run match and mismatch behavior.
6. Numeric registry fixtures prove generated macro and stale-source detection.
7. Model-family fixtures include at least one pass and one failure per adapter.
8. PDF QA and anonymity fixtures exercise metadata, text, and unavailable-tool
   behavior.
9. Skill contract, quick validation, `git diff --check`, and the full test suite
   pass before commit and push.

## Explicit non-goals

- No award guarantee or claimed judge simulation accuracy.
- No redistribution of copyrighted contest statements or excellent papers.
- No requirement to use all model families or produce a fixed number of pages,
  figures, or references beyond the user-approved bibliography contract.
- No live-contest browsing that violates the selected contest rules.
