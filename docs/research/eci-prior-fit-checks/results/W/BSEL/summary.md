# BSEL: sensitivity of the ECI to the choice of benchmarks (2026-11-21)

Exploratory under Epoch's model, except A4, which is the plan's optional item and is reported with no verdict. Baseline P0 (W5: Epoch's priors, seed 12345, 4 chains, 4,000 draws per chain, target_accept 0.95). Each refit deletes the rows of its benchmarks from the fit input, re-applies Epoch's inclusion rule (at least 4 benchmarks and at least 4 scores in [0.1, 0.9] per model) and refits with Epoch's `fit_bayesian_eci` at P0's settings (retry at 8,000 draws, then target_accept 0.99, 2 h cap per attempt). Scores are on the models present in both fits. S2 and S3 pass/fail uses the registered counts 12/1/3/9 for all/frontier/sparse/dense even where the inclusion rule removed stratum members (sens_metrics' own floor(0.05 n) flags are kept in summary.json). No subset removed an anchor, so no refit is unanchored.

Design: A4 (8 LOBO refits, the benchmarks both anchors have scores on), the other 49 LOBO refits, four residual clusters (all four FrontierMath tiers; ARC-AGI and ARC-AGI-2; OTIS Mock AIME 2024-2025 and LMCA; HellaSwag, PIQA, Winogrande, TriviaQA, GSM8K), all 16 benchmarks of W4d's F at once, and 20 random drops of 11 of 57 benchmarks (`numpy.random.default_rng(20261121)`, `choice(57, 11, replace=False)` on the sorted names). 82 refits. The FrontierMath cluster drops v1 and v2 tiers together because Epoch's supersession step is not re-run on the deleted rows (see deviations_local.md).

## Fit status

- Seed 12345 (first pass, 06:58 to 10:47 UTC): 80 of 82 converged by the W5 rule (0 divergences, R-hat <= 1.01, bulk ESS >= 400). A4_DTBench converged on the second attempt (8,000 draws).
- A4 OTIS Mock AIME 2024-2025: attempt 1 fell back to the cold stage and ended non-converged (0 divergences, R-hat 1.026, min ESS 170, 6,517 s); attempt 2 (8,000 draws) hit the 2 h cap.
- LOBO FrontierMath-Tier-4-2025-07-01-Private: attempt 1 hit the 2 h cap; no draws.
- Labelled deviation: both were rerun with seed 22345 (the P0b seed) and converged on the first attempt in 359 s and 548 s (R-hat 1.001, min ESS 5,847 and 5,575). The converged reruns stand in for the seed-12345 records in every count and table below (`substituted_by_rerun` in summary.json; seed-12345-only counts in `fail_counts_converged_seed12345_only`). The non-converged seed-12345 OTIS draws give almost the same numbers (frontier max shift 4.10 against 4.08, stretch +2.52 against +2.51).
- Median wall time 402 s per fit (16 concurrent on cores 0-63, 1 thread per chain process); five other fits needed 41 to 115 min because Epoch's pilot stage ran slowly or failed its checks. Peak watchdog RSS 36.0 GB.
- Seed-noise reference P0b (seed 22345) against P0: every stratum passes S1-S4, frontier max shift 0.03 points, max adjacent-pair change 0.007, stretch change -0.002.

## Main table

Cells: S1 / S2 count / S3 count; `*` = fails S1, S2 or S3 in that stratum. Stretch = posterior-mean ECI of rank 1 minus rank 20 (P0 13.32). Scale slope = OLS slope of the refit's posterior-mean ECI on P0's over common non-anchor models (1 = no stretch relative to the anchor gap). Low end = mean shift of the models below P0 ECI 100 (42 in P0).

| Refit | Models dropped | all S1/S2/S3 | frontier | sparse | dense | S4 (max pair change) | Frontier max abs shift | Stretch change (rank 1 - rank 20) | Scale slope | Low-end mean shift | Top-10 set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P0b (seed noise) | 0 | 1.000/0/0 | 1.000/0/0 | 1.000/0/0 | 1.000/0/0 | pass (0.01) | 0.03 | -0.00 | nan | +nan | same |
| A4_DTBench | 15 | 1.000/8/1 | 0.999/0/0 | 0.999/4/1* | 1.000/4/0 | pass (0.07) | 1.61 | -0.95 | 1.024 | -2.3 | same |
| A4_GPQA_diamond | 12 | 1.000/22/21* | 1.000/2/0* | 0.999/3/10* | 1.000/19/11* | pass (0.06) | 1.93 | +1.23 | 0.954 | +3.8 | same |
| A4_MATH_level_5 | 7 | 1.000/85/12* | 1.000/0/0 | 1.000/36/4* | 1.000/49/8* | pass (0.03) | 1.66 | +0.96 | 1.118 | -8.5 | same |
| A4_METR_Time_Horizons | 1 | 1.000/0/0 | 1.000/0/0 | 1.000/0/0 | 1.000/0/0 | pass (0.01) | 0.06 | -0.01 | 0.995 | +0.4 | same |
| A4_OTIS_Mock_AIME_2024_2025 (non-converged) | 6 | 1.000/164/114* | 1.000/20/17* | 0.999/54/34* | 1.000/110/80* | pass (0.04) | 4.10 | +2.52 | 1.160 | -11.1 | same |
| A4_SimpleBench | 1 | 1.000/0/0 | 0.999/0/0 | 1.000/0/0 | 1.000/0/0 | pass (0.07) | 0.25 | -0.17 | 0.986 | +1.0 | same |
| A4_VPCT | 1 | 1.000/0/0 | 1.000/0/0 | 1.000/0/0 | 1.000/0/0 | pass (0.01) | 0.13 | +0.05 | 0.999 | +0.2 | same |
| A4_WeirdML | 5 | 1.000/0/0 | 0.995/0/0 | 1.000/0/0 | 1.000/0/0 | pass (0.05) | 0.88 | -0.46 | 0.980 | +1.3 | same |
| C_FM | 3 | 0.999/31/4* | 0.995/0/0 | 1.000/0/0 | 0.999/31/4* | fail (0.35) | 1.02 | -0.62 | 0.988 | +1.6 | same |
| C_ARC | 2 | 0.999/40/5* | 0.997/1/0 | 1.000/0/0 | 0.999/40/5* | pass (0.08) | 1.12 | +0.63 | 0.960 | +2.2 | same |
| C_OTIS_LMCA | 15 | 1.000/148/137* | 0.995/19/16* | 0.999/48/47* | 1.000/100/90* | pass (0.09) | 3.10 | +1.77 | 1.184 | -13.2 | same |
| C_OLD | 37 | 1.000/3/2 | 1.000/0/0 | 1.000/0/0 | 1.000/3/2 | pass (0.01) | 0.28 | +0.21 | 0.963 | +3.8 | same |
| C_F16 | 103 | 0.993/132/150* | 0.960/18/19* | 1.000/6/5* | 0.993/126/145* | fail (0.43) | 19.35 | +14.25 | 1.387 | -23.8 | same |
| R01 | 20 | 1.000/150/137* | 0.994/20/19* | 0.999/43/23* | 0.999/107/114* | fail (0.37) | 3.88 | +2.10 | 1.135 | -9.1 | same |
| R02 | 33 | 0.999/56/19* | 0.992/2/0* | 0.999/14/11* | 0.999/42/8* | fail (0.27) | 1.50 | -0.25 | 0.893 | +8.6 | same |
| R03 | 23 | 1.000/52/13* | 0.986/10/0* | 1.000/11/6* | 1.000/41/7* | fail (0.11) | 2.17 | -1.30 | 0.853 | +10.6 | same |
| R04 | 33 | 0.999/159/205* | 0.997/20/20* | 1.000/39/43* | 0.999/120/162* | pass (0.04) | 4.35 | +2.32 | 1.218 | -14.8 | same |
| R05 | 57 | 0.999/41/28* | 0.980/7/0* | 0.987/13/10* | 0.999/28/18* | fail (0.36) | 2.16 | -0.30 | 0.977 | +0.6 | same |
| R06 | 36 | 0.999/24/1* | 0.977/5/0* | 0.998/6/0* | 0.999/18/1* | fail (0.40) | 1.94 | -0.44 | 0.947 | +3.9 | Claude Fable 5 in |
| R07 | 52 | 0.999/52/37* | 1.000/0/0 | 0.999/11/7* | 0.999/41/30* | fail (0.12) | 0.32 | +0.26 | 0.822 | +14.5 | same |
| R08 | 45 | 0.999/80/68* | 0.983/5/0* | 0.998/20/17* | 0.999/60/51* | fail (0.35) | 2.00 | +0.56 | 1.143 | -10.2 | same |
| R09 | 30 | 0.999/165/194* | 0.991/18/20* | 0.998/35/29* | 0.999/130/165* | fail (0.19) | 4.29 | +2.77 | 1.137 | -9.0 | Claude Fable 5 in |
| R10 | 18 | 0.999/96/105* | 0.995/0/15* | 0.999/18/11* | 0.998/78/94* | fail (0.12) | 1.61 | +2.38 | 1.060 | -5.0 | same |
| R11 | 8 | 0.999/22/13* | 0.984/1/1* | 0.998/2/0 | 0.999/20/13* | fail (0.34) | 1.40 | -0.31 | 0.969 | +2.6 | same |
| R12 | 44 | 0.999/111/149* | 0.992/6/19* | 0.993/24/18* | 0.999/87/131* | fail (0.14) | 2.60 | +1.83 | 1.018 | -0.8 | Claude Fable 5 in |
| R13 | 26 | 0.999/146/35* | 0.994/14/0* | 0.995/37/21* | 0.999/109/14* | fail (0.18) | 2.14 | -1.05 | 0.820 | +12.3 | same |
| R14 | 25 | 1.000/75/3* | 0.992/8/0* | 1.000/3/1 | 1.000/72/2* | fail (0.15) | 1.72 | -0.14 | 0.957 | +2.7 | same |
| R15 | 6 | 0.999/23/4* | 0.971/1/0* | 1.000/0/0 | 0.999/23/4* | fail (0.54) | 1.32 | -1.34 | 0.944 | +4.8 | same |
| R16 | 44 | 0.998/136/204* | 0.989/20/20* | 0.986/20/30* | 0.998/116/174* | fail (0.37) | 6.75 | +4.24 | 1.060 | -2.4 | same |
| R17 | 76 | 0.998/125/13* | 0.997/16/0* | 0.968/15/8* | 0.998/110/5* | pass (0.10) | 1.91 | -0.50 | 0.775 | +15.4 | same |
| R18 | 37 | 0.999/102/27* | 0.995/20/0* | 0.998/6/5* | 0.999/96/22* | fail (0.17) | 4.03 | -1.74 | 0.829 | +11.8 | same |
| R19 | 25 | 0.999/19/6* | 0.985/1/0* | 0.996/8/5* | 0.999/11/1* | fail (0.31) | 1.39 | -0.59 | 0.928 | +5.4 | Claude Fable 5 in |
| R20 | 21 | 0.998/66/16* | 0.994/0/0 | 0.997/8/3* | 0.998/58/13* | pass (0.08) | 1.17 | +0.55 | 0.928 | +4.9 | same |
| A4_OTIS_Mock_AIME_2024_2025__s22345 | 6 | 1.000/164/130* | 1.000/20/15* | 0.999/54/46* | 1.000/110/84* | pass (0.04) | 4.08 | +2.51 | 1.159 | -11.1 | same |
| LOBO_FrontierMath_Tier_4_2025_07_01_Private__s22345 | 0 | 1.000/0/0 | 1.000/0/0 | 1.000/0/0 | 1.000/0/0 | pass (0.01) | 0.41 | -0.21 | 0.975 | +1.8 | same |

## LOBO, all 57 benchmarks, sorted by frontier max shift

| LOBO benchmark | Models dropped | Frontier max abs shift | Frontier median abs gap change | Stretch change | Fails |
|---|---|---|---|---|---|
| OTIS Mock AIME 2024-2025 (A4) | 6 | 4.08 | 0.73 | +2.51 | S2:all, S3:all, S2:frontier, S3:frontier, S2:sparse, S3:sparse, S2:dense, S3:dense |
| GPQA diamond (A4) | 12 | 1.93 | 0.35 | +1.23 | S2:all, S3:all, S2:frontier, S3:sparse, S2:dense, S3:dense |
| MATH level 5 (A4) | 7 | 1.66 | 0.29 | +0.96 | S2:all, S2:sparse, S3:sparse, S2:dense |
| DTBench (A4) | 15 | 1.61 | 0.30 | -0.95 | S2:sparse |
| LMCA | 9 | 1.32 | 0.28 | -0.86 | S2:sparse |
| ARC-AGI-2 | 1 | 1.14 | 0.10 | +0.15 | S2:all, S2:dense |
| GSO-Bench | 0 | 0.98 | 0.19 | -0.60 | - |
| WeirdML (A4) | 5 | 0.88 | 0.22 | -0.46 | - |
| FrontierMath-Tiers-1-3-v2-Private | 1 | 0.86 | 0.21 | +0.12 | S4 |
| Remote Labor Index | 0 | 0.81 | 0.07 | -0.93 | S4 |
| FrontierMath-Tier-4-v2-Private | 0 | 0.79 | 0.23 | +0.02 | S4 |
| EBR-bench | 1 | 0.73 | 0.21 | -0.01 | S1:frontier, S4 |
| Cybench | 1 | 0.66 | 0.11 | -0.35 | - |
| WeirdML v3 | 0 | 0.61 | 0.26 | -0.04 | S4 |
| Furniture Assembly | 0 | 0.56 | 0.19 | +0.42 | - |
| FrontierSWE | 0 | 0.52 | 0.14 | +0.62 | S4 |
| Chess Puzzles | 1 | 0.51 | 0.14 | +0.43 | - |
| Mystery Game Puzzles | 1 | 0.47 | 0.14 | -0.30 | - |
| MirrorCode | 0 | 0.44 | 0.12 | -0.10 | S4 |
| ProofBench | 1 | 0.44 | 0.18 | -0.15 | S4 |
| Aider polyglot | 1 | 0.42 | 0.08 | -0.24 | - |
| FrontierMath-Tier-4-2025-07-01-Private | 0 | 0.41 | 0.08 | -0.21 | - |
| FrontierCode | 0 | 0.41 | 0.13 | +0.26 | - |
| SpireClimb | 0 | 0.38 | 0.12 | +0.39 | S4 |
| Balrog | 0 | 0.37 | 0.06 | -0.13 | - |
| FrontierMath-2025-02-28-Private | 0 | 0.36 | 0.07 | -0.17 | - |
| ARC-AGI | 2 | 0.33 | 0.17 | +0.55 | S2:dense |
| SimpleQA Verified | 1 | 0.31 | 0.09 | -0.29 | - |
| APEX-Agents | 1 | 0.27 | 0.13 | +0.08 | S4 |
| OSWorld 2.0 | 0 | 0.26 | 0.01 | -0.15 | - |
| Terminal Bench | 1 | 0.25 | 0.03 | -0.11 | - |
| SimpleBench (A4) | 1 | 0.25 | 0.09 | -0.17 | - |
| GDPval | 0 | 0.23 | 0.03 | -0.10 | - |
| CadEval | 0 | 0.18 | 0.03 | -0.10 | - |
| Surface Evolver Bench | 1 | 0.18 | 0.04 | -0.06 | - |
| PostTrainBench | 0 | 0.16 | 0.03 | -0.06 | - |
| MMLU | 20 | 0.14 | 0.02 | +0.08 | S2:all, S2:sparse, S3:sparse |
| ExploitBench | 0 | 0.14 | 0.01 | +0.11 | - |
| VPCT (A4) | 1 | 0.13 | 0.01 | +0.05 | - |
| The Agent Company | 1 | 0.13 | 0.03 | -0.07 | - |
| Fiction.LiveBench | 2 | 0.12 | 0.01 | +0.03 | - |
| Winogrande | 15 | 0.12 | 0.02 | +0.09 | - |
| CL-bench | 0 | 0.09 | 0.02 | -0.07 | - |
| OSWorld | 0 | 0.08 | 0.02 | -0.03 | - |
| METR Time Horizons (A4) | 1 | 0.06 | 0.02 | -0.01 | - |
| CL-bench Life | 0 | 0.05 | 0.02 | -0.09 | - |
| ANLI | 0 | 0.04 | 0.01 | -0.04 | - |
| TriviaQA | 2 | 0.04 | 0.01 | -0.01 | - |
| ARC AI2 | 14 | 0.03 | 0.01 | +0.04 | S2:sparse |
| GSM8K | 14 | 0.03 | 0.01 | +0.04 | - |
| GeoBench | 0 | 0.03 | 0.01 | +0.01 | - |
| HellaSwag | 7 | 0.03 | 0.01 | +0.04 | - |
| BBH | 1 | 0.03 | 0.01 | +0.02 | - |
| LAMBADA | 1 | 0.02 | 0.01 | +0.00 | - |
| DeepResearch Bench | 0 | 0.02 | 0.01 | -0.02 | - |
| OpenBookQA | 1 | 0.02 | 0.01 | +0.00 | - |
| PIQA | 3 | 0.02 | 0.01 | -0.00 | - |

## A4: anchors and scale (raw capability)

Spread = posterior mean of c(GPT-5) - c(Claude 3.5 Sonnet); b = 20 / spread per draw, the ECI points per raw unit. P0: spread 1.957, b CV 0.074. OTIS row from the seed-22345 rerun.

| A4 benchmark | Models dropped | Anchor spread ratio | Scale b ratio | b CV P0 / refit | Median abs shift | Max abs shift (model) | Spearman(shift, P0 ECI) |
|---|---|---|---|---|---|---|---|
| DTBench | 15 | 1.028 | 0.973 | 0.074 / 0.075 | 0.64 | 4.62 (Cerebras-GPT-13B) | +0.12 |
| GPQA diamond | 12 | 0.966 | 1.038 | 0.074 / 0.088 | 0.74 | 6.17 (Cerebras-GPT-13B) | -0.33 |
| MATH level 5 | 7 | 0.911 | 1.099 | 0.074 / 0.082 | 0.91 | 13.91 (Cerebras-GPT-13B) | +0.97 |
| METR Time Horizons | 1 | 1.007 | 0.994 | 0.074 / 0.079 | 0.09 | 0.74 (chatglm2-6b) | -0.20 |
| OTIS Mock AIME 2024-2025 | 6 | 0.857 | 1.169 | 0.074 / 0.087 | 1.74 | 18.36 (Cerebras-GPT-13B) | +0.97 |
| SimpleBench | 1 | 1.010 | 0.991 | 0.074 / 0.075 | 0.17 | 1.61 (Cerebras-GPT-13B) | -0.88 |
| VPCT | 1 | 0.990 | 1.010 | 0.074 / 0.075 | 0.08 | 0.46 (Claude Opus 4.1) | +0.06 |
| WeirdML | 5 | 1.030 | 0.971 | 0.074 / 0.075 | 0.35 | 2.06 (Cerebras-GPT-13B) | -0.92 |


## Findings (exploratory; under Epoch's model)

- A4. Removing METR Time Horizons, SimpleBench, VPCT or WeirdML leaves every stratum and S4 passing (frontier shifts 0.06 to 0.88). Removing OTIS Mock AIME 2024-2025 moves the most: the anchor gap shrinks by 14% (scale b up 17%), 20 of 20 frontier models shift by more than 0.25 W, widths grow by a median 25%, the frontier stretch grows by 2.51 points and the low end falls by 11.1. GPQA diamond (frontier S2 2 of 20), MATH level 5 and DTBench fail S2 or S3 in at least the sparse stratum. Anchor-gap ratios over the other seven are 0.91 to 1.03 and b ratios 0.97 to 1.10. The top-10 set is unchanged in all eight.
- Frontier ranking. Across all 57 LOBO refits the top-10 set never changes; its order changes in 13, by one or two adjacent swaps in 12 (most often Claude Opus 5.5 and GPT-6.1 Sol at ranks 4 and 5) and by GPT-6.1 Sol falling three places without EBR-bench. The S4 adjacent-pair rule fails in 10 LOBO refits (pair-probability changes 0.10 to 0.30 against 0.007 for P0b), all on removals of benchmarks scored mostly by frontier models: APEX-Agents, EBR-bench, both FrontierMath v2 tiers, FrontierSWE, MirrorCode, ProofBench, Remote Labor Index, SpireClimb, WeirdML v3. In the random 20% drops the top-10 set changes in 4 of 20, each time Claude Fable 5 replacing Claude Opus 5 at rank 10, and the top-10 order is unchanged in 3 of 20.
- Frontier gaps. Single removals move the frontier stretch by -0.95 to +2.51 points and frontier models by at most 4.08 (OTIS Mock AIME), then 1.93 (GPQA diamond), 1.66 (MATH level 5), 1.61 (DTBench), 1.32 (LMCA), 1.14 (ARC-AGI-2). Removing OTIS Mock AIME with LMCA stretches the frontier by +1.77 and raises the scale relative to the anchor gap by 18%, a little less than OTIS alone; removing all 16 of F stretches it by +14.25 with 103 models dropped by the inclusion rule. Random 20% drops give stretch changes of -1.74 to +4.24 and frontier max shifts of 0.32 to 6.75.
- How often S1-S4 would fail. LOBO (57): 47 pass S1-S3 in every stratum; failures are S2 in all/dense (5 each), sparse (6), frontier (2: OTIS, GPQA diamond), S3 in all/dense (2), frontier (1), sparse (4), S1 frontier once (EBR-bench, 0.988), S4 10. Clusters: OTIS+LMCA and F16 fail all four strata, FrontierMath fails all and dense and S4, ARC fails all and dense, the old-benchmark cluster passes everything. Random drops: S2 fails in all 20 in the all and dense strata, 17 sparse, 14 frontier; S3 fails 16 all, 13 dense, 15 sparse, 6 frontier; S1 fails frontier 8, sparse 3; S4 fails 17.
- Low end against frontier. Shifts in points are largest at the low end: the median over random drops of the per-quintile median absolute shift is 4.5 points in the bottom P0 quintile (ECI 56 to 109) and 0.6 to 1.0 in the others; the low-end mean shift ranges -14.8 to +15.4 over random drops and -11.1 to +5.7 over LOBO. Relative to each model's 90% width, both tails move more than the middle quintiles that sit between the anchors (random: 0.28, 0.16, 0.17, 0.17, 0.22 of W). Low-end models move without losing any of their own scores: removing OTIS Mock AIME lowers Cerebras-GPT-13B by 18.4 points and removing MATH level 5 by 13.9, with all 6 of its scores kept, and the shift tracks P0 ECI (Spearman 0.97 in both), which indicates a change of scale relative to the anchor gap (scale slope 0.77 to 1.22 over random drops).
- Benchmarks with many low-end models (MMLU, Winogrande, GSM8K, ARC AI2) drop 14 to 20 models each through the inclusion rule and move single remaining models by 9.6 to 21.5 points, while the frontier moves by at most 0.14.
- For comparison, the W5 prior arms P8 and P9 raised the low end by 14.0 and 17.2 points and the stretch by 0.81 and 1.13; a random 20% benchmark drop, or the removal of OTIS Mock AIME alone, moves both by similar or larger amounts.

## Chart wanted (not in the fragment)

A two-panel dot plot from `chart_data.json`: left, one row per benchmark (`lobo`, 57 rows, A4 highlighted), dots at `frontier_max_abs_shift` and `stretch_change`; right, a strip of the 20 random drops and 5 clusters (`refits`, kind random/cluster) on the same two axes, with P0b as the noise reference line.

## Files

- `runs/W/BSEL/design.json` (refit list, dropped benchmarks and models), `fits/<id>.json` (per-refit result, attempts, comparison) and `fits/<id>.npz` (4,000 thinned ECI draws, full-draw means and quantiles, anchor capability draws); reruns as `fits/<id>__s22345.*`.
- `summary.json`, `chart_data.json`, `fragment.html`.
- Code: `eci_work/tools/bsel_common.py`, `bsel_design.py`, `bsel_run_entry.py`, `run_bsel.sh`, `mem_watchdog_bsel.sh`, `bsel_agg.py`, `bsel_report.py`, `bsel_py.sh`.
