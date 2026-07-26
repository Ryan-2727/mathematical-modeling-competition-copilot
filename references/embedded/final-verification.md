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
- `results/verified_values.csv` is the single source for decisive computed
  values. Generate `paper/generated/results.tex`, then run
  `scripts/verify_verified_values.py`; reject stale hashes, duplicate keys,
  invalid types or units, unused decisive macros, and conflicting manual values.
- Run `scripts/verify_model_validation.py` for every declared primary model
  family. Preserve the actual diagnostic artifacts and predeclared thresholds.
- Every decisive subproblem claim has a completed, failure-oriented entry in `reports/stress_tests.csv` and a preserved result file.
- Figures match source data and are referenced.
- At least 10 unique, relevant scholarly works are cited in the LaTeX body; each
  key is present in `paper/references.bib` and `reports/bibliography.csv`, with
  authoritative metadata verification, an exact-title Google Scholar query, a
  supported claim, and a source locator. The cited passages have been read.
- Run `scripts/verify_bibliography_metadata.py` against hash-bound authoritative
  metadata snapshots, retraction-check records, and supporting-passage evidence.
- Run `scripts/verify_abstract_quality.py`; confirm every numbered task is
  represented by its method, decisive result, validation, and answer or
  recommendation.
- Run `scripts/verify_manuscript_quality.py`; resolve missing captions/labels,
  unreferenced figures, undefined citations/references, figure-manifest gaps, and
  material LaTeX log warnings.
- Submission format matches contest requirements.
- For CUMCM 2026, run `verify_submission.py --profile cumcm-2026`; explicitly record main-text pages, visual abstract-first/no-TOC checks, and the support archive result.
- Run `verify_paper_depth.py` with the visually confirmed main-text and appendix
  counts. Confirm every numbered subproblem has its own completed depth-plan row;
  a long code appendix does not compensate for an abbreviated main argument.
  Treat empirical minimum page targets as advisory unless the official rules
  impose a minimum; always enforce the official maximum.
- For Chinese 2025-format contests, `paper-writing-zh-cn-format2025.md` checks are complete: abstract is first in the electronic paper, commitment and number pages are excluded from the electronic paper, appendix and support-material rules are satisfied, and identity information is absent.
- Missing plugin/runtime limitations are recorded.
- The contest rules snapshot is current and all critical fields are verified.
- AI use/non-use declaration and required detail report match the actual workflow.
- Data source permissions, transformations, hashes, environment, command, seed, solver status, and validation evidence are recorded.
- Submission state, final hashes, anonymity scan, artifact size, and receipt are recorded when submission is in scope.
- `reports/claims.csv` and `reports/argument_coverage.csv` pass `scripts/verify_claims.py`.
- Run `scripts/verify_evidence_chain.py`; every decisive claim has a locatable
  code/command, data hash, result hash, verified-value macro, figure label, and
  paper location. Rebuild the paper after a result-hash change.
- Run `scripts/verify_decision_quality.py`; confirm every selected route has a
  baseline/candidate refutation record, uncertainty comparison where material,
  fallback route, causal-boundary record where applicable, and implementability
  evidence beyond the objective value.
- Run `scripts/verify_figure_narrative.py`; each figure identifies its claim,
  question, takeaway, and decision relevance.
- Complete `reports/page_readability_checklist.csv` against the compiled PDF and
  run `scripts/verify_page_readability.py`. A missing renderer is `LIMITED`, not
  visual proof; unresolved checklist cells are `FAIL`.
- `paper/main.tex` compiles to the inspected `paper/main.pdf`; source and PDF are
  both retained as the first deliverable.
- Run `scripts/verify_pdf_visual.py` on `paper/main.pdf`. Review the rendered
  pages and its page count, page size, first-page markers, forbidden TOC
  markers, sparse pages, figure/table references, raster warnings, and metadata
  findings. `LIMITED` is acceptable only for optional checks; a missing tool or
  visual-evidence file for a mandatory rule is `FAIL`. The default forbids a
  table-of-contents heading for CUMCM; use `--allow-contents` only when the
  selected official profile permits or encourages one, such as the current
  MCM/ICM profile.
- Run `scripts/anonymity_scan.py` over source, PDF, images, and archives.
  Inspect image metadata and rendered-page OCR when available; record OCR
  absence as a limitation unless the selected profile makes that check
  mandatory.
- `scripts/verify_latex_compatibility.py` produces a fresh, compile-backed
  `reports/latex_compatibility.json` for both project-root and `build/` output
  paths; its source fingerprint matches the delivered paper tree.
- When LaTeX source is delivered, create a portable source ZIP with `main.tex`
  at its archive root. It must include `README.md`, `.latexmkrc`,
  `.vscode/settings.json`, all included sections, bibliography, figures, code,
  styles, and assets. Run `scripts/verify_portable_latex.py --archive <zip>
  --out <report> --compile`; record its JSON result, archive hash, and any
  unavailable XeLaTeX limitation. Confirm VS Code can use the packaged
  `latexmk (XeLaTeX)` recipe and that the root `main.tex` is the stated Overleaf
  entrypoint.
- `support.zip` contains the allow-listed code, data or legal retrieval evidence,
  environment, exact commands, results, licenses, and hashes as the second
  deliverable. `scripts/verify_paper_delivery.py` returns `PASS`.
- Run `scripts/verify_delivery_profiles.py`; preserve the full user delivery
  under `delivery/` and only profile-permitted files under
  `official-submission/`.
- The frozen reproduction runs from a clean copied project without an implicit
  shell. Commands are argv arrays unless `--allow-shell` is explicitly recorded.
  Repeated runs agree by output hashes or declared tolerance-aware CSV
  comparisons, and each run retains its own log and environment evidence.
- Run `scripts/contestctl.py check` for `setup`, `modeling`, `paper`, `delivery`,
  and `freeze`; do not edit its reports to bypass a failed specialist gate.

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
- `reports/latex_compatibility.json`, including both build commands, PDF outputs,
  source fingerprint, and visual-inspection result
- `reports/pdf_visual_verification.json`, including tool availability, rendered
  pages, findings, limitations, and the selected profile
- verified-value and model-validation report paths, fingerprints, statuses, and
  unresolved evidence limitations
- clean-reproduction run directories, commands, input/output hashes, comparison
  policy, and repeated-run verdict
- portable LaTeX archive path, hash, root-entrypoint check, VS Code recipe check,
  fresh-directory compile status, PDF page count, and Overleaf configuration note

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
