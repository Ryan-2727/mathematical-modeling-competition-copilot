# CUMCM 2026 B/C Readiness and Paper-Gate Design

## Scope

Improve the existing workflow without changing its phase structure or explicit-invocation rule. The change covers:

1. executable 2026 timing and AI-use compliance;
2. targeted B/C model-family coverage;
3. numeric traceability in the abstract and conclusion;
4. reference relevance in addition to reference authenticity; and
5. evidence-based rejection of unjustified model complexity.

Windows-client, account, and first-student manual rehearsals are explicitly out of scope. GitHub publication is also out of scope for this change.

## Design decisions

### One authoritative contest profile

Extend `assets/contest-profiles/cumcm-2026.json` with the MD5 deadline, upload opening time, and upload deadline. The profile loader, rule lock, submission state checks, documentation, and tests consume these fields. The H70-H74 schedule must distinguish local freeze/MD5 work from the later upload window.

### Honest AI and privacy boundary

A live CUMCM 2026 project initialized through this AI skill cannot declare `ai_mode=none`; initialization fixes the branch to `used`. It records the runtime boundary and requires an auditable first AI-use entry. Search remains allowed without lexical filtering, but any action whose privacy effect is unclear remains blocked until the user records a decision. The workflow does not claim to provide an operating-system network interceptor.

The declaration is an ordinary UTF-8 LaTeX source file. A generator may create the starter declaration only when it is absent. Human edits to the purpose text are preserved, while verification protects the mandatory declaration structure and requires a non-empty, non-placeholder purpose.

### Targeted B/C model cards

Add a machine-readable library and a concise human guide for recurring structures observed in 2021-2025 B/C problems:

- response surfaces and designed experiments;
- bearing-only localization and observability;
- coverage path planning;
- sequential tests and decision processes;
- compositional data;
- supply-chain and robust mixed-integer optimization;
- price-demand and assortment optimization;
- longitudinal and interval-censored data; and
- probability calibration and class imbalance.

Every card must define signals, baseline, candidate route, promotion threshold, diagnostics, falsification test, fallback, deliverables, and primary literature. A validator checks completeness and required coverage. The library routes model choice; it is not an instruction to use a complex method automatically.

### Numeric traceability

Every claim-bearing number in the reachable abstract and conclusion must be represented by a generated verified-value macro. A narrowly scoped exemption ledger may cover structural numbers such as question identifiers or calendar years, with a category and reason. Raw unregistered result numbers fail verification.

### Relevant rather than padded literature

The existing minimum of ten verified, cited scholarly works remains. Each row additionally identifies its evidence role, the exact claim it supports, and a reachable paper location. A source with valid metadata but no necessary relationship to a manuscript claim fails; this prevents bibliography padding.

### Complexity promotion gate

The model budget records a comparison metric, direction, baseline value, candidate value, and predeclared minimum improvement. A selected non-baseline route passes only if its measured advantage reaches that threshold and points to a validation artifact. Otherwise the simpler route must remain primary; the complex route may be discussed only as future model optimization or a rejected candidate.

## Verification

- Unit tests cover success and failure cases for every new field and gate.
- Existing orchestration profiles include the new validators without changing phase semantics.
- The complete test suite and skill-contract validator must pass.
- The clean repository copy is then synchronized to the installed local skill and compared semantically.
