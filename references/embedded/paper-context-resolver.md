# Paper Context Resolver

Use this module only for narrow literature or reproduction-critical questions.

## Apply When

- A paper, README, or repository leaves a specific gap that affects reproduction or model correctness.
- The gap concerns dataset version, data split, preprocessing, evaluation protocol, checkpoint mapping, method detail, runtime assumption, or a source conflict.
- There is a concrete question to answer.

## Do Not Apply When

- The user only wants a broad paper summary.
- The README or provided source already gives enough detail.
- The task is title-only paper lookup with no concrete modeling gap.
- The goal is to override source instructions without documenting the conflict.

## Output Contract

Record:

- question
- source list
- direct evidence
- inferred conclusion
- conflict note, if sources disagree
- impact on the contest model

## Evidence Rules

- Prefer primary sources: paper, appendix, official code, official dataset documentation.
- Separate direct statements from inference.
- Do not import a method into the contest solution unless it improves the model, validation, or paper explanation.
- Keep literature notes concise; the paper should not become a literature review unless the contest asks for it.
