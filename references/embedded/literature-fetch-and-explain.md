# Literature Fetch And Explain

This module embeds the practical workflow of `paper-fetch-skill` and `paper-explainer` for mathematical modeling contests.

Use it when literature can improve model choice, parameter setting, validation, or paper credibility. Do not use literature search as a substitute for solving the contest problem.

## Paper Fetch Workflow

1. Define the modeling need before searching:
   - method background
   - parameter range
   - dataset or preprocessing rule
   - evaluation metric
   - comparable case study
2. Prefer primary or authoritative sources:
   - official contest background material
   - peer-reviewed papers
   - arXiv only when peer-reviewed sources are unavailable or the topic is very new
   - official datasets or standards
3. Keep the search narrow. Record:
   - query or source path
   - title
   - authors or organization
   - year
   - DOI, URL, or stable identifier
   - why it matters for the model
4. Reject sources that are only loosely related, inaccessible when evidence is needed, or not useful for a model decision.

## Paper Explanation Workflow

For each useful source, extract only contest-relevant details:

- problem setting
- assumptions
- variables and parameters
- model family
- objective or loss function
- constraints
- data requirements
- evaluation metrics
- limitations
- what can be reused in the contest paper

Then produce a short source note:

```markdown
## Source Note: <title>

- Citation:
- Modeling use:
- Key method:
- Reusable assumptions:
- Parameters or formulas:
- Evidence strength: direct / inferred / weak
- Risk or limitation:
```

## Integration With Paper Context Resolver

Use `paper-context-resolver.md` only after this broader fetch-and-explain step leaves a narrow reproduction-critical gap, such as a dataset split, preprocessing detail, evaluation protocol, checkpoint mapping, or conflicting source claim.

## Citation Discipline

- Never fabricate citations, titles, author names, years, URLs, or formulas.
- Mark uncertain details as uncertain.
- Separate what the paper states from what is inferred for the contest model.
- Every source used in the final paper must support a specific claim, assumption, method choice, parameter, or comparison.
