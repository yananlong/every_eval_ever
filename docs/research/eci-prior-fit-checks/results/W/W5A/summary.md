# W5A: anchor sensitivity of the W5 prior-sensitivity scores (plan A3, block WA; exploratory)

Post-processing of the saved W5 posterior draws (no new fits). Each W5 arm and P0 are re-anchored on the same pair, with targets equal to W5 P0's posterior-mean ECI of the two anchor models (130/150 for the original pair), and S1-S4 are scored with the frozen `sens_metrics.score` through `wa_anchor.score_vs_base` (S1 and S4 on all models, S2 and S3 with the anchors of both anchorings removed from each stratum, limits floor(0.05 n), S2 threshold 0.25 W). A3 enters no verdict. The C1 verdict stays on the original anchoring.

Code: `eci_work/tools/w5_anchor.py` (numbers), `eci_work/tools/w5_anchor_report.py` (this file and fragment.html). Data: `w5_anchor.json`, `chart_data.json`.

## Checks

- Re-anchoring the ECI draws equals re-anchoring the raw capability draws: on the raw capability kept in the .nc files (P0, P1, P8, P9 thinned to 2,000 draws; PR and J2 all 16,000) the largest difference is 7.1e-14 ECI points; against the float32 .npz draws it is 3.4e-05 (float32 storage).
- No pair has a draw with a non-positive map (c_high <= c_low) in any arm or in P0.
- Within-arm invariance (P8, PR, every pair): largest change of a within-draw rank 0, of P(top 10) 0.
- Reproduction of `runs/W/W5/sensitivity.json` under the original anchoring: P1, P2, P4-P8, X1, X2, PR and J2 match to 1e-9 (PR and J2 against w5j_scores.json for J2). P9, P10 do not match when read from `P9_retry3.npz` / `P10_retry3.npz`: sensitivity.json was computed from `P9.npz` and `P10.npz` (8,000 draws per chain, the first-pass fits), which reproduce exactly (rows P9_first, P10_first). `w5_agg.entry_fit` loads `<name>.npz` whenever the sidecar says resolved, and the sidecars were later set to resolved by the third attempt. Every pass/fail flag and every S2/S3 count is the same for both versions; continuous values differ slightly (P9 S4 largest adjacent-pair change 0.068 retry3 against 0.061 first pass; all-stratum S1 0.999750 against 0.999754). This report uses the retry3 draws for P9 and P10, as the brief specifies, and carries the first-pass arrays alongside; their flags agree in every pair.

## Strata sizes per pair (S2/S3 n, limit)

| Pair | Low anchor (T) | High anchor (T) | all | frontier | sparse | dense |
| --- | --- | --- | --- | --- | --- | --- |
| orig | Claude 3.5 Sonnet (130.00) | GPT-5 (150.00) | 254 (12) | 20 (1) | 72 (3) | 182 (9) |
| L0-S10 | Claude Sonnet 4 (141.86) | Claude Opus 4.5 (151.91) | 252 (12) | 20 (1) | 72 (3) | 180 (9) |
| L0-S15 | Claude Sonnet 4 (141.86) | Claude Opus 4.7 (157.42) | 252 (12) | 20 (1) | 72 (3) | 180 (9) |
| L0-S20 | Claude Sonnet 4 (141.86) | GPT-5.6 Sol (162.99) | 252 (12) | 19 (0) | 72 (3) | 180 (9) |
| L6-S10 | Claude Opus 4.5 (151.91) | GPT-5.6 Sol (162.99) | 252 (12) | 19 (0) | 72 (3) | 180 (9) |
| L6-S15 | Claude Opus 4.5 (151.91) | Claude Fable 5.1 (167.01) | 252 (12) | 19 (0) | 72 (3) | 180 (9) |
| L12-S10 | Claude Opus 4.6 (156.34) | Gemini 4 Argon (166.48) | 252 (12) | 19 (0) | 72 (3) | 180 (9) |
| Full | Claude Sonnet 4 (141.86) | GPT-6 Astra (169.02) | 252 (12) | 19 (0) | 72 (3) | 180 (9) |
| X-lowGPT5 | GPT-4o mini (123.88) | GPT-5 (150.00) | 253 (12) | 20 (1) | 72 (3) | 181 (9) |
| X-lowTop | GPT-4o mini (123.88) | Claude Fable 5.2 (173.43) | 252 (12) | 19 (0) | 72 (3) | 180 (9) |

