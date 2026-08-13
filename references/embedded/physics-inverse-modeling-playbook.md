# Physical measurement and inverse-modeling playbook

Load this playbook only when observations arise from a physical measurement
process and the requested quantity is latent, indirect, or jointly calibrated.
Use the general reasoning kernel first.

## Contents

- [1. Declare the inverse problem](#1-declare-the-inverse-problem)
- [2. Build the forward observation chain](#2-build-the-forward-observation-chain)
- [3. Create a physics candidate ladder](#3-create-a-physics-candidate-ladder)
- [4. Separate parameter roles](#4-separate-parameter-roles)
- [5. Establish estimability](#5-establish-estimability)
- [6. Construct an independent route](#6-construct-an-independent-route)
- [7. Diagnose before increasing fidelity](#7-diagnose-before-increasing-fidelity)
- [8. Report only supported physics](#8-report-only-supported-physics)

## 1. Declare the inverse problem

State the target quantity, measurement axes, controls, acquisition conditions,
units, resolution, calibration information, and plausible error sources. Draw
the direction explicitly:

`physical state -> mechanism -> instrument/observation process -> recorded data`

Model in the forward direction and invert only after checking whether different
latent states can generate indistinguishable observations. Do not mistake a
visually regular signal for direct observation of the target.

## 2. Build the forward observation chain

Start from the smallest defensible chain:

1. define geometry, boundary conditions, and conservation relations;
2. define the latent physical state and target parameter;
3. map the state through the core propagation or response mechanism;
4. add the material/constitutive relation required by the measured range;
5. add instrument scale, offset, resolution, calibration, and noise;
6. transform the model into the exact domain and sampling grid of the data.

Verify units and limiting cases at every link. Preserve raw-domain and
transformed-domain conventions; an FFT, derivative, smoothing step, or peak
detector changes the observation model and error structure.

## 3. Create a physics candidate ladder

Use a nested ladder rather than starting with the highest-fidelity formula:

- `P0`: dimensional, periodic-feature, invariant, or closed-form estimate;
- `P1`: minimal forward model with fixed or simple constitutive quantities;
- `P2`: condition-dependent constitutive relation or calibrated observation;
- `P3`: coherent interaction, multiple path, coupling, loss, or resonance term;
- `P4`: full joint model across measurement conditions.

Treat empirical constitutive laws, carrier/resonance corrections, and coherent
multi-path responses as candidate mechanism families, not mandatory formulas.
Choose them from the material regime, measurement band, and observed defect.

For each upgrade, predeclare the residual or external inconsistency it should
remove. Compare nested candidates using an interpretable metric, parameter
stability, and physical plausibility. Reject an upgrade that only reduces
in-sample error by absorbing noise or calibration bias.

## 4. Separate parameter roles

Partition the forward model as shared physical parameters, condition-specific
physical parameters, and nuisance parameters.

- Share a target across angles, frequencies, sensors, or trials only when the
  same specimen/system and mechanism justify it.
- Vary parameters that represent true changes in state or boundary condition.
- Keep scale, baseline, phase offset, calibration drift, and noise parameters
  condition-specific unless evidence supports sharing.
- Fix external material constants only with a source, range, and sensitivity
  analysis; do not estimate every constant from one limited signal.

Compare separate fits with joint fits. Use systematic condition-level residuals
to detect an invalid sharing assumption. Prefer partial pooling or a stated
range when exact sharing and full separation are both unsupported.

## 5. Establish estimability

Before nonlinear inversion:

- derive observable parameter combinations and dimensionless groups;
- check whether amplitude, phase, scale, baseline, and target parameters trade
  off under the sampling range;
- inspect sensitivity/Jacobian rank and parameter profiles;
- use synthetic recovery at realistic noise and resolution;
- use multi-start fits to expose local modes, not to prove uniqueness;
- compare information gained by each measurement condition.

Apply `PASS`, `CONDITIONAL`, or `FAIL` from `model-reasoning-kernel.md` to each
reported physical parameter. On `CONDITIONAL`, fix or bound weak parameters and
propagate that choice. On `FAIL`, report an identifiable combination, interval,
or experiment-design need instead of a fabricated point estimate.

## 6. Construct an independent route

Use one global/generative route as the primary inversion and, when feasible,
one local, algebraic, spectral, invariant-based, or differently represented
route as a check. The routes must differ in at least two of:

1. mathematical principle;
2. data representation;
3. dominant failure mode.

Using the same objective with a different optimizer checks algorithm stability;
it is not an independent estimator. Using a feature method only to initialize a
global fit is not independent unless its standalone result is retained and
compared with a predeclared tolerance.

If no independent estimator is feasible, record why and combine at least two
other checks such as synthetic recovery, an invariant, a calibration standard,
or held-condition prediction. Preserve the remaining limitation.

## 7. Diagnose before increasing fidelity

Link each candidate mechanism to a testable signature:

| Observed defect | Investigate before upgrading |
|---|---|
| Structured oscillatory residual | sampling/phase alignment, omitted path or interaction |
| Condition-dependent bias | invalid sharing, calibration drift, missing state dependence |
| Amplitude mismatch with stable phase | scale/loss/instrument response before new target physics |
| High parameter correlation | reparameterization, wider conditions, or fixed external constant |
| Boundary-hitting parameters | unit/domain error, weak information, or wrong mechanism |
| Local feature and global fit disagree | indexing, preprocessing, resolution, nuisance terms, identifiability |

Run residual plots in the native and useful transformed domains, parameter
profiles/correlations, subrange stability, condition holdout, plausible
calibration perturbations, and synthetic recovery. Use finer discretization or
more complex physics only when its predicted signature is present.

## 8. Report only supported physics

In the paper, show the forward chain, candidate progression, parameter-sharing
logic, identifiability boundary, independent route, decisive diagnostics, and
reason for accepting or rejecting higher fidelity. Keep internal audit detail
in support files, but expose enough evidence for the reader to reconstruct the
decision.

Do not:

- call a numerical solver a physical mechanism;
- call ordinary nonlinear fitting machine learning without a relevant reason;
- infer microscopic parameters unsupported by the measurement range;
- discard resonance, edge, or anomalous regions without a physical and
  sensitivity-based justification;
- average conflicting estimates to hide model disagreement;
- report more precision than calibration, identifiability, and uncertainty
  permit.
