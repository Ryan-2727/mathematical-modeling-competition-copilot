# CUMCM 2026 executable rules profile

Use this profile only after confirming that the project is governed by the 2026
National College Student Mathematical Modeling Competition rules. Record the
official URLs and access time in `reports/contest_rules_snapshot.md`.

## Enforced by `verify_submission.py --profile cumcm-2026`

- Electronic paper: one standalone PDF or Word document, at most 20 MB.
- Support package: one ZIP or RAR archive, at most 20 MB when supplied.
- Main text: no table of contents; at most 30 pages, excluding appendices.
  Record the counted main-text pages explicitly because a generic PDF parser
  cannot reliably distinguish appendices.
- Electronic paper starts with the abstract page and excludes the commitment
  and number-only pages. Confirm these by visual inspection.
- When AI is used, include `AI工具使用详情.pdf` in the support archive. It must
  state tool/version, purpose/stage, key interactions, adoption, and human
  modification or verification.
- Never allow identity, school, or region information in any submitted file.

The profile is a guardrail, not a substitute for the current official rules or
regional notices. If they differ, update the snapshot and use the stricter
requirement.
