# CUMCM 2026 executable rules profile

The executable facts in this reference are loaded from
`assets/contest-profiles/cumcm-2026.json`. Update and verify that bundled profile
first when an official source changes; do not maintain a second script-local
copy of dates, URLs, AI branches, or submission limits.

Use this profile only after confirming that the project is governed by the 2026
National College Student Mathematical Modeling Competition rules. Record the
official URLs and access time in `reports/contest_rules_snapshot.md`.

## Locked 2026 calendar and sources

- Competition: 2026-09-10 18:00 through 2026-09-13 20:00,
  `Asia/Shanghai` (74 hours).
- National registration deadline: 2026-09-07 20:00.
- Submission channel: CNKI competition management system; the team performs the
  final upload manually.
- Lock four official `mcm.edu.cn` roles: first notice, paper format, contest
  rules, and AI policy. Save local snapshots and hashes.
- Recheck online at T-30, T-7, and T-1 before the contest. During live work use
  the local lock unless the user explicitly authorizes a refresh.

## Enforced by `verify_submission.py --profile cumcm-2026`

- Electronic paper: one standalone PDF or Word document, at most 20 MB.
- Support package: one ZIP or RAR archive, at most 20 MB when supplied.
- Main text: no table of contents; at most 30 pages, excluding appendices.
  Record the counted main-text pages explicitly because a generic PDF parser
  cannot reliably distinguish appendices.
- Electronic paper starts with the abstract page and excludes the commitment
  and number-only pages. Confirm these by visual inspection.
- Declare exactly one AI branch with `--ai-mode none|used`. `none` requires the
  exact official non-use declaration after the references and forbids conflicting
  AI evidence. `used` requires inline disclosure, an AI-tool reference, and
  `AI工具使用详情.pdf` in the support archive, including tool/version,
  purpose/stage, key interactions, adoption, and human verification or changes.
- Never allow identity, school, or region information in any submitted file.

The profile is a guardrail, not a substitute for the current official rules or
regional notices. If they differ, update the snapshot and use the stricter
requirement.