S1 keeps all models of the stratum (plan convention). When a pair's anchor is in the 20-model frontier stratum, frontier n falls to 19 and its limit to 0. No status change below is caused by that: every change also holds against the original limits (12/1/3/9).

## Pass/fail by arm and pair

Cell: failing strata (A all, F frontier, S sparse, D dense; a stratum fails if S1, S2 or S3 fails) and S4, then S2/S3 counts per stratum. * marks a flag that differs from the original anchoring.

| Arm | orig | L0-S10 | L0-S15 | L0-S20 | L6-S10 | L6-S15 | L12-S10 | Full | X-lowGPT5 | X-lowTop |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P1, P2, P4, P5, P6, P7, P10, X1, X2, P0b, P3 | pass | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| P8 | A S D<br>A 59/57 F 0/0 S 30/33 D 29/24 | A S D<br>A 55/55 F 0/0 S 29/32 D 26/23 | A S D<br>A 61/55 F 0/0 S 32/32 D 29/23 | A S D<br>A 61/58 F 0/0 S 32/33 D 29/25 | A S D<br>A 61/55 F 0/0 S 32/32 D 29/23 | A S D<br>A 61/56 F 0/0 S 32/33 D 29/23 | A S D<br>A 61/54 F 0/0 S 32/32 D 29/22 | A S D<br>A 63/59 F 0/0 S 33/33 D 30/26 | A S D<br>A 58/55 F 0/0 S 29/32 D 29/23 | A S D<br>A 63/58 F 0/0 S 31/33 D 32/25 |
| P9 | A S D<br>A 61/59 F 0/0 S 32/33 D 29/26 | A S D<br>A 61/56 F 0/0 S 32/33 D 29/23 | A S D<br>A 64/58 F 0/0 S 33/33 D 31/25 | A S D<br>A 69/59 F 0/0 S 36/33 D 33/26 | A S D<br>A 70/57 F 0/0 S 36/33 D 34/24 | A S D<br>A 77/59 F 0/0 S 40/33 D 37/26 | A S D<br>A 69/58 F 0/0 S 36/33 D 33/25 | A S D<br>A 74/60 F 0/0 S 39/34 D 35/26 | *A F S D<br>A 66/59 F 5/0 S 32/33 D 34/26 | *A F S D<br>A 141/63 F 7/0 S 33/34 D 108/29 |
| PR | A S D<br>A 62/60 F 0/0 S 32/34 D 30/26 | A S D<br>A 61/57 F 0/0 S 32/33 D 29/24 | A S D<br>A 67/59 F 0/0 S 35/33 D 32/26 | A S D<br>A 73/60 F 0/0 S 39/34 D 34/26 | A S D<br>A 71/58 F 0/0 S 37/33 D 34/25 | A S D<br>A 82/60 F 0/0 S 44/34 D 38/26 | A S D<br>A 72/57 F 0/0 S 38/33 D 34/24 | A S D<br>A 77/61 F 0/0 S 40/34 D 37/27 | *A F S D<br>A 72/59 F 11/0 S 32/33 D 40/26 | *A F S D<br>A 155/65 F 9/0 S 36/34 D 119/31 |
| J2 | A S D<br>A 40/21 F 0/0 S 21/16 D 19/5 | *A S D<br>A 32/1 F 0/0 S 18/1 D 14/0 | *A S D<br>A 40/12 F 0/0 S 21/10 D 19/2 | A S D<br>A 46/28 F 0/0 S 23/23 D 23/5 | *A S D<br>A 37/8 F 0/0 S 20/8 D 17/0 | *A S D<br>A 44/11 F 0/0 S 24/10 D 20/1 | *A S D<br>A 34/6 F 0/0 S 19/5 D 15/1 | A S D<br>A 47/37 F 0/0 S 24/28 D 23/9 | A S D<br>A 35/19 F 0/0 S 20/16 D 15/3 | *A S D<br>A 41/43 F 0/0 S 21/29 D 20/14 |
| P9_first | A S D<br>A 61/59 F 0/0 S 32/33 D 29/26 | A S D<br>A 61/55 F 0/0 S 32/32 D 29/23 | A S D<br>A 64/58 F 0/0 S 33/33 D 31/25 | A S D<br>A 70/59 F 0/0 S 36/33 D 34/26 | A S D<br>A 70/58 F 0/0 S 36/33 D 34/25 | A S D<br>A 77/59 F 0/0 S 40/33 D 37/26 | A S D<br>A 69/58 F 0/0 S 36/33 D 33/25 | A S D<br>A 76/60 F 0/0 S 40/34 D 36/26 | *A F S D<br>A 67/59 F 6/0 S 32/33 D 35/26 | *A F S D<br>A 145/61 F 8/0 S 35/34 D 110/27 |

