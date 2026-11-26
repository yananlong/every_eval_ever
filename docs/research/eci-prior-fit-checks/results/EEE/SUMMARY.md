# Mirror of the ECI prior and fit checks on EEE data

Results hold under Epoch's model. Epoch-data column: runs/W/. EEE-data column: runs/EEE/, the same scripts, seeds, caps and rules run on Epoch's 2,879 cells with EEE scores substituted where a matched EEE score exists (688 cells, 366 changed). Generated 2026-11-21.

## Crosswalk audit

- EEE manifest 959f0e11 (2026-11-20T08:30Z, 127,491 records, 129 collections), Hugging Face revision 5bce4753a80399062c1a2988715a6ad7e33528b9. All sha256 verified. Against the pinned dd7efcff: +4,630 records, none removed.
- Maps (CSV, runs/EEE/crosswalk/): benchmark_map.csv (101 included entries, 33 benchmarks), model_map.csv (1,356 ids mapped to 220 fitted groups; 99 ambiguous-model), source_class.csv, collection_screen.csv (129 collections), pairs.csv (1,256 pairs: 520 independent, 312 same-upstream, 424 upstream-unknown).
- Same-upstream control: median absolute difference 0.0000 (limit 0.02).
- Audit (rule: at most 2 errors in 50): first sample, seed 20261113, 8 errors, fail (source class; benchmark home URL read as the score reference). Second sample, seed 20261114, 0 errors (2 under stricter readings). A post-audit check found a model-map error in the low anchor (undated claude-3.5-sonnet matched to the June 2024 group); fixed, rebuilt. Third sample, seed 20261115, 0 errors, pass, 95% upper bound 5.8%. The third sample is outside the registered path (one re-audit). Files: audit_sample_first_20261113.csv, audit_facts_20261114.txt, audit_sample.csv, audit_result.json.

## Coverage

- 688 of 2,879 cells have an EEE score (23.9%): 280 independent, 210 same-upstream, 198 upstream-unknown. 366 cells differ from Epoch's value by more than 0.0015, 241 by more than 0.02, 135 by more than 0.05, 71 by more than 0.10.
- 201 of 256 models and 33 of 57 benchmarks have at least one EEE cell (55 models none, 94 one or two, 70 three to five, 37 six or more). By benchmark and by model: input/coverage_by_benchmark.csv, input/coverage_by_model.csv.
- Primary variant: EEE score where available, class priority independent, same-upstream, upstream-unknown, highest across sources within the class. Other cells keep Epoch's value. Same-upstream scores are used (they equal Epoch's in 92% of pairs).
- Anchors: Claude 3.5 Sonnet 2 of 12 cells from EEE (GPQA diamond 0.403 to 0.431, MMLU 0.820 to 0.872). GPT-5 6 of 28 (changed: GPQA diamond 0.850 to 0.852, Terminal Bench 0.496 to 0.371).
- EEE-only matrix: 48 models meet Epoch's inclusion rule, Claude 3.5 Sonnet not among them. Not fitted (B5 size condition fails).

## ECI: Epoch-data fit against EEE-data fit

| Stratum | Models | Spearman | Mean shift | Median abs shift | Largest shift | Moved > 0.25 W | Intervals intersect | Median width ratio |
|---|---|---|---|---|---|---|---|---|
| All non-anchor models | 254 | 0.9994 | +1.01 | 0.32 | 13.5 | 28 | 100% | 1.01 |
| Frontier | 20 | 0.9985 | +0.08 | 0.10 | 0.3 | 0 | 100% | 1.04 |
| Sparse (6 or fewer scores) | 72 | 0.9976 | +2.31 | 1.43 | 13.5 | 15 | 100% | 0.95 |
| Dense | 182 | 0.9995 | +0.50 | 0.21 | 7.5 | 13 | 100% | 1.02 |


