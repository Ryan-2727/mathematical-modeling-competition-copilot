# Problem-structure playbooks

Choose a playbook from the requested decision, explanation, or prediction. Each
playbook is a reasoning skeleton, not a mandatory model list.

## Evaluation and ranking

Define the decision maker and alternatives; justify indicator direction and
scale; expose weight provenance; compare at least one weighting baseline; test
rank stability; end with a recommendation and the conditions under which it
changes.

## Forecasting

Define forecast horizon and information available at prediction time; prevent
leakage; compare a naive or simple statistical baseline; use chronological
backtesting; report uncertainty and failure regimes; connect forecasts to the
decision requested by the problem.

## Optimization and scheduling

Derive variables, objective, and each constraint from the mechanism; validate a
small instance independently; report feasibility, solver status, gap or lack of
global guarantee; perturb scarce resources and costs; translate the solution
into an implementable schedule or policy.

## Mechanistic dynamics

State conservation, causality, or transition mechanisms; check dimensions;
identify parameter sources and identifiability limits; calibrate separately from
validation; test initial/boundary conditions and numerical convergence; explain
what intervention the dynamics support.

## Physical measurement and inverse problems

Read `physics-inverse-modeling-playbook.md`. Map observable data to a latent
quantity through an explicit observation equation; begin with an identifiable
proxy, then add material, calibration, boundary, absorption, or multi-path
mechanisms only when a predeclared diagnostic supports promotion. Separate
shared, condition-specific, and nuisance parameters; compare separate and joint
fits; pair the global fit with a genuinely independent local, algebraic, or
alternative-representation estimate when feasible.

## Classification, clustering, and statistical explanation

Define the target or similarity meaning; separate preprocessing fitted on train
data; report class imbalance and leakage checks; compare an interpretable
baseline; use suitable out-of-sample metrics; distinguish association from
causation; explain errors and unstable segments.

## Simulation and stochastic systems

Justify distributions and dependence; fix seeds; report replications and Monte
Carlo uncertainty; check warm-up or steady-state assumptions; compare analytic
or simplified cases; turn distributions into risk-aware decisions rather than
only mean values.