C1 rule applied on each anchoring (defensible arms P1-P10, P3 unresolved): orig: P8 [all,sparse], P9 [all,sparse]; L0-S10: P8 [all,sparse], P9 [all,sparse]; L0-S15: P8 [all,sparse], P9 [all,sparse]; L0-S20: P8 [all,sparse], P9 [all,sparse]; L6-S10: P8 [all,sparse], P9 [all,sparse]; L6-S15: P8 [all,sparse], P9 [all,sparse]; L12-S10: P8 [all,sparse], P9 [all,sparse]; Full: P8 [all,sparse], P9 [all,sparse]; X-lowGPT5: P8 [all,sparse], P9 [all,frontier,sparse]; X-lowTop: P8 [all,sparse], P9 [all,frontier,sparse].

Changes against the original anchoring:

- L0-S10, J2: failing criteria all:S2, all:S3, sparse:S2, sparse:S3, dense:S2 -> all:S2, sparse:S2, dense:S2
- L0-S15, J2: failing criteria all:S2, all:S3, sparse:S2, sparse:S3, dense:S2 -> all:S2, sparse:S2, sparse:S3, dense:S2
- L6-S10, J2: failing criteria all:S2, all:S3, sparse:S2, sparse:S3, dense:S2 -> all:S2, sparse:S2, sparse:S3, dense:S2
- L6-S15, J2: failing criteria all:S2, all:S3, sparse:S2, sparse:S3, dense:S2 -> all:S2, sparse:S2, sparse:S3, dense:S2
- L12-S10, J2: failing criteria all:S2, all:S3, sparse:S2, sparse:S3, dense:S2 -> all:S2, sparse:S2, sparse:S3, dense:S2
- X-lowGPT5, P9: failing criteria all:S2, all:S3, sparse:S2, sparse:S3, dense:S2, dense:S3 -> all:S2, all:S3, frontier:S2, sparse:S2, sparse:S3, dense:S2, dense:S3
- X-lowGPT5, PR: failing criteria all:S2, all:S3, sparse:S2, sparse:S3, dense:S2, dense:S3 -> all:S2, all:S3, frontier:S2, sparse:S2, sparse:S3, dense:S2, dense:S3
- X-lowGPT5, P9_first: failing criteria all:S2, all:S3, sparse:S2, sparse:S3, dense:S2, dense:S3 -> all:S2, all:S3, frontier:S2, sparse:S2, sparse:S3, dense:S2, dense:S3
- X-lowTop, P9: failing criteria all:S2, all:S3, sparse:S2, sparse:S3, dense:S2, dense:S3 -> all:S2, all:S3, frontier:S2, sparse:S2, sparse:S3, dense:S2, dense:S3
- X-lowTop, PR: failing criteria all:S2, all:S3, sparse:S2, sparse:S3, dense:S2, dense:S3 -> all:S2, all:S3, frontier:S2, sparse:S2, sparse:S3, dense:S2, dense:S3
- X-lowTop, J2: failing criteria all:S2, all:S3, sparse:S2, sparse:S3, dense:S2 -> all:S2, all:S3, sparse:S2, sparse:S3, dense:S2, dense:S3
- X-lowTop, P9_first: failing criteria all:S2, all:S3, sparse:S2, sparse:S3, dense:S2, dense:S3 -> all:S2, all:S3, frontier:S2, sparse:S2, sparse:S3, dense:S2, dense:S3

## Anchor values with the pair fixed

If the pair is fixed and the targets (T_l, T_h) become (T_l', T_h'), every draw of both fits maps by ECI' = T_l' + k (ECI - T_l) with one constant k = (T_h' - T_l')/(T_h - T_l) > 0. Means, quantiles and widths all scale by k, so |mean_k - mean_0| / W_0 (S2) and W_k / W_0 (S3) are unchanged, the Spearman correlation of means (S1) and the within-draw orders (S4) are unchanged, and every point shift and gap scales by k.

