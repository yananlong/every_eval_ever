# F0 against Epoch's `build_bayesian_model` (structural identity, real fit input)

Result: identical. Nothing differs in structure, density or gradient. Evidence: `model_identity.json` (script `runs/lib/identity_check.py`; sensitivity check `runs/lib/identity_mutation.py`).

**Structure.** `runs/lib/models.py` builds F0 without importing Epoch's builder. The description of every free random variable (name, shape, distribution, transform, value variable), the observed variable, the potential, the deterministics and the coordinates is identical to Epoch's on the 2,879-row fit input (256 models, 57 benchmarks):
- tau_alpha, sigma_median, tau_sigma: LogNormal with the same (mu, sigma); log transform.
- sigma: `Truncated(LogNormal(ln sigma_median, tau_sigma), lower 0, upper 0.5)`, one per benchmark; kappa = 1 / (4 sigma^2) - 1.
- capability: Uniform(-50, 50), one per model (interval transform).
- difficulty: Flat with `ZeroSumTransform([-1])` plus the potential that is -inf unless every |difficulty| <= 50.
- log_slope: ZeroSumNormal with sigma tau_alpha * sqrt(K / (K - 1)), K = 57; slope = exp(log_slope).
- mu = clip(sigmoid(slope * (capability - difficulty)), 1e-6, 1 - 1e-6); the observed y = performance clipped to [1e-3, 1 - 1e-3] (the observed arrays are equal); y ~ Beta(mu kappa, (1 - mu) kappa).
- The constants (1e-6, 0.5, 50) equal Epoch's module constants, and the free and diagnostic variable lists equal `_FREE_VARS` and `_DIAGNOSTIC_VARS`.

**Density and gradient.** 300 random points in the unconstrained space (value variables matched by name; offsets of SD 0.1, 0.7 and 1.5 around the initial point), `compile_logp` and `compile_dlogp` (428 unconstrained coordinates):
- max relative difference of logp: 0.0 (requirement 1e-8); of the gradient: 0.0 (requirement 1e-6).
- Per term (each free variable and the observed likelihood, Jacobian included, and the potential as the remainder): max relative difference 0.0 in every term.
- At a point outside the difficulty box both models return -inf.
- The test can fail: a clip of 1e-4 changes logp by 819.5, a tau_alpha prior SD of 0.6 instead of 0.5 by 0.128, and the reference prior by 40,931.

**Anchoring.** F0 is fitted through Epoch's own `fit_bayesian_eci`, so the anchor models, the per-draw anchor transform, the ECI and EDI mapping and the intervals are Epoch's code, not a reimplementation.

**Sampler.** F0 uses Epoch's own sampling routine with our model: `fit_bayesian_eci` is called with `eci.bayesian.build_bayesian_model` replaced in memory by our builder (the mechanism the plan uses for P8 to P10; `models.epoch_with`), so the diagonal pilot, the dense mass matrix, the draw ladder and the cold fallback are Epoch's unmodified code. For expansions the same call is used with `_FREE_VARS` and `_DIAGNOSTIC_VARS` extended in memory for the added variables (a change from the plan's M12 wording; see `runs/deviations.md`).
