# Skill Deduplication and Maintainability Design

## Goal

Reduce duplicated instructions, context cost, and maintenance drift in the
mathematical-modeling competition skill without changing its principal
behavior, phase order, explicit-invocation rule, user approval points,
verification semantics, or two-part delivery contract.

The refactor must preserve every existing contest capability. A shorter entry
file is successful only when each removed detail remains reachable through a
directly named reference, executable profile, script, or generated project
artifact.

## Non-negotiable invariants

Preserve all of the following:

- explicit invocation only;
- phases 0 through 12 in their current order;
- current-problem privacy and online-action approval boundaries;
- H6 problem audition and 8/24/48/74-hour CUMCM 2026 rehearsals;
- baseline, competing model, refutation, uncertainty, causal, fallback, and
  implementability requirements;
- verified literature and passage evidence, including the ten-source minimum;
- result-first abstract and complete per-subproblem argument chains;
- portable XeLaTeX/latexmk output for Overleaf and VS Code;
- optional award review only after paper completion and explicit user consent;
- distinction between structural verification and mathematical truth;
- separate complete user delivery and contest-limited official submission;
- compiled PDF plus rebuildable LaTeX and verified support-material delivery.

Existing validator status meanings and pass/fail conditions must remain
unchanged unless a test exposes an existing contradiction. Any such
contradiction must be documented rather than silently reinterpreted.

## Selected approach

Use a bounded structural refactor rather than a textual-only cleanup or a full
validator rewrite.

1. Make the CUMCM 2026 profile machine-readable and authoritative for duplicated
   dates, source URLs, AI branches, and submission fields. Existing scripts
   consume the same values through a small loader. Documentation retains human
   explanations and is checked against the profile.
2. Reduce `SKILL.md` to the core phase router, mandatory outputs, hard gates,
   and conditional reference links. Move repeated command lists and detailed
   checklists to existing references. Keep the file comfortably below 500
   lines.
3. Replace the manually exhaustive artifact tree with a clearly labelled core
   layout. Treat `init_contest.py` and its tested manifest as the complete
   generated layout.
4. Clarify paper-reference responsibilities. Do not remove capabilities or
   optional-review consent gates. Retain compatibility files when removing them
   would break existing links.
5. Add navigation to long references and merge duplicate workflow-map entries.
6. Extract only stable script primitives such as safe path resolution, hashing,
   CSV loading, and JSON report writing when tests prove exact equivalence.
   Do not centralize validator-specific business rules.
7. Move repeated contract inventory into a machine-readable manifest while
   preserving the current contract checks and output format.
8. Keep the English homepage and Chinese README switch. Add an automated check
   preventing `README.md` and `README.en.md` from drifting while both files
   remain present.

## Architecture and data flow

### Contest profile

Store the CUMCM 2026 profile under a bundled data directory suitable for direct
script loading. The profile includes a schema/version field and only facts that
are currently duplicated. A loader resolves the bundled path independently of
the contest project working directory and returns immutable profile data.

`init_contest.py`, `verify_submission.py`, and rule-lock helpers read that
profile. Markdown references describe the same rules but do not become an
alternative executable source. Contract tests compare documented key values
with the profile.

### Skill entry and references

`SKILL.md` remains the only operational entry point. Each phase names the
reference files required for that phase directly. The entry states what must be
produced and which gate controls progress, while detailed fields and command
sequences live in the named reference.

Long references receive a compact contents list when this improves navigation.
Files with related themes retain one clear owner for each rule: writing,
presentation, compilation, or final verification. Compatibility routers may
point to the owner but must not restate the rule in full.

### Scripts and contract inventory

Shared helpers remain deliberately small and dependency-free. Existing command
line interfaces, report paths, report schemas, status values, and exit codes
remain stable. A contract manifest lists required resources and capability
markers; `validate_skill_contract.py` validates the manifest and the Skill
instead of repeating file inventories in several Python collections.

## Error handling and compatibility

- Missing or invalid bundled profile data fails closed with a clear error.
- Existing initialized contest projects remain readable; no migration may
  overwrite user work.
- Existing direct script invocations and arguments remain supported.
- Existing reference paths remain valid unless a compatibility file is left in
  place.
- No report may be edited or synthesized merely to satisfy a gate.
- No file outside the repository and explicitly synchronized installed Skill
  copies is removed.

## Verification and success criteria

The refactor is complete only when all of the following hold:

1. `SKILL.md` is below 400 lines and every invariant above remains represented
   by an entry rule, a direct phase reference, and/or an executable gate.
2. CUMCM 2026 executable facts have one machine-readable source and profile
   parity tests pass.
3. All references named by routers are discoverable; long-reference navigation
   checks pass.
4. Existing unit and regression tests pass without weakening assertions.
5. Skill contract validation and the system Skill quick validator pass.
6. README language-switch links work and English mirror parity is tested.
7. A before/after capability matrix shows no removed phase, report family,
   validator, user approval point, or delivery requirement.
8. Source and installed Skill copies have identical tracked-file hashes after
   synchronization.
9. The final worktree diff contains only files traceable to this design.

GitHub publication is not part of this design unless the user requests it after
local verification.
