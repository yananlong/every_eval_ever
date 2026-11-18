# W2 summary: fit, reproduction and the equivalence check

Gate G0: **passed** (reproduction and convergence). Equivalence check EQ: **passed**, with exact agreement. Details in `reproduction.json`, `model_identity.md`, `settings_provenance.md`, `epoch_sampler_summary.csv`.

## W2a: Epoch's unmodified `fit_bayesian_eci` on the published fit input (defaults, `evaluate=True`)
All three seeds converged at the first rung of the pilot-then-dense stage (1,000 draws per chain, 4 chains, no cold fallback), about 2.4 to 3.2 minutes each.

| Seed | Divergences | max r_hat | min bulk ESS | min tail ESS | min BFMI |
| --- | --- | --- | --- | --- | --- |
| 12345 | 0 | 1.0043 | 1,076 | 1,307 | 0.879 |
| 22345 | 0 | 1.0032 | 1,228 | 1,537 | 0.836 |
| 32345 | 0 | 1.0052 | 1,287 | 1,317 | 0.817 |

G0 reproduction criteria, seed 12345 against the published `eci_scores.csv`:
- Largest absolute difference in ECI, non-anchor models: 0.420 points (tolerance max(0.5, 0.07 W) per model: 0 of 254 models exceed it; largest difference as a share of the published width: 0.019).
- Spearman over 256 models: 0.999993 (required 0.999).
- Median width ratio 0.9955 (required in [0.95, 1.05]); 100% of the 254 ratios in [0.85, 1.15] (required 95%).
- Reported: max absolute EDI difference 0.767; max scaled-slope difference 0.0013; seed-to-seed SD of posterior-mean ECI at most 0.248; the nine top-10 adjacent-pair probabilities (ours against published) are in `reproduction.json` (for example 0.9975 against 0.996, 0.7295 against 0.748, 0.713 against 0.702).

Settings: the repository states no production override; the defaults are the only documented settings (`settings_provenance.md`).

## W2b: loader input (`prepare_benchmark_data`), seed 12345
The same 2,879 keys; three scores differ (GPQA diamond: Claude Fable 5 0.845 published against 0.957 loader, Claude Fable 5.2 0.957 against 0.986, Claude Opus 5.5 0.911 against 0.959). Converged. Against W2a: S1 Spearman 0.99998 (all), 1.0 (frontier), 0.99977 (sparse); S2 and S3 counts 0 in every stratum; S4 top-10 set unchanged, max adjacent-pair change 0.023. Reported only, not gated.

## EQ (M12): our F0 against Epoch's fit
- Structure and density (`model_identity.md`): identical on every term; at 300 random unconstrained points the largest relative difference of logp and of the gradient is 0.0, and the density at 20 posterior draws agrees exactly (requirement 1e-6).
- Fit, seeds 12345 and 22345: our F0 was fitted by Epoch's own routine with our builder swapped in; the posterior draws are bit-identical to Epoch's (maximum ECI difference 0.0, Spearman 1.0, width ratio 1.0).
- Prediction: elpd_loo 3449.963 (ours) against 3449.963 (Epoch's), difference 0.000 (limit 2); seed 22345 3450.452 against 3450.452. SE 56.7, p_loo 442.6.

Deviation: F0 and later models use Epoch's sampler routine, not our own call (`runs/deviations.md`, item 1).