Numerically, for every pair and the value sets (100, 150), (0, 100), (130, 140): largest change in S1 0.0e+00, in the largest relative shift 2.5e-12, in the median width ratio 7.4e-14, in the S4 pair change 0.0e+00; 0 count or flag mismatches; the low-end shift and frontier stretch equal k times their values at the pair targets to 3.8e-11 points.

Under the original pair, k = 2.5, 5 and 0.5 for the three value sets:

| Arm | Low-end shift (130/150) | (100/150) | (0/100) | (130/140) | Frontier stretch (130/150) | (100/150) | (0/100) | (130/140) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P8 | 14.00 | 34.99 | 69.99 | 7.00 | 0.81 | 2.01 | 4.03 | 0.40 |
| P9 | 17.23 | 43.07 | 86.14 | 8.61 | 1.13 | 2.83 | 5.66 | 0.57 |
| PR | 18.76 | 46.90 | 93.80 | 9.38 | 1.23 | 3.07 | 6.15 | 0.61 |
| J2 | 8.66 | 21.66 | 43.32 | 4.33 | 0.44 | 1.10 | 2.20 | 0.22 |

All value sets for all pairs are in `w5_anchor.json` under `values`.

## Point differentials against P0 (pair targets)

Low end: the 42 models below P0 ECI 100 under the original anchoring (mean shift, range). Frontier stretch: (top minus 20th of the strata.json frontier) in the arm minus the same in P0, top = Claude Fable 5.2, 20th = GPT-5.5. Gap changes: |(m_i - m_j)_arm - (m_i - m_j)_P0| over all pairs of non-anchor models, over frontier pairs, and over pairs of one low-end and one frontier model.