Top 10: same set, ranks 4 and 5 exchanged (Claude Opus 5.5, GPT-6.1 Sol). Largest frontier shift 0.28 points. Mean shift by ECI band: below 80 +8.0 (19 models), 80 to 100 +3.5 (23), 100 to 120 -0.1, 120 to 140 +0.1, 140 to 160 +0.2, 160 and above +0.1. Largest shift +13.5 (Cerebras-GPT-13B, no changed cell). EDI shifts: TriviaQA +20.2, LAMBADA +12.7, PIQA +12.4, HellaSwag +10.5. G5 as registered (Spearman at least 0.9, at least 80% of intervals intersecting) is met: 0.9994 and 100%, read on the substitution matrix. Files: eci_compare.json, eci_compare.csv, edi_compare.csv.

## Side by side: every headline number

### W2 reproduction fit

| Quantity | Epoch data | EEE data |
|---|---|---|
| Seeds converged (of 3) | 3 | 3 |
| Divergences, seed 12345 | 0 | 0 |
| Max R-hat, seed 12345 | 1.0043 | 1.0054 |
| Min bulk ESS / min tail ESS | 1,076 / 1,307 | 1,680 / 2,032 |
| elpd LOO (SE); p_loo | 3,450 (57); 443 | 3,386 (57); 450 |
| Largest seed-to-seed SD of a posterior-mean ECI | 0.25 | 0.29 |

### W3 simulation study

| Quantity | Epoch data | EEE data |
|---|---|---|
| G-null replicates converged | 187 of 199 | 192 of 199 |
| G-null timeouts at the 60-minute cap | 3 | 5 |
| 90% interval coverage of ECI, all models (90% CI) | 0.882 (0.871 to 0.893) | 0.875 (0.865 to 0.886) |
| 90% interval coverage of ECI, frontier | 0.903 | 0.868 |
| 90% coverage, sparse / dense models | 0.872 / 0.886 | 0.874 / 0.876 |
| 50% interval coverage of ECI, all models | 0.480 | 0.470 |

### W3 power

| Quantity | Epoch data | EEE data |
|---|---|---|
| Noise-level check (T3) on G-disp: rejections of converged fits | 19 of 19 | 19 of 19 |
| Residual-correlation check (T2) on G-2D: rejections of converged fits | 7 of 7 | 9 of 9 |
| Lab-by-benchmark check (T5) on G-offset: rejections of converged fits | 0 of 18 | 1 of 20 |
| Time-drift check (T4) on G-drift: rejections of converged fits | 0 of 16 | 0 of 15 |
| Curve-shape check (T1) on G-shape: rejections of converged fits | 2 of 14 | 3 of 18 |

### W3 convergence

| Quantity | Epoch data | EEE data |
|---|---|---|
| G-2D replicates with a usable fit (of 20) | 7 | 9 |
| G-2D replicates that crashed in anchoring | 3 | 5 |
| Converged of 20: G-offset / G-shape / G-disp / G-drift | 18 / 14 / 19 / 16 | 20 / 18 / 19 / 15 |

### W3 positive control

| Quantity | Epoch data | EEE data |
|---|---|---|
| Seeds on which the control fails S1 to S4 in the all-models or frontier stratum (of 3) | 3 | 3 |
| Seed 12345: S2 count / S3 count in all models (limit 12); frontier fails | 57 / 60; no | 56 / 56; no |

### W3 SBC (M13)

| Quantity | Epoch data | EEE data |
|---|---|---|
| Parameters flagged at the Bonferroni level (of 311) | 33 | 22 |

### W3 gate G1

| Quantity | Epoch data | EEE data |
|---|---|---|
| Interpretation unqualified (all G1 conditions met) | no | no |

### W3M rank tests (Modrak-style)

| Quantity | Epoch data | EEE data |
|---|---|---|
| ECI (254 models): gamma-flagged; central 90% share | 0; 0.88 | 0; 0.88 |
| EDI (57 benchmarks): gamma-flagged; central 90% share | 20; 0.87 | 15; 0.86 |
| Slope (57): gamma-flagged; central 90% share | 46; 0.75 | 41; 0.76 |
| Sigma (57): gamma-flagged; central 90% share | 30; 0.87 | 30; 0.87 |
| Replicates used | 180 | 192 |
| Joint log-likelihood: gamma p; mean rank | 0.0001; 0.39 | 0.0000; 0.38 |
| Pearson dispersion: gamma p; mean rank | 0.00005; 0.20 | 0.00005; 0.17 |

