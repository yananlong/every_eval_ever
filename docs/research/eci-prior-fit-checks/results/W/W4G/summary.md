# W4G summary (INTERIM calibrated p)

Posterior: `seed12345.nc`. Replicated datasets and statistics: 400 draws; LOO-PIT: 4000 draws. elpd_loo 3449.96, p_loo 442.6, Pareto k above 0.7 for 50 rows.
Calibrated p-values use 22 G-null replicates (planned 199, minimum 150 for a verdict); with fewer, the smallest possible p is 1/(R + 1) and no rejection at 0.01 is possible.

## Global checks (effect size = (observed - mean replicated) / SD replicated)

| Check | Observed | Replicated mean (SD) | Effect size | Raw in-sample p | Effect vs null SD | Calibrated p | Max-T adjusted p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T1 | 4.503 | 5.385 (0.725) | -1.22 | 0.905 | +10.45 | 0.043 | 0.043 |
| T2 | 3.402 | 1.114 (0.0872) | +26.23 | 0.000 | +39.51 | 0.043 | 0.043 |
| T3 | 0.08059 | 0.01238 (0.023) | +2.96 | 0.003 | +0.54 | 0.391 | 0.913 |
| T4 | 0.02198 | 0.03045 (0.02) | -0.42 | 0.618 | -2.91 | 1.000 | 1.000 |
| T5 | 4.455 | 3.388 (0.73) | +1.46 | 0.070 | +8.74 | 0.043 | 0.043 |
| T6 | 11.56 | 1.367 (1.45) | +7.01 | 0.000 | +3.20 | 0.043 | 0.217 |
| T7 | 3.644 | 5.23 (11.4) | -0.14 | 0.583 | +0.32 | 0.348 | 0.957 |
| boundary_count | 81 | 56.46 (6.39) | +3.84 | 0.000 (upper) / 1.000 (lower) |  | | |
| mid_range_share | 0.7996 | 0.8019 (0.00492) | -0.47 | 0.680 (upper) / 0.345 (lower) |  | | |

## Largest per-benchmark effects (benchmarks with at least 20 rows)

**mean_score**

| Benchmark | Rows | Observed | Replicated mean (SD) | Effect size |
| --- | --- | --- | --- | --- |
| OTIS Mock AIME 2024-2025 | 169 | 0.6592 | 0.6504 (0.00787) | +1.12 |
| Mystery Game Puzzles | 82 | 0.233 | 0.2232 (0.0176) | +0.55 |
| Furniture Assembly | 39 | 0.2619 | 0.2484 (0.025) | +0.54 |
| MMLU | 92 | 0.522 | 0.518 (0.00982) | +0.41 |
| ARC-AGI | 91 | 0.6633 | 0.6603 (0.00821) | +0.37 |

**boundary_count**

| Benchmark | Rows | Observed | Replicated mean (SD) | Effect size |
| --- | --- | --- | --- | --- |
| SimpleBench | 95 | 1 | 0.0425 (0.202) | +4.74 |
| Mystery Game Puzzles | 82 | 14 | 6.423 (1.81) | +4.20 |
| Furniture Assembly | 39 | 10 | 3.328 (1.79) | +3.73 |
| FrontierMath-Tier-4-2025-07-01-Private | 26 | 10 | 4.44 (1.61) | +3.45 |
| Chess Puzzles | 87 | 4 | 1.163 (0.971) | +2.92 |

**Q_b**

| Benchmark | Rows | Observed | Replicated mean (SD) | Effect size |
| --- | --- | --- | --- | --- |
| OTIS Mock AIME 2024-2025 | 169 | 26.3 | 5.697 (4.84) | +4.26 |
| DTBench | 150 | 11.78 | 5.371 (4.34) | +1.48 |
| ARC-AGI-2 | 90 | 13.64 | 6.103 (5.28) | +1.43 |
| Aider polyglot | 44 | 0.4341 | 5.187 (3.83) | -1.24 |
| Winogrande | 61 | 0.5852 | 5.857 (4.53) | -1.16 |

**dispersion**

| Benchmark | Rows | Observed | Replicated mean (SD) | Effect size |
| --- | --- | --- | --- | --- |
| MMLU | 92 | 0.538 | 1.001 (0.248) | -1.87 |
| BBH | 39 | 0.4834 | 0.9968 (0.348) | -1.48 |
| LMCA | 126 | 0.7543 | 0.9898 (0.171) | -1.37 |
| FrontierMath-Tiers-1-3-v2-Private | 90 | 0.6828 | 0.9887 (0.229) | -1.33 |
| ARC-AGI | 91 | 0.637 | 0.9934 (0.306) | -1.16 |

## Randomised LOO-PIT

All rows (2879): mean 0.508, SD 0.290 (uniform 0.289), share below 0.05 / above 0.95 = 0.061 / 0.052, gamma 0.0000, p 5e-05.
Rows with Pareto k at most 0.7 (2829): mean 0.510, SD 0.287, share below 0.05 / above 0.95 = 0.053 / 0.048, gamma p 0.0345.
Per benchmark (35 with at least 30 rows), gamma test flagged at 0.00029: none.

## Reading (interim, written by hand)

- LOO-PIT is close to uniform. The ECDF difference dips to about -0.025 near u = 0.5 and touches the lower edge of the 95% band; PIT values fall in the tails slightly more often than expected (0.061 below 0.05, 0.052 above 0.95). The all-rows gamma p is at its floor (5e-5) but is 0.035 on the 2,829 rows with Pareto k at most 0.7, so the departure is driven partly by 50 rows with unreliable weights. No benchmark with at least 30 rows is flagged. The shape means the predictive distributions are slightly too narrow, by a small amount.
- The in-sample effect sizes understate fitted-residual statistics, as M6 says: T1 observed 4.50 sits below the replicated mean 5.39 (effect -1.2, raw p 0.905) yet is 10.5 null-SDs above the null-refit mean. The null-referenced effect sizes (T1 +10.5, T2 +39.5, T5 +8.7 with 22 replicates) are the ones to cite. These calibrated p-values are interim (22 replicates; the smallest possible p is 0.043), so none rejects.
- Largest effects: T2 (local dependence) +26 SD against the replicated datasets and about +40 against the null refits; the boundary count is 81 against 56.5 expected (+3.8 SD), concentrated in SimpleBench (+4.7), Mystery Game Puzzles (+4.2), Furniture Assembly (+3.7) and FrontierMath-Tier-4-2025-07-01-Private (+3.5); $Q_b$ is largest for OTIS Mock AIME 2024-2025 (observed 26.3 against 5.7, +4.3 SD); the dispersion is below 1 for MMLU (0.54 against 1.00, -1.9 SD). The mid-range share is as expected (effect -0.47).
- The density overlays show the observed density departing from the replicates near 0 for OTIS Mock AIME, ARC-AGI-2 and Mystery Game Puzzles, and a bump near 0.45 for WeirdML.
