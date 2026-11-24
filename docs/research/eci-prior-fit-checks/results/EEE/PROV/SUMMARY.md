# Provenance resampling on EEE (exploratory, beyond plan)

Results hold under Epoch's model. Each refit keeps Epoch's 2,879 cells and Epoch's input columns; only `performance` changes, in the 688 covered cells (cells with at least one EEE source). Fit: Epoch's unmodified `fit_bayesian_eci` through `lib.fit_any.run`, seed 12345, Epoch's priors, 4,000 draws per chain, retry ladder and 2 h cap as BSEL. Reference fits: P0 (Epoch data) and the deterministic EEE fit (runs/EEE/W5/P0, highest score in the preferred class per cell).

Crosswalk on EEE manifest 959f0e11 (rev 5bce4753); main at 27d78eef (manifest 0a760ce1, +303 records) would add about 2 cells; not rebuilt.

The crosswalk's third audit sample (seed 20261115, 0 errors in 50) is accepted as a recorded deviation in runs/EEE/PROGRESS.md and is not repeated here.

## Design

- R (Epoch's value or any EEE source): 50 refits, RNG base seed 2026112100 (replicate j uses default_rng(base + j)); 688 cells have a pool, 688 have a real choice, 481 of those with distinct values; on average 216 cells differ from Epoch's value by more than 0.0015.
- I (independent sources only): 20 refits, RNG base seed 2026112200 (replicate j uses default_rng(base + j)); 280 cells have a pool, 120 have a real choice, 118 of those with distinct values; on average 265 cells differ from Epoch's value by more than 0.0015.
- O (own-run sources only): 20 refits, RNG base seed 2026112300 (replicate j uses default_rng(base + j)); 295 cells have a pool, 99 have a real choice, 99 of those with distinct values; on average 236 cells differ from Epoch's value by more than 0.0015.

Epoch's value counts as one entry of the R pool even where a same-upstream source copies it, so same-upstream copies raise its weight. Per source the highest score in the cell is used. Design file: design.json (pool values, sources, per-replicate draw strings).

## Convergence

| Variant | Converged | Max divergences | Max R-hat | Min ESS | Fits needing a retry |
|---|---|---|---|---|---|
| R | 50 of 50 | 0 | 1.0017 | 4917 | 0 |
| I | 20 of 20 | 0 | 1.0014 | 5354 | 0 |
| O | 20 of 20 | 0 | 1.0015 | 4460 | 0 |


Epoch's inclusion rule (as applied by its data loader, not inside the fit) would drop no model in any refit.

## Provenance spread of the posterior-mean ECI (non-anchor models, converged replicates)

| Variant | Stratum | Largest SD (model) | Its 90% width | SD / width | SD / 0.25 | Largest SD / width over models (model) | Models with SD above 0.25 |
|---|---|---|---|---|---|---|---|
| R | all | 4.27 (Cerebras-GPT-13B) | 38.0 | 0.112 | 17.1 | 0.339 (o1-preview) | 145 of 254 |
| R | frontier | 0.38 (Claude Fable 5.2) | 7.7 | 0.050 | 1.5 | 0.067 (Claude Opus 5) | 13 of 20 |
| I | all | 2.03 (Gemma 2 9B) | 9.8 | 0.208 | 8.1 | 0.212 (Gemma 4 26B A4B) | 70 of 254 |
| I | frontier | 0.13 (Claude Fable 5.2) | 7.7 | 0.017 | 0.5 | 0.017 (Claude Opus 5.5) | 0 of 20 |
| O | all | 1.41 (Yi 6B) | 20.3 | 0.069 | 5.6 | 0.139 (Gemma 4 26B A4B) | 46 of 254 |
| O | frontier | 0.11 (Claude Fable 5.2) | 7.8 | 0.014 | 0.4 | 0.014 (Claude Fable 5.2) | 0 of 20 |

Median per-model SD: R 0.30; I 0.11; O 0.08. The 0.25 reference is the largest seed-to-seed SD on Epoch data (W2, 3 seeds); 0.29 on EEE data. The refits share one fit seed, so the provenance SD also contains sampler noise of at most that size.

## Top 10 and frontier

- R: 1 distinct top-10 set(s); 0 of 50 differ from P0's set, 0 from the deterministic EEE fit's set. Frontier-20 adjacent gaps: largest SD 0.23, median SD 0.045; 3 adjacent pair(s) ever flip order; SD of the rank-1 minus rank-20 stretch 0.20.
- I: 1 distinct top-10 set(s); 0 of 20 differ from P0's set, 0 from the deterministic EEE fit's set. Frontier-20 adjacent gaps: largest SD 0.03, median SD 0.012; 1 adjacent pair(s) ever flip order; SD of the rank-1 minus rank-20 stretch 0.08.
- O: 1 distinct top-10 set(s); 0 of 20 differ from P0's set, 0 from the deterministic EEE fit's set. Frontier-20 adjacent gaps: largest SD 0.03, median SD 0.015; 1 adjacent pair(s) ever flip order; SD of the rank-1 minus rank-20 stretch 0.06.

## S1 to S4 style counts against P0 (limits as BSEL: S2 and S3 counts 12/1/3/9, all/frontier/sparse/dense)

| Variant | Spearman all | Spearman frontier | S2 count, all (range) | S3 count, all (range) | Refits failing S2, all | Refits failing any of S1 to S3, frontier | Refits failing S4 | Frontier max shift (points) |
|---|---|---|---|---|---|---|---|---|
| R | 0.9994 to 0.9997 | 0.9970 to 1.0000 | 6 to 32 | 0 to 3 | 16 of 50 | 0 of 50 | 0 of 50 | 0.19 to 1.07 |
| I | 0.9993 to 0.9995 | 1.0000 to 1.0000 | 11 to 15 | 0 to 0 | 14 of 20 | 0 of 20 | 0 of 20 | 0.12 to 0.47 |
| O | 0.9994 to 0.9995 | 1.0000 to 1.0000 | 12 to 16 | 0 to 0 | 17 of 20 | 0 of 20 | 0 of 20 | 0.16 to 0.52 |

Deterministic EEE fit against P0: S2 count 31, S3 count 2, Spearman 0.9994. Against the deterministic EEE fit instead:

| Variant | S2 count, all (range) | S3 count, all (range) | Refits failing S2, all | Frontier max shift (points) |
|---|---|---|---|---|
| R | 6 to 49 | 0 to 16 | 20 of 50 | 0.12 to 0.97 |
| I | 1 to 5 | 0 to 0 | 0 of 20 | 0.25 to 0.49 |
| O | 1 to 6 | 0 to 0 | 0 of 20 | 0.31 to 0.54 |

## Residual checks T1 to T7 on each refit

Each refit's T statistics are computed on its own data and posterior (same code as W4, thinned to 400 draws), and the max-T adjusted p is taken against the existing W3 model-true replicates of the EEE-data fit (192) and of the Epoch-data fit (187). Those replicate sets were generated from the original fits, not from each refit, so this isolates the change in the observed statistic. A per-refit replicate set would need about 200 extra fits per refit. Validation: the same code reproduces the published W4 values (Epoch T5 4.455, EEE T5 3.861).

| Variant | T5 observed (range) | T5 adjusted p, EEE replicates: median (range) | Rejections of T5 at 0.01 (EEE / Epoch replicates) | T3 adjusted p, EEE replicates: median | T1 and T2 rejections |
|---|---|---|---|---|---|
| R | 3.851 to 4.868 | 0.0104 (0.0052 to 0.0155) | 8 / 9 of 50 | 0.073 | 50 and 50 of 50 |
| I | 3.907 to 4.413 | 0.0104 (0.0052 to 0.0104) | 1 / 1 of 20 | 0.049 | 20 and 20 of 20 |
| O | 3.936 to 4.321 | 0.0104 (0.0104 to 0.0104) | 0 / 0 of 20 | 0.026 | 20 and 20 of 20 |

Reference: Epoch data T5 4.455, adjusted p 0.0053; deterministic EEE fit T5 3.861, adjusted p 0.0155 (T3 0.0933). Adjusted p takes values in steps of about 0.005 (1/193), so 0.0104 is two steps above the smallest value and sits next to the 0.01 level. T6 and T7 never reject. T3 and T4 never reject.

## Drivers

- R: Spearman of per-model SD with the number of the model's multi-source cells -0.12, with the summed pool range 0.07, with the mean difficulty SD of the model's own benchmarks 0.69. Models with no multi-source cell: median SD 1.04 (n=68); with some: 0.28 (n=186). Benchmarks with the largest difficulty SD: TriviaQA 0.500, LAMBADA 0.292, PIQA 0.226, OSWorld 2.0 0.217, VPCT 0.194.
- I: Spearman of per-model SD with the number of the model's multi-source cells -0.03, with the summed pool range 0.10, with the mean difficulty SD of the model's own benchmarks 0.67. Models with no multi-source cell: median SD 0.11 (n=142); with some: 0.11 (n=112). Benchmarks with the largest difficulty SD: LAMBADA 0.066, TriviaQA 0.062, HellaSwag 0.046, PIQA 0.041, GSM8K 0.022.
- O: Spearman of per-model SD with the number of the model's multi-source cells -0.02, with the summed pool range 0.09, with the mean difficulty SD of the model's own benchmarks 0.59. Models with no multi-source cell: median SD 0.08 (n=158); with some: 0.08 (n=96). Benchmarks with the largest difficulty SD: LAMBADA 0.047, TriviaQA 0.041, HellaSwag 0.034, PIQA 0.032, GSM8K 0.019.

## Files

design.json, fits/ (per-refit json and thinned draws), summary.json, chart_data.json, fragment.html, tcheck.json. Code: tools/prov_*.py, tools/run_prov.sh, tools/prov_mem_watchdog.sh.
