# LLM-MM-Agent Methodology

This module adapts the usail-hkust/LLM-MM-Agent project as a workflow, not as a runtime dependency.

Source ideas:

- Simulate a human mathematical modeling workflow.
- Convert unstructured contest statements into structured model design.
- Use four stages: problem analysis, mathematical modeling, computational solving, and solution reporting.
- Use HMML-style method retrieval: domain -> subdomain -> method schema.
- Use MLE-Solver-style code iteration: generate, run, inspect, repair, rerun.

## 1. Problem Analysis

Extract:

- background and real-world objective
- subproblem requirements
- known and missing data
- decision variables and parameters
- constraints and evaluation criteria
- necessary assumptions
- dependencies between subproblems

Do not start coding before each subproblem has a clear output and validation target.

## 2. Mathematical Modeling

Select methods through a hierarchy:

1. Domain: optimization, prediction, simulation, evaluation, classification, network, differential equation, game theory, statistical inference, or hybrid.
2. Subdomain: for example multi-objective optimization, time-series forecasting, queueing simulation, entropy-weighted evaluation, graph shortest path, or regression.
3. Method schema: variables, objective, constraints, algorithm, and validation metric.

Compare at least two plausible methods when the route is not obvious. Pick the simplest model that answers the problem and can be explained in the paper.

## 3. Computational Solving

Use an iterative solve loop:

1. Create executable code, notebook, or formula-backed spreadsheet.
2. Load and validate data.
3. Implement the baseline.
4. Run and inspect outputs.
5. Repair errors or weak assumptions.
6. Add sensitivity, robustness, or ablation checks when needed.
7. Rerun and record the result.

## 4. Solution Reporting

Write in the same order as the modeling logic:

- problem and assumptions
- notation
- model derivation
- algorithm or solution process
- results
- validation
- strengths, weaknesses, and sensitivity

The report is not complete until notation, formulas, results, figures, captions, and conclusions are mutually consistent.