| Pair | Arm | Low-end shift (range) | in P0 widths | Frontier mean shift | Stretch (ratio) | Gap change all: median / max | frontier: median / max | low-frontier median | share of >2-point changes with a low-end model |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| orig | P8 | 14.00 (8.4 to 23.4) | 0.53 | 0.48 | 0.81 (1.061) | 0.70 / 23.82 | 0.25 / 1.00 | 12.87 | 0.70 |
| orig | P9 | 17.23 (10.4 to 28.9) | 0.65 | 0.72 | 1.13 (1.085) | 1.02 / 29.46 | 0.37 / 1.49 | 15.70 | 0.68 |
| orig | PR | 18.76 (11.4 to 31.7) | 0.71 | 0.77 | 1.23 (1.092) | 1.13 / 32.41 | 0.40 / 1.61 | 17.16 | 0.67 |
| orig | J2 | 8.66 (4.7 to 15.5) | 0.32 | 0.14 | 0.44 (1.033) | 0.52 / 15.75 | 0.15 / 0.75 | 7.92 | 0.80 |
| L0-S10 | P8 | 14.53 (8.8 to 24.2) | 0.47 | 0.34 | 0.70 (1.052) | 0.82 / 24.63 | 0.21 / 0.89 | 13.54 | 0.69 |
| L0-S10 | P9 | 17.99 (11.0 to 30.0) | 0.58 | 0.47 | 0.95 (1.071) | 1.18 / 30.61 | 0.32 / 1.31 | 16.70 | 0.66 |
| L0-S10 | PR | 19.35 (11.9 to 32.6) | 0.63 | 0.57 | 1.10 (1.082) | 1.25 / 33.32 | 0.37 / 1.49 | 17.93 | 0.66 |
| L0-S10 | J2 | 8.82 (4.8 to 15.7) | 0.28 | 0.13 | 0.42 (1.032) | 0.56 / 15.99 | 0.15 / 0.74 | 8.09 | 0.80 |
| L0-S15 | P8 | 14.61 (8.8 to 24.3) | 0.55 | 0.26 | 0.65 (1.048) | 0.88 / 24.75 | 0.20 / 0.84 | 13.69 | 0.69 |
| L0-S15 | P9 | 18.14 (11.1 to 30.2) | 0.68 | 0.34 | 0.87 (1.065) | 1.27 / 30.83 | 0.29 / 1.22 | 16.95 | 0.65 |
| L0-S15 | PR | 19.54 (12.0 to 32.9) | 0.74 | 0.41 | 1.00 (1.075) | 1.37 / 33.60 | 0.34 / 1.38 | 18.29 | 0.65 |
| L0-S15 | J2 | 8.75 (4.8 to 15.6) | 0.33 | 0.14 | 0.43 (1.032) | 0.54 / 15.87 | 0.15 / 0.74 | 8.01 | 0.80 |
| L0-S20 | P8 | 15.08 (9.2 to 25.0) | 0.60 | 0.01 | 0.50 (1.037) | 1.12 / 25.51 | 0.17 / 0.69 | 14.37 | 0.67 |
| L0-S20 | P9 | 18.75 (11.5 to 31.1) | 0.75 | -0.01 | 0.65 (1.049) | 1.60 / 31.81 | 0.25 / 1.01 | 17.88 | 0.63 |
| L0-S20 | PR | 20.23 (12.5 to 33.9) | 0.81 | -0.01 | 0.74 (1.055) | 1.75 / 34.71 | 0.28 / 1.12 | 19.41 | 0.62 |
| L0-S20 | J2 | 9.12 (5.1 to 16.1) | 0.36 | -0.03 | 0.33 (1.025) | 0.70 / 16.45 | 0.13 / 0.64 | 8.53 | 0.77 |
| L6-S10 | P8 | 15.97 (9.9 to 26.2) | 0.52 | -0.02 | 0.33 (1.025) | 1.41 / 26.54 | 0.13 / 0.53 | 15.24 | 0.65 |
| L6-S10 | P9 | 19.97 (12.5 to 32.7) | 0.64 | -0.05 | 0.40 (1.030) | 2.01 / 33.16 | 0.19 / 0.80 | 19.03 | 0.60 |
| L6-S10 | PR | 21.61 (13.7 to 35.7) | 0.70 | -0.05 | 0.45 (1.033) | 2.21 / 36.22 | 0.20 / 0.84 | 20.85 | 0.59 |
| L6-S10 | J2 | 9.56 (5.4 to 16.8) | 0.31 | -0.04 | 0.25 (1.019) | 0.84 / 17.00 | 0.11 / 0.57 | 8.98 | 0.75 |
| L6-S15 | P8 | 16.17 (10.1 to 26.5) | 0.58 | -0.08 | 0.27 (1.020) | 1.51 / 26.78 | 0.11 / 0.47 | 15.50 | 0.64 |
| L6-S15 | P9 | 20.24 (12.8 to 33.1) | 0.73 | -0.14 | 0.31 (1.023) | 2.14 / 33.52 | 0.16 / 0.72 | 19.37 | 0.59 |
| L6-S15 | PR | 21.85 (13.9 to 36.0) | 0.79 | -0.14 | 0.36 (1.027) | 2.33 / 36.49 | 0.18 / 0.77 | 21.17 | 0.57 |
| L6-S15 | J2 | 9.69 (5.5 to 16.9) | 0.35 | -0.08 | 0.22 (1.016) | 0.90 / 17.20 | 0.11 / 0.54 | 9.16 | 0.74 |
| L12-S10 | P8 | 16.60 (10.4 to 27.1) | 0.50 | -0.02 | 0.21 (1.015) | 1.62 / 27.27 | 0.09 / 0.42 | 15.87 | 0.63 |
| L12-S10 | P9 | 20.46 (13.0 to 33.4) | 0.62 | -0.04 | 0.31 (1.023) | 2.17 / 33.72 | 0.17 / 0.72 | 19.50 | 0.59 |
| L12-S10 | PR | 22.33 (14.3 to 36.7) | 0.68 | -0.04 | 0.30 (1.022) | 2.45 / 37.01 | 0.17 / 0.72 | 21.55 | 0.56 |
| L12-S10 | J2 | 9.75 (5.6 to 17.0) | 0.29 | -0.02 | 0.23 (1.017) | 0.89 / 17.21 | 0.11 / 0.55 | 9.15 | 0.74 |
| Full | P8 | 15.28 (9.3 to 25.3) | 0.63 | -0.10 | 0.43 (1.033) | 1.23 / 25.83 | 0.15 / 0.63 | 14.64 | 0.67 |
| Full | P9 | 18.99 (11.7 to 31.5) | 0.78 | -0.16 | 0.57 (1.043) | 1.74 / 32.20 | 0.22 / 0.93 | 18.22 | 0.62 |
| Full | PR | 20.51 (12.7 to 34.3) | 0.84 | -0.18 | 0.64 (1.048) | 1.90 / 35.14 | 0.25 / 1.02 | 19.87 | 0.61 |
| Full | J2 | 9.20 (5.1 to 16.3) | 0.37 | -0.08 | 0.30 (1.023) | 0.75 / 16.60 | 0.12 / 0.62 | 8.65 | 0.76 |
| X-lowGPT5 | P8 | 13.15 (7.7 to 22.2) | 0.54 | 0.73 | 1.03 (1.077) | 0.82 / 22.69 | 0.32 / 1.22 | 11.81 | 0.71 |
| X-lowGPT5 | P9 | 16.21 (9.6 to 27.4) | 0.67 | 1.04 | 1.43 (1.107) | 1.19 / 28.09 | 0.45 / 1.79 | 14.39 | 0.69 |
| X-lowGPT5 | PR | 17.56 (10.4 to 30.1) | 0.72 | 1.16 | 1.59 (1.119) | 1.30 / 30.81 | 0.51 / 1.98 | 15.60 | 0.68 |
| X-lowGPT5 | J2 | 7.61 (3.9 to 14.0) | 0.31 | 0.42 | 0.69 (1.052) | 0.44 / 14.47 | 0.21 / 1.00 | 6.67 | 0.83 |
| X-lowTop | P8 | 14.01 (8.2 to 23.8) | 0.60 | -0.55 | 0.60 (1.045) | 0.94 / 24.91 | 0.16 / 0.49 | 13.90 | 0.68 |
| X-lowTop | P9 | 17.30 (10.2 to 29.4) | 0.74 | -0.78 | 0.80 (1.060) | 1.36 / 31.05 | 0.25 / 0.74 | 17.21 | 0.65 |
| X-lowTop | PR | 18.69 (11.1 to 32.1) | 0.80 | -0.85 | 0.90 (1.067) | 1.49 / 33.93 | 0.27 / 0.83 | 18.67 | 0.64 |
| X-lowTop | J2 | 8.34 (4.3 to 15.2) | 0.35 | -0.49 | 0.39 (1.029) | 0.60 / 16.07 | 0.13 / 0.41 | 8.22 | 0.79 |

