# Multi-year CUMCM exemplar-corpus observations

These observations were learned from a local training corpus of 219 excellent
CUMCM papers spanning 2003--2025. They guide paper craft only; they are not
competition-time solution sources and they do not override current official rules.

## What is stable across years

- A strong abstract is an answer map: it names the task, method, key output for
  each question, and at least one validation/robustness finding. It does not only
  announce that models were built.
- The opening pages reduce the statement to a usable problem representation:
  background only as needed, then inputs, conditions, units, deliverables, and
  numbered subproblems.
- The body preserves a reader-visible chain for each subproblem: mechanism or
  decision need, model choice, equations/algorithm, computed result, and practical
  interpretation.
- Assumptions and notation earn their place by simplifying or constraining a later
  model. They are not a disconnected checklist.
- The conclusion answers the original questions explicitly and states where the
  model is robust, uncertain, or limited.

## Figure and table lessons

Use a context schematic only when it makes the physical, spatial, network, or
process mechanism easier to understand. Use data figures for distributions,
correlations, preprocessing, fits, prediction error, sensitivity, scenario change,
or route/network behavior. Use tables for exact parameter values, constraints,
comparisons, and recommendations. Introduce each visual with its claim and follow
it with interpretation; avoid consecutive visuals that repeat the same point.

For multi-question problems, plan at least one evidence-bearing output for every
major answer, but do not force a figure for a purely analytical derivation. In the
appendix, retain code and long intermediate outputs; do not use them to inflate the
main narrative.

## What must not become a rule

Historical papers range widely in page count and layout because rules, archive
formats, and tasks changed. Never copy their page count, title wording, model stack,
equations, numerical results, or visual style as a quota. Current official rules
and the project evidence determine the page budget, format, and required materials.

## Drafting checklist learned from the corpus

Before freeze, ask:

1. Can a judge locate the direct answer to every numbered task in the abstract,
   relevant result section, and conclusion?
2. Does every major figure/table have an explicit claim, a source result, and a
   nearby interpretation?
3. Does every model section explain why the model fits the task before presenting
   calculation detail?
4. Are uncertainty, sensitivity, or failure conditions discussed where a decision
   depends on estimated data or fitted parameters?
5. Could a reader remove any paragraph, figure, or table without losing evidence?
   If yes, remove or consolidate it.
