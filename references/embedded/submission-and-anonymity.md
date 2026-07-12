# Submission and anonymity

## Pre-freeze checks

Run `scripts/anonymity_scan.py --root <submission-root> --out reports/anonymity_scan.txt`
with team/school/region/username terms supplied through repeated `--term` flags.
Review every match; the script is a detector, not proof of anonymity. Check PDF,
Word, image, spreadsheet, notebook, archive, and source-code metadata manually if
the relevant tool is available.

Run `scripts/verify_submission.py` on the final PDF and support archive. Preserve
the generated hash manifest with the submission record.

## Support package

The paper appendix, archive contents, and `submission_manifest.json` must agree.
Include runnable code, non-provided external data, required AI-use documentation,
and long intermediate outputs only when current rules require or permit them. Exclude
cache folders, virtual environments, keys, credentials, editor backups, private
paths, and material that reveals team identity.

Use `scripts/build_support_archive.py` with explicit repeated `--include` paths;
never archive an entire project directory by default.

For CUMCM 2026 with AI use, include `AI工具使用详情.pdf`; render it from the
audit log and inspect it before archiving. Scan final PDF text/metadata, Office
metadata, and archive paths before freezing. An unavailable reader is an
unresolved check, not a pass.

## Copyright and permissions

For each non-team asset, record source, license/permission, exact location of use,
and citation. Redraw or regenerate a visual from licensed/public data when reuse is
not permitted. Do not assume that an online image may be placed in a submission.