## Reading

- Under the seven WA alternative pairs no defensible arm changes status: P8 and P9 fail all, sparse and dense and pass the frontier and S4 in every pair, and P1, P2, P4-P7 and P10 pass everywhere, as do X1, X2, P0b and the non-converged P3 (exploratory). J2 (exploratory) changes at the criterion level only: its all-stratum S3 (21 against a limit of 12 originally) falls to 1-12 under five frontier-anchored pairs, while its all-stratum S2 still fails.
- Under the two exploratory pairs with GPT-4o mini (P0 ECI 123.9) as the low anchor, P9 and PR also fail the frontier on S2 (P9: 5 of 20 and 7 of 19 frontier models shift by more than 0.25 W; PR: 11 and 9). P8 stays at 0 but its largest frontier shift rises from 0.15 W to 0.24 W, just under the threshold. With GPT-5 as the high anchor every frontier model lies 10 to 23 points above it, so the 2 % compression of the GPT-4o mini to GPT-5 raw-capability gap under P9 (ratio to the Claude 3.5 Sonnet to GPT-5 gap 1.280 against 1.306 in P0) is extrapolated into a frontier-wide level shift of 0.4 to 2.2 points, against P0 frontier widths that shrink from a median 5.4 to 4.9.
- The C1 rule returns falsified on every anchoring (P8 and P9 fail all and sparse in every pair). Under the GPT-4o mini pairs P9 additionally fails the frontier, which would make the frontier part of the failure.
- Low end moves, frontier holds survives every pair in gap terms: frontier-pair gap changes stay at medians 0.09-0.51 points (max 2.0, PR under X-lowGPT5; 1.8 for P9), while low-end to frontier gaps change by medians of 12-22 points for P8, P9 and PR (6.7-9.2 for J2), and 56-83 % of the gap changes larger than 2 points involve one of the 42 low-end models, which make up 17 % of the models. In points the low-end shift grows as the anchors move up the scale (P8 13.2 under X-lowGPT5 to 16.6 under L12-S10; P9 16.2 to 20.5) because the shift is extrapolated further below the pair, and with the GPT-4o mini anchor it is smallest; in P0 widths it stays at 0.47-0.63 for P8 and 0.58-0.78 for P9.

