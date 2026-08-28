# Skill hardening design

## Goal

Close the three release-quality gaps found in the 2026-08-28 audit without
changing the mathematical-modeling workflow: Windows rule-lock portability,
deterministic rule-date evaluation, and safe local Skill synchronization.

## Scope

1. Normalize the project root before validating rule snapshot paths. Use one
   effective date for both `valid_through` and freshness-checkpoint checks so
   historical and future-dated tests are deterministic.
2. Add a read-only `-Verify` mode to `scripts/sync_local_skill.ps1`. It checks
   the same 207-file payload that the copy mode uses, reports missing or
   mismatched files, and reports extra files without deleting anything.
3. Add regression coverage for Windows-style temporary paths, an explicit
   effective date, and the synchronization verifier. Keep real contest
   statements, attachments, data, solutions, and papers out of tests.
4. Move the generated project-layout tree from `SKILL.md` into the setup
   reference, leaving the phase routing and all hard workflow rules unchanged.

## Non-goals

- Do not auto-select a contest problem or change the user-confirmation gate.
- Do not weaken privacy, AI-disclosure, paper-delivery, or submission checks.
- Do not delete files from an installation directory.
- Do not upload or publish anything to GitHub as part of this change.

## Verification

- Run the focused rule-lock and synchronization tests.
- Run the Skill contract validator, model-library checks, kernel regression,
  Python compilation, and the complete test suite.
- Run the Skill Creator validator and compare the installed payload hashes with
  the repository payload. Report excluded or extra files separately.
- Inspect the final diff and leave the repository ready for a later explicit
  GitHub push.
