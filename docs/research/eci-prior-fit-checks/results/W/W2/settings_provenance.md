# W2 settings and where each was found

Epoch's code at e04929a (vendored copy `runs/vendor/eci-public`, identical to `ext/eci-public` apart from `.git` and bytecode caches). W2a calls the unmodified `fit_bayesian_eci(df, evaluate=True, random_seed=s, progressbar=False)` with every other argument at its default. The repository states no override for the production run, so the defaults are the only documented settings; whether Epoch's production pipeline uses others cannot be determined from the repository and is not guessed.

| Setting | Value | Where found |
| --- | --- | --- |
| Fit input | published `epoch_capabilities_index/processed_data_for_eci.csv` (2,879 rows) | plan; the loader output differs on 3 rows (W2b) |
| Sampler | NUTS, pilot (diagonal mass matrix, tune 1000, draws 1000) then dense mass matrix (tune 500) | `bayesian.py` constants `_PILOT_TUNE`, `_PILOT_DRAWS`, `_DENSE_TUNE`; README "Sampler" |
| Draws per chain | `None`: adaptive, dense stage 1,000 up to 16,000, then cold stage 4,000 up to 32,000 | `fit_bayesian_eci` signature and docstring; `_DENSE_DRAWS`, `_COLD_DRAWS`; README; `scripts/fit_eci.py --draws` default None |
| Tuning | `None`: 500 dense, 1,000 cold | `fit_bayesian_eci` docstring; `scripts/fit_eci.py --tune` |
| Chains | 4 (one per core) | `fit_bayesian_eci` signature; `scripts/fit_eci.py --chains` default 4 |
| target_accept | 0.95 | signature; `scripts/fit_eci.py --target-accept` |
| Seed | 12345 (plan seeds 22345 and 32345 for the other seeds) | signature; `scripts/fit_eci.py --seed` |
| Internal seeds | pilot seed+1, dense seed+200, rung offsets | `_sample` |
| Convergence checks | zero divergences, r_hat <= 1.01, bulk ESS >= 400 | `_MIN_ESS`, `_MAX_RHAT`, `_ladder` |
| Clip eps | 1e-3 | `performance_clip_eps` default; `build_bayesian_model` |
| Priors | `BayesianPriors()` defaults: tau_alpha, tau_sigma LogNormal(ln 0.5, 0.5); sigma_median LogNormal(ln 0.1, 0.5); flat capability and difficulty (+-50) | `BayesianPriors`, `build_bayesian_model` |
| Anchors | Claude 3.5 Sonnet = 130, GPT-5 = 150 | `DEFAULT_ANCHOR_*` constants |
| Interval | 90% equal-tailed | `ci_level` default |
| Data filters (loader only) | min_date 2023-01-01, min 4 benchmarks and 4 mid-range [0.1, 0.9] per model | `prepare_benchmark_data` defaults (not used for W2a: the published input is already filtered) |
| evaluate | script default off; W2 uses True (plan) | `scripts/fit_eci.py --evaluate` |

Not determinable from the repository: the production run's draws, seed or overrides, and the production data date. G0 is the test of whether the defaults reproduce the published files.
