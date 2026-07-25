# Verified Literature and Two-Part Delivery

Use this playbook whenever the skill is expected to produce a completed paper.
It is a hard completion gate, not a suggestion.

## Ten-source minimum

- Cite at least 10 unique, relevant scholarly works in the LaTeX body. Do not
  inflate the count with irrelevant papers, duplicate versions, home pages,
  generic web articles, or uncited bibliography entries.
- Verify bibliographic metadata against an authoritative record: the publisher,
  DOI/Crossref, OpenAlex, the journal or conference, or another official source.
- Also save a reproducible Google Scholar exact-title query URL for every work.
  Scholar discovery alone is not enough to establish metadata or source content.
- Read the abstract and the relevant full-text section when available. Record the
  exact claim the source supports and a page, section, equation, table, or other
  locator. If only an abstract is accessible, limit the attributed claim to what
  the abstract actually establishes.
- Never invent a title, author, venue, year, DOI, method detail, finding, quotation,
  page number, or source locator. A plausible-looking BibTeX entry is not evidence.
- In live-contest mode, literature may support general methods and domain facts,
  but current-problem discussions, posted solutions, shared code, and interactive
  answer sources remain prohibited.

Maintain `reports/bibliography.csv` with these fields:

```text
citation_key,title,authors,year,venue,doi_or_url,verification_source,verified_at,scholar_query,scholar_checked_at,scholar_status,metadata_snapshot,metadata_sha256,retraction_status,retraction_checked_at,claim_supported,source_locator,supporting_passage,supporting_passage_sha256,status
```

Set `scholar_status` to `found` only after the exact-title result has been observed,
and record the check date. Only mark the row `verified` after the metadata check,
Scholar result, and source-content check are complete. Keep citation keys identical
in the ledger, the LaTeX citation commands, and `paper/references.bib`.

Save authoritative metadata responses under `reports/bibliography_metadata/` and
short copyright-compliant claim-supporting excerpts or precise evidence notes
under `reports/source_passages/`.
Set `verification_source` to the record-specific HTTPS Crossref, DOI, or OpenAlex
URL that matches the saved metadata; labels such as `official` are not evidence.
Use the canonical `https://scholar.google.com/scholar?q=...` URL for the exact-title
Scholar check. Record all evidence SHA-256 values. Run
`scripts/verify_bibliography_metadata.py --project-dir . --out
reports/bibliography_verification.json`. Its pass verifies saved evidence
integrity and metadata agreement; it does not establish that a source was
interpreted correctly.

## Paper deliverable

The first final deliverable contains both:

- `paper/main.pdf`, compiled from the frozen LaTeX source; and
- `paper/main.tex`, every included `.tex` file, `paper/references.bib`, figures,
  tables, class/style files, and any local assets required to rebuild the PDF.

Use BibTeX or Biber consistently with the selected template. A typical build is:

```powershell
Push-Location paper
xelatex -interaction=nonstopmode -halt-on-error -file-line-error main.tex
biber main  # use bibtex main instead when the template selects BibTeX
xelatex -interaction=nonstopmode -halt-on-error -file-line-error main.tex
xelatex -interaction=nonstopmode -halt-on-error -file-line-error main.tex
Pop-Location
```

Do not call the paper complete when only `.tex` exists or when compilation has
unresolved citations, missing graphics, placeholders, or fatal errors. Render the
PDF and inspect page order, clipping, font substitution, captions, tables, and
anonymity whenever the PDF runtime is available.

## Support-material deliverable

The second final deliverable is `support.zip`. It must contain:

- runnable code, scripts, or notebooks;
- data permitted for redistribution, plus generated/processed inputs needed for
  reproduction; when raw data cannot legally be redistributed, include an official
  retrieval URL, license, version/date, expected hash, and retrieval command;
- environment or dependency evidence;
- exact commands in `support/reproduction_commands.txt`;
- representative result/output evidence used by the paper;
- `support/README.md`, `support/materials_manifest.csv`, and
  `support/data_inventory.csv`.

Every included artifact needs a source, license/permission, SHA-256 value, category,
and purpose. Never package credentials, private paths, caches, virtual environments,
copyrighted data without permission, or identity-revealing metadata.

This is a user delivery artifact, not automatically an official submission
artifact. Put the portable paper source and support archive under `delivery/`.
Put only files allowed by the selected official profile under
`official-submission/`, then run `scripts/verify_delivery_profiles.py`. In
particular, do not submit a separate support archive to MCM/ICM.

Build the archive from its allow-list rather than archiving the whole project:

```powershell
python scripts/build_support_archive.py --project-dir . --materials-manifest support/materials_manifest.csv --out support.zip --manifest support_manifest.json
```

## Completion gate

Run this after the PDF and support archive are frozen:

```powershell
python scripts/verify_paper_delivery.py --project-dir . --out reports/paper_delivery.json
```

A failure blocks the completion claim. A pass proves only that the recorded
structure, cross-references, archive membership, and hashes satisfy this contract.
It cannot prove that a paper is mathematically correct or that source content was
described honestly; a human must still read the cited passages and inspect the PDF.
