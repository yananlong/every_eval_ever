# W4G summary (final)

Posterior: `seed12345.nc`. Replicated datasets and statistics: 400 draws; LOO-PIT: 4000 draws. elpd_loo 3386.45, p_loo 449.9, Pareto k above 0.7 for 42 rows.
Calibrated p-values use 192 G-null replicates (planned 199, minimum 150 for a verdict); with fewer, the smallest possible p is 1/(R + 1) and no rejection at 0.01 is possible.

## Global checks (effect size = (observed - mean replicated) / SD replicated)

| Check | Observed | Replicated mean (SD) | Effect size | Raw in-sample p | Effect vs null SD | Calibrated p | Max-T adjusted p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T1 | 4.471 | 5.382 (0.679) | -1.34 | 0.930 | +9.29 | 0.005 | 0.005 |
| T2 | 3.21 | 1.121 (0.0874) | +23.90 | 0.000 | +26.74 | 0.005 | 0.005 |
| T3 | 0.08974 | 0.01182 (0.0141) | +5.51 | 0.005 | +2.38 | 0.031 | 0.093 |
| T4 | 0.02065 | 0.03057 (0.0198) | -0.50 | 0.635 | -2.41 | 0.990 | 1.000 |
| T5 | 3.861 | 3.387 (0.61) | +0.78 | 0.180 | +4.36 | 0.005 | 0.016 |
| T6 | 13.36 | 1.316 (1.36) | +8.83 | 0.000 | +6.49 | 0.005 | 0.202 |
| T7 | 3.032 | 4.797 (5.04) | -0.35 | 0.823 | -0.09 | 0.389 | 0.990 |
| boundary_count | 83 | 56.81 (6.46) | +4.05 | 0.000 (upper) / 1.000 (lower) |  | | |
| mid_range_share | 0.7975 | 0.7989 (0.00524) | -0.27 | 0.610 (upper) / 0.415 (lower) |  | | |

## Largest per-benchmark effects (benchmarks with at least 20 rows)

**mean_score**

| Benchmark | Rows | Observed | Replicated mean (SD) | Effect size |
| --- | --- | --- | --- | --- |
| OTIS Mock AIME 2024-2025 | 169 | 0.6592 | 0.6517 (0.00722) | +1.04 |
| Furniture Assembly | 39 | 0.2619 | 0.2498 (0.0223) | +0.54 |
| MMLU | 92 | 0.519 | 0.5141 (0.0111) | +0.44 |
| Mystery Game Puzzles | 82 | 0.233 | 0.2259 (0.0163) | +0.44 |
| GPQA diamond | 176 | 0.6826 | 0.6805 (0.00473) | +0.44 |

**boundary_count**

| Benchmark | Rows | Observed | Replicated mean (SD) | Effect size |
| --- | --- | --- | --- | --- |
| Mystery Game Puzzles | 82 | 14 | 6.235 (1.84) | +4.23 |
| Furniture Assembly | 39 | 10 | 3.143 (1.71) | +4.02 |
| FrontierMath-Tier-4-2025-07-01-Private | 26 | 10 | 4.058 (1.74) | +3.42 |
| SimpleBench | 95 | 1 | 0.07 (0.274) | +3.39 |
| Chess Puzzles | 87 | 4 | 1.265 (0.968) | +2.83 |

**Q_b**

| Benchmark | Rows | Observed | Replicated mean (SD) | Effect size |
| --- | --- | --- | --- | --- |
| OTIS Mock AIME 2024-2025 | 169 | 24.59 | 5.581 (4.69) | +4.05 |
| DTBench | 150 | 17.6 | 5.747 (4.26) | +2.78 |
| ARC-AGI-2 | 90 | 13.97 | 6 (5.46) | +1.46 |
| PIQA | 41 | 0.6014 | 5.152 (3.85) | -1.18 |
| BBH | 39 | 0.5502 | 4.955 (3.9) | -1.13 |

**dispersion**

| Benchmark | Rows | Observed | Replicated mean (SD) | Effect size |
| --- | --- | --- | --- | --- |
| MMLU | 92 | 0.591 | 1.012 (0.245) | -1.72 |
| BBH | 39 | 0.4678 | 1.006 (0.37) | -1.45 |
| FrontierMath-Tiers-1-3-v2-Private | 90 | 0.6505 | 0.974 (0.224) | -1.44 |
| LMCA | 126 | 0.7517 | 1.008 (0.179) | -1.43 |
| ARC-AGI | 91 | 0.6148 | 1.011 (0.299) | -1.32 |

## Randomised LOO-PIT

All rows (2879): mean 0.509, SD 0.290 (uniform 0.289), share below 0.05 / above 0.95 = 0.056 / 0.049, gamma 0.0000, p 5e-05.
Rows with Pareto k at most 0.7 (2837): mean 0.510, SD 0.287, share below 0.05 / above 0.95 = 0.051 / 0.046, gamma p 0.0388.
Per benchmark (35 with at least 30 rows), gamma test flagged at 0.00029: none.
