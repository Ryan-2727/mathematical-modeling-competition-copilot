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
- Final paper MD5 generation/submission deadline: 2026-09-13 20:00.
- Official paper/support upload window: 2026-09-13 20:30 through
  2026-09-14 14:00. Do not report a receipt before the window opens.
- Submission channel: CNKI competition management system; the team performs the
  final upload manually.
- Lock four official `mcm.edu.cn` roles: first notice, paper format, contest
  rules, and AI policy. For each role save the official index locator, article
  page, and attachment PDF with local snapshots and hashes.
- Recheck online at T-30, T-7, and T-1 before the contest. During live work use
  the local lock unless the user explicitly authorizes a refresh.

## Enforced by `verify_submission.py --profile cumcm-2026`

- Paper version sequence: page 1 is the commitment form, page 2 is the
  number-only page, page 3 is the abstract-only page, and main text begins on
  page 4. The abstract is normally no more than one page. The electronic paper
  starts from the abstract and therefore excludes the first two administrative
  pages.
- Electronic paper: one standalone PDF or Word document, at most 20 MB.
- Support package: one ZIP or RAR archive, at most 20 MB when supplied.
- Main text: do not create a table of contents or a separate contents page;
  count no more than 30 main-text pages, excluding appendices. Appendices have
  no page limit. Do not misread the 30-page limit as a total-PDF limit. Record
  the counted main-text pages explicitly because a generic PDF parser cannot
  reliably distinguish appendices.
- Page planning: treat 30 pages as a hard ceiling, not a target. For a normal
  CUMCM paper, plan about 20--25 main-text pages unless task complexity supports
  a shorter paper or genuinely requires approaching 30. Prefer information
  density, complete reasoning, effective figures, and model validation over
  filler, smaller type, or duplicated prose.
- Electronic paper starts with the abstract page and excludes the commitment
  and number-only pages. Confirm these by visual inspection.
- The profile verifier supports exactly one AI branch with `--ai-mode
  none|used`; a live project invoking this AI skill must use `used`. Put the official
  `AI工具使用声明` before the references. `none` requires the exact 2026 non-use
  declaration and forbids conflicting AI evidence. `used` requires the exact
  use-declaration pattern with a non-empty purpose and `AI工具使用详情.pdf` in the
  support archive, including tool/version, purpose/stage, principal prompting or
  process description, adoption, and human review, modification, or verification.
- Never allow identity, school, or region information in any submitted file.

The profile is a guardrail, not a substitute for the current official rules or
regional notices. If they differ, update the snapshot and use the stricter
requirement.
