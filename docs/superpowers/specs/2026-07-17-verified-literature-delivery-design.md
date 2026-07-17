# Verified literature and two-part delivery design

## Goal

Make a completed contest paper fail verification unless it has at least ten
unique, real, source-checked scholarly references that are actually cited in
the LaTeX source, plus two explicit deliverables: the compiled paper with its
LaTeX source and a reproducible support-material package containing code and
data evidence.

## Chosen approach

Use a bibliography evidence ledger and a deterministic package verifier.
Prompt-only rules are insufficient because they cannot detect invented or
uncited references. Direct Google Scholar automation is not a reliable sole
validator because access may be unavailable or rate-limited. Instead, each
reference must be checked against authoritative metadata such as a publisher
page, DOI/Crossref, or OpenAlex, and must also record an exact-title Google
Scholar query that a human can reproduce.

## Artifacts and data flow

1. `reports/bibliography.csv` records citation key, bibliographic metadata,
   authoritative verification source and time, exact-title Scholar query,
   supported claim and source locator, and status.
2. `paper/main.tex`, included section files, and `paper/references.bib` form the
   source of the paper. `paper/main.pdf` must be produced by an actual LaTeX
   build; a source-only draft is not a completed paper.
3. `support/README.md` explains reproduction. `support/materials_manifest.csv`
   inventories code, data, environment, commands, results, figures, licenses,
   and SHA-256 values. If raw data cannot legally be redistributed, the package
   contains its official retrieval URL, version, license, hash and retrieval
   script; generated or processed inputs remain included when allowed.
4. `scripts/verify_paper_delivery.py` cross-checks unique LaTeX citation keys
   against BibTeX and the ledger, enforces the ten-reference minimum, rejects
   incomplete verification rows, requires a non-empty PDF and LaTeX source,
   and checks the support manifest and hashes.

## Failure behavior

The verifier fails closed. Missing metadata, fewer than ten unique cited
sources, unsupported citation keys, nonexistent support files, hash mismatch,
or absent code/data evidence blocks the completion claim. A structural pass is
not a semantic guarantee: the workflow still requires human reading of each
source and forbids attributing a claim that the source does not support.

## Testing

Add one passing fixture with ten cited BibTeX entries and a complete support
manifest, plus failures for fewer than ten citations, missing source evidence,
and support-file hash mismatch. Retain all existing tests and the explicit
invocation contract.
