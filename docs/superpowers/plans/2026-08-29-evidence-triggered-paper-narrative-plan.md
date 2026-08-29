# Evidence-Triggered Paper Narrative Implementation Plan

## Goal

Implement the approved evidence-triggered paper narrative gate without changing
the Skill's explicit invocation, contest privacy, modeling, LaTeX, or delivery
mechanisms.

## Task 1: Freeze the executable contract with failing tests

Add focused tests for a paper reasoning map and verifier covering:

- required core modeling paths;
- conditional model-comparison obligations;
- literature, data-calibrated, assumed, and official parameter sources;
- evidence-bound failed routes;
- boundary-sensitive claims;
- human review;
- non-triggered alternatives and failures that must not be fabricated.

Add style-checker tests for repetitive paragraph openings, mechanical
transitions, generic model praise, and the prohibition on AI-authorship labels.

Verification: run the focused tests and confirm they fail for the missing
implementation.

## Task 2: Implement the narrative evidence gate

Add `scripts/verify_paper_reasoning_narrative.py` and initialize
`reports/paper_reasoning_map.csv`. Reuse existing model, parameter, failure, and
claim ledgers by ID and safe project-relative locators. Do not duplicate result
values or generate paper prose.

Integrate the verifier into the paper verification graph and the Skill contract.

Verification: focused verifier tests pass for triggered and non-triggered cases.

## Task 3: Extend advisory Chinese prose review

Extend `scripts/verify_chinese_academic_style.py` with located advisory findings
for repetitive openings, mechanical transitions, generic praise, and unsupported
universal scope. Keep the tool advisory by default and never emit an
AI-authorship verdict or rewrite text.

Verification: existing and new style tests pass; a natural fixture is not forced
to use fixed headings.

## Task 4: Route the behavior without duplicating instructions

Update the smallest necessary set of owners:

- concise routing in `SKILL.md`;
- detailed paper behavior in result-first, paper-depth, paper-writing, and
  evidence-gate references;
- workflow map and contract;
- LaTeX template comments;
- English README mirror and Chinese README.

Verification: Skill line budget, README mirror equality, link scan, contract
validation, and Skill quick validation pass.

## Task 5: Full regression, commit, and local installation sync

Run the full unit suite, Python compilation, model-library validation, standard
library kernel regression, diff checks, and installation payload verification.
Commit only scoped changes, synchronize the tracked payload to the local Skill
directory without deleting extra files, then run read-only hash verification.

Do not push GitHub unless the user explicitly requests it after completion.