### W4 residual checks

| Quantity | Epoch data | EEE data |
|---|---|---|
| Converged model-true replicates in the reference | 187 | 192 |
| Curve-shape (T1): observed; max-T adjusted p | 4.503; 0.0053 | 4.471; 0.0052 |
| Residual-correlation (T2): observed; max-T adjusted p | 3.402; 0.0053 | 3.210; 0.0052 |
| Noise-level (T3): observed; max-T adjusted p | 0.081; 0.8138 | 0.090; 0.0933 |
| Time-drift (T4): observed; max-T adjusted p | 0.022; 1.0000 | 0.021; 1.0000 |
| Lab-by-benchmark (T5): observed; max-T adjusted p | 4.455; 0.0053 | 3.861; 0.0155 |
| Floor-and-ceiling (T6): observed; max-T adjusted p | 11.561; 0.2181 | 13.356; 0.2021 |
| Per-model fit (T7): observed; max-T adjusted p | 3.644; 0.8936 | 3.032; 0.9896 |
| Checks rejected at 0.01 family-wise | T1, T2, T5 | T1, T2 |
| T2: SDs above the mean of the model-true replicates | 29.9 | 26.7 |

### W4 marginal fit

| Quantity | Epoch data | EEE data |
|---|---|---|
| Held-out 90% coverage (rows) | 0.898 (2,704) | 0.900 (2,704) |
| LOO 90% coverage | 0.895 | 0.900 |
| Benchmarks flagged (of tested) | 0 of 44 | 0 of 44 |

### W4 localisation

| Quantity | Epoch data | EEE data |
|---|---|---|
| Benchmark pairs with q > 3.84 (share); median q | 0.26; 1.25 | 0.24; 1.25 |
| Developer-by-benchmark cells with |t| > 2 (share) | 0.16 | 0.17 |
| Benchmarks in the localisation set F (limit 10) | 16 | 17 |
| Rows deleted with F (of 2,879) | 1,398 | 1,412 |
| T1 after deleting F: unadjusted p | 0.0055 | 0.0052 |
| T2 after deleting F: unadjusted p | 0.0055 | 0.0052 |
| T5 after deleting F: unadjusted p | 0.0110 | 0.0052 |

### W4 verdict

| Quantity | Epoch data | EEE data |
|---|---|---|
| Model-adequacy claim (C2) | falsified | falsified |

### Anchors

| Quantity | Epoch data | EEE data |
|---|---|---|
| Largest change in a posterior-mean gap over the alternative anchor pairs (points) | 1.27 | 1.00 |
| Median per-model interval-width ratio, range over pairs | 0.93 to 1.33 | 0.93 to 1.36 |
| Uncertainty of gaps between frontier models, median ratio, range over pairs | 0.96 to 1.03 | 0.97 to 1.05 |
| Common change of unit, range over pairs | 1.001 to 1.010 | 1.001 to 1.009 |
| Per-model interval-width ratio, min to max over the pre-declared pairs | 0.46 to 2.02 | 0.44 to 1.98 |
| Largest shift of a posterior-mean ECI over the pre-declared pairs (points); models moved by more than 0.25 W | 0.88; 0 | 0.86; 0 |
| Within-draw rankings and P(i>j) changed by re-anchoring (largest change) | 0.000 | 0.000 |

### W5 prior sensitivity

