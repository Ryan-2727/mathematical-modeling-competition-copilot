# Private CUMCM 2021--2025 regression design

## Purpose

Use a user-owned historical-problem corpus at `<historical-corpus-root>` to improve the mathematical-modeling
competition Skill without publishing contest statements, attachments, solutions,
scores, or run artifacts. The corpus contains 15 intended cases: A, B, and C for
each year from 2021 through 2025.

## Boundaries

- Run only in `training` mode. Never treat a historical run as a live-contest
  submission.
- Keep the benchmark manifest, copied inputs, generated projects, execution logs,
  internal scores, and baseline values in a private workspace outside the Git
  repository.
- Commit only reusable process changes, generic tests, and metadata-free
  documentation. Do not commit problem titles, statements, attachment names,
  numerical answers, benchmark paths, or private scores.
- Exclude files that can reveal prior work or expected outputs, including existing
  papers, code, result workbooks, generated figures, `tmp/`, build artifacts, and
  prior regression material.
- Do not delete or modify any source corpus file. Use a copied, whitelisted input
  set for each run.

## Isolation design

Create a date-stamped private regression root selected by the user. Within it,
create one directory per case with three independent areas:

```text
private-root/
  inputs/<case-id>/       # only whitelisted statement and original attachments
  runs/<case-id>/         # generated project and artifacts
  evidence/<case-id>/     # internal rubric and regression evidence
```

A preparer records only private relative paths and SHA-256 hashes in the private
manifest. It rejects source paths matching output-oriented names and directories,
and it rejects copied files that resolve outside the selected case source.

The 2024 A source directory contains pre-existing generated code, paper, figures,
and publication copies. Treat it as contaminated: prepare its input set only from
the separately whitelisted original statement and attachments; never expose the
rest of that directory to a solving run. If the original attachments cannot be
identified unambiguously, mark the case `blocked` rather than guessing.

## Regression sequence

1. Inventory all 15 cases and create a private manifest with them disabled.
2. Preflight each case: verify its statement, classify attachments, hash copies,
   and identify contamination. Enable only cases with an unambiguous isolated
   input set.
3. Run two diverse calibration cases independently with the invoked Skill. Freeze
   each project before any comparison.
4. Review failures using the five internal dimensions: correctness evidence,
   validation, reproducibility, writing, and visual communication. Promote at
   most three general rules.
5. Implement only rules that are independent of an individual problem's wording,
   data, answer, or model choice. Add public synthetic tests for each rule.
6. Run at least one later unseen case after each rule batch. A regression beyond
   the predeclared private tolerance blocks the release.
7. Continue through the enabled cases. Record blocked cases and limitations but do
   not manufacture input mappings or scores.

## Public Skill changes

Add a reusable private-regression preparation and audit capability that accepts a
user-supplied private root, requires an explicit allow-list, detects contamination
patterns, and produces metadata-free diagnostics. Extend the Skill instructions
to require isolation, a case freeze before learning, a three-rule change cap, and
unseen-case confirmation. Keep the existing public synthetic benchmark as the
only repository-contained benchmark.

## Verification

- Unit-test the preparer with synthetic directories for allow-listing, path escape,
  result-file exclusion, duplicate hashes, and contamination detection.
- Run the preparer in dry-run and execute modes on the private corpus; retain all
  reports outside Git.
- After each public Skill revision, run the repository's full tests, contract
  validation, and the private blinded regression runner.
- Before local sync or GitHub publication, confirm Git has no private corpus path,
  statement text, attachment name, answer, score, or generated private artifact
  staged.
