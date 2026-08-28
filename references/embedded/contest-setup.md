# Contest Setup

Use this phase to turn an open-ended contest request into a controlled project.

## Required Questions

Ask only questions that materially affect the workflow:

- Contest type: MCM/ICM, CUMCM, Huawei Cup, school contest, or other.
- Submission language: Chinese, English, or contest-mandated format.
- Paper format: DOCX, PDF, LaTeX, Typst, or unknown.
- Time budget and deadline.
- Available data and whether external data is allowed.
- Team roles, if the user wants division of work.
- Known subproblem count, if the statement makes it obvious.
- Operating mode: training, live contest, or post-hoc review.
- Official rules URL/version, deadline time zone, AI disclosure requirement, and submission/hash procedure.

If the user provides the problem statement and deadline, proceed with reasonable defaults instead of blocking on minor preferences.

## Embedded Brainstorming Gate

Before committing to a model route, generate a small option set instead of picking the first plausible method:

- list at least one simple baseline model
- list one stronger model if the data and time budget support it
- identify which assumptions each option needs
- state what evidence would make an option fail
- choose the route that is easiest to verify under the deadline

Keep this brainstorming bounded. Do not expand into speculative features, extra deliverables, or unrelated methods.

## Required Artifacts

Create or update:

- `plan.md`: scope, assumptions, phase plan, deliverables, risks.
- `todo.md`: phase checklist and status.

Recommended `todo.md` structure:

```markdown
# Todo

- [ ] 1. Contest setup and strategy
- [ ] 2. Problem analysis and model design
- [ ] 3. Literature and reproduction details
- [ ] 4. Computation and experiments
- [ ] 5. Figures, tables, and diagrams
- [ ] 6. Paper writing
- [ ] 7. Final verification
```

Update `todo.md` after each phase. Do not leave status stale.

## Generated Project Layout

`scripts/init_contest.py` is the tested authority for the generated layout.
Preserve an existing structure; otherwise maintain at least:

```text
.
|-- contest_manifest.json
|-- rules.lock.json
|-- plan.md
|-- todo.md
|-- data/{raw,processed}/
|-- code/
|-- results/verified_values.csv
|-- figures/
|-- reports/                 # phase evidence and generated gate reports
|-- environment/
|-- support/materials_manifest.csv
|-- support.zip
|-- paper/{main.tex,references.bib,sections,generated,figures,build,main.pdf}
|-- delivery/                # complete user handoff
`-- official-submission/     # selected-profile files only
```

## Setup Quality Gate

Before modeling starts:

- The contest problem statement is available or the missing statement is explicitly requested.
- Submission requirements are known or marked unknown.
- Data availability and external-data policy are recorded.
- Current contest rules are snapshotted and critical compliance fields are verified.
- In live mode, allowed source classes and prohibited interactive/discussion sources are recorded before any web research.
- The project artifact layout is created or mapped to an existing structure.