| Quantity | Epoch data | EEE data |
|---|---|---|
| Verdict label; unresolved priors | Sensitive; P3 | Sensitive; none |
| Priors failing S1 to S4 (strata) | P8 (all, sparse); P9 (all, sparse) | P8 (all, sparse); P9 (all, sparse) |
| P8: models moved by more than 0.25 W, all models (limit 12); frontier (limit 1) | 59; 0 | 58; 0 |
| P8: interval-width ratio outside 0.8 to 1.25, all models (limit 12) | 57 | 51 |
| P8: mean shift of models below ECI 100 (count); largest shift; largest frontier shift (points) | +14.0 (42); 23.4; 1.1 | +9.9 (36); 14.3; 1.2 |
| P9: models moved by more than 0.25 W, all models (limit 12); frontier (limit 1) | 61; 0 | 61; 0 |
| P9: interval-width ratio outside 0.8 to 1.25, all models (limit 12) | 59 | 57 |
| P9: mean shift of models below ECI 100 (count); largest shift; largest frontier shift (points) | +17.2 (42); 28.8; 1.7 | +13.0 (36); 19.0; 1.9 |
| Smallest rank correlation with the baseline over P1 to P10 | 0.9998 | 0.9998 |
| Top 10 unchanged under every resolved prior P1 to P10 | yes | yes |
| Hyperprior and noise priors (P1, P2, P4 to P7, P10) with any S2 or S3 count above 0 | 0 | 0 |
| S5 power-scaling screen flags | 0 | 0 |
| Reference prior PR: S2 / S3 counts, all models | 62 / 60 | 64 / 58 |
| Jeffreys prior J2: S2 / S3 counts, all models | 40 / 21 | unresolved (2 h cap) |
| Prior arms on which T1, T2 and T5 all reject (of arms checked) | 19 of 19 | 0 of 16 |
| Prior arms on which T1 and T2 both reject (of arms checked) | 19 of 19 | 16 of 16 |
| T5 max-T adjusted p across the prior arms, range | 0.0053 to 0.0053 | 0.0104 to 0.0207 |

## Reading

- Same on both matrices: W2 converges cleanly; 90% coverage in the 0.85 to 0.95 band; power pattern (T3 yes, T2 conditional on convergence, T5, T4, T1 low); positive control fails on 3 seeds; T1 and T2 reject at 0.01 family-wise; held-out and LOO coverage near 0.90, no benchmark flagged; F above 10 and T1, T2 not localised, so C2 is falsified; P8 and P9 fail S2 and S3 in the all-models stratum, so C1 is falsified; anchors move widths and leave rankings.
- Different: T5 does not reject on EEE data (adjusted p 0.016; Anthropic on GPQA diamond no longer extreme). Frontier coverage 0.868 against 0.903. Weak models rise by up to 13.5 points through re-estimated benchmark difficulties. elpd LOO falls from 3,450 to 3,386. P3, P9, P10 resolve at the first attempt; J2 times out.
- Limits: 2,191 cells unchanged by construction; 210 covered cells are copies of Epoch's sources; one benchmark (GPQA diamond) carries over half of the independent cells.

## Deviations and wall-clock

- Wall-clock (UTC, 2026-11-21): crosswalk and audits 06:05 to 07:45; W2 07:45 to 07:51 (6 fits in parallel); W3 07:51 to 10:14 (27 fits in parallel, 2 h 23 min); W5 arms 08:24 to 11:19 on spare cores (J2 at the 2 h cap); idle 11:19 to 20:37 (agent interrupted); W3M, W4, W4d, anchors, W5 aggregation 20:37 to 21:05. Peak memory 62 GB.
- Deviations: latest manifest instead of dd7efcff; third audit sample; pair defined with source class; FrontierMath refinement of rule 5; metric identity for FrontierCode, FrontierSWE and OSWorld 2.0 decided against Epoch's values, PostTrainBench excluded; substitution matrix instead of the plan's EEE-only B5; scripts run unchanged from a mirror work root (runs/EEE/_mirror); W1 output copied; 1 thread per chain process (W4 on Epoch data used 8); W3M on 192 W3 fits with no refits; anchor extension uses the EEE fit's own pre-declared pairs and its five crashed G-2D replicates; C2 verdict file assembled by tools/eee_w4d_verdict.py with the G3 rule; A3 and A4 not run. A first W2 and partial W3 on an input with the model-map error were stopped and moved to runs/EEE/_superseded_v1. Full text: runs/deviations_local.md.