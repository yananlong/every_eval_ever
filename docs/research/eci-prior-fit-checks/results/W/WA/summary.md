# WA summary: sensitivity to the two anchor models (M11a, R28; exploratory, no gate)

Inputs: the three W2 fits (seeds 12345, 22345, 32345; 4,000 draws each, 12,000 pooled), post-processing only, no sampling. Files: `anchor_pairs.json` (the pairs, committed before any result), `a1.json`, `a2.json`, `fig_width_ratios.png`, `fig_invariance.png`. A3 (the W5 grid) is prepared and tested on W2 draws only; it runs after W5.

## What the saved draws are
The `capability` draws in the traces are raw (pre-anchor; range -13.10 to 3.59). The stored `eci` draws are Epoch's per-draw map of them,
$$\mathrm{ECI}^{(s)}_m = 130 + 20\,\frac{c^{(s)}_m - c^{(s)}_{\text{Claude 3.5 Sonnet}}}{c^{(s)}_{\text{GPT-5}} - c^{(s)}_{\text{Claude 3.5 Sonnet}}},$$
checked against `bayesian.py` (e04929a, `_anchor_transform`): recomputing it from `capability` reproduces the stored `eci` to $3\times10^{-14}$, and the two anchors sit at exactly 130 and 150 in every draw. Every re-anchoring below was computed twice, from `eci` and from `capability`, and agrees to at most $7\times10^{-13}$ ECI points.

## The pairs (pre-declared rule, M11a)
Eligible models: at least 20 observed scores and posterior SD of capability below the median. Only 32 of 256 models have 20 or more scores, all 32 pass the SD condition (the condition does not bind), and they span P0 mean ECI 141.9 to 169.0. So **every alternative anchor lies in the top part of the scale**, and the original low anchor (130, 12 scores) is not itself eligible. The original pair is kept as a reproduction check: re-anchoring on it returns the stored draws to within $2\times10^{-13}$. Seven alternative pairs follow from the rule (three of the nine combinations of low position and span had no eligible high anchor): see `anchor_pairs.json` and the table in M11a. New anchor values are the models' P0 posterior-mean ECI, so each new scale agrees with Epoch's at its own anchors on average. No pair is unstable (no draw has the high anchor at or below the low one).

## What the anchoring cannot change (exact)
For every pair, on every seed and pooled: the within-draw rank of every model, $P(i > j)$ for all 32,640 model pairs, and $P(\text{top } 10)$ for every model are identical to those under Epoch's anchors. **Maximum absolute differences: ranks 0 (integer), $P(i>j)$ 0.0, $P(\text{top }10)$ 0.0** (over all 8 pairs x 4 draw sets; `a1.json`, `fig_invariance.png` left). The reason is that each draw is mapped by a positive affine function, which cannot reorder models inside that draw. Consequences: S4's top-10 set is the same and its largest adjacent-pair probability change is 0.000 for every pair; the 20 models of the frontier stratum keep their order within every draw.

## What it can change (A1, 12,000 pooled draws against the original anchoring)
| Pair | Width ratio, median (min, max) | Median ratio: frontier / sparse | S3 count, all (frontier of 19 or 20) | S2 count | S1 all / frontier / sparse | Largest change in a top-10 gap, points (relative) | Posterior-mean rank: largest change, models changed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `L0-S10` | 1.128 (0.90, 1.39) | 1.148 / 1.142 | 45 of 252 (0 of 20) | 0 | 1.00000 / 1.00000 / 0.99997 | 0.030 (0.011) | 1, 4 of 256 |
| `L0-S15` | 1.006 (0.69, 1.15) | 0.749 / 1.019 | 39 (18 of 20) | 0 | 1.00000 / 1.00000 / 0.99997 | 0.014 (0.041) | 1, 4 |
| `L0-S20` | 0.959 (0.52, 1.08) | 0.580 / 0.972 | 44 (19 of 19) | 0 | 1.00000 / 1.00000 / 0.99997 | 0.006 (0.017) | 1, 4 |
| `L6-S10` | 1.208 (0.56, 1.68) | 0.631 / 1.208 | 155 (19 of 19) | 0 | 1.00000 / 1.00000 / 1.00000 | 0.025 (0.041) | 0, 0 |
| `L6-S15` | 1.098 (0.46, 1.44) | 0.554 / 1.108 | 109 (19 of 19) | 0 | 1.00000 / 1.00000 / 0.99997 | 0.026 (0.049) | 1, 4 |
| `L12-S10` | 1.339 (0.49, 2.02) | 0.584 / 1.317 | 187 (19 of 19) | 0 | 1.00000 / 1.00000 / 0.99997 | 0.040 (0.455) | 1, 2 |
| `Full` | 0.936 (0.46, 1.07) | 0.556 / 0.946 | 41 (19 of 19) | 0 | 1.00000 / 1.00000 / 0.99997 | 0.013 (0.027) | 1, 4 |

In plain language:
- **Interval widths do depend on the anchors, and a lot.** Over the seven pairs, pooled per-model 90% width ratios run from 0.46 to 2.02, and the median over models from 0.94 to 1.34 (`fig_width_ratios.png`). The seed-to-seed spread of the median ratio is at most 0.04, so this is not Monte Carlo noise. The pattern is geometric: a model close to the anchors inherits little uncertainty from the scale factor, and a model far from them inherits more. Anchors placed at the frontier (all pairs except `L0-S10`) shrink frontier intervals to 0.55 to 0.75 of the original width (the original high anchor, 150, is 10 to 23 points below the frontier models, 160 to 173), and widen the old and sparse models in the range of `L6-S10` and `L12-S10` (median ratio about 1.2 to 1.3). The scale factor's spread (SD/mean of $b^{(s)}$) is 0.047 to 0.100 for the alternative pairs against 0.075 for the original, and its log is only weakly correlated with the original's (0.11 to 0.24).
- **Under the M3 thresholds as a reference only**, S3 (width ratio outside 0.8 to 1.25) would be exceeded by 39 to 187 of 252 non-anchor models, and nearly every frontier model (18 to 19 of 19) for pairs that put the high anchor at or above 157. Posterior means barely move: S2 is 0 for every pair (largest shift of a posterior mean 0.85 ECI points, `L0-S10`; median 0.02 to 0.17 points), and S1 is at least 0.99997 in every stratum. No verdict follows from these flags (M11a).
- **Gaps and ranks: practically unchanged.** The nine adjacent gaps in the baseline top-10 order (from 0.04 to 3.66 points) change by at most 0.040 points pooled (0.043 on a single seed), and by at most 5% of the gap in relative terms except `L12-S10`, where the 0.09-point gap between Claude Sonnet 5.5 and Gemini 4 Argon becomes 0.13 (relative change 0.455; absolute 0.04). Posterior-mean ranks change by at most 1 place pooled (at most 2 on a single seed) and for at most 4 of 256 models (5 on a seed); no model in the top 20 changes rank. Every pooled swap is between models whose original posterior means differ by at most 0.003 ECI points, that is, tied means.
- **Anchor models gain or lose an interval.** Under Epoch's anchors the two anchors have no interval. Under the alternatives, Claude 3.5 Sonnet's 90% width is 5.2 to 9.9 points and GPT-5's 2.6 to 4.0 points (`a1.json`, `anchor_widths_pooled`); Claude 3.5 Sonnet has only 12 scores (capability SD 0.167, against 0.09 to 0.12 for the eligible models), so fixing it removes an uncertainty of about 5 to 10 points from the displayed intervals and moves it into the other models' widths. Conversely the alternative anchors have widths of 3.1 to 6.2 points under Epoch's scale.

## A2: anchor-free standardisation (12,000 pooled draws)
Per draw, capabilities are standardised across the 256 models: $z^{(s)}_m = (c^{(s)}_m - \bar c^{(s)})/\mathrm{SD}^{(s)}(c)$, and a robust variant with the median and $\mathrm{IQR}/1.349$. Both are per-draw positive affine, so the exact invariance holds again (differences 0 in ranks, $P(i>j)$, $P(\text{top }10)$). To compare with ECI, each is expressed in ECI-equivalent units by fixed constants from the P0 posterior means (mean 130.83 and SD 26.98 for the z-score; median 138.86 and IQR/1.349 25.96 for the robust variant).

| Scale | Width ratio vs Epoch's: median (min, max); frontier / sparse | S3 count, all of 254 | S2 count | S1 all | Largest top-10 gap change (points) | Rank: largest change, models changed | Largest posterior-mean shift (points) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| z-score | 0.876 (0.44, 0.99); 0.886 / 0.892 | 59 | 0 | 1.00000 | 0.002 | 2, 3 | 0.54 |
| Robust (median, IQR) | 0.843 (0.65, 1.00); 0.764 / 0.843 | 84 | 0 | 1.00000 | 0.027 | 2, 5 | 0.61 |

What an anchor-free scale would change for readers:
- Every model has an interval, including Claude 3.5 Sonnet (z-score: 5.1 ECI-equivalent points, 90% width) and GPT-5 (2.3 points); Epoch's display shows none for them.
- Intervals are narrower than under Epoch's anchors (median 0.84 to 0.88 of the width) and no model is wider (largest ratio 0.99 for the z-score and 1.00 for the robust scale), because the SD or IQR of 256 models is far better determined than the gap between two models. This is consistent with part of the width Epoch shows for non-anchor models being the cost of tying the scale to two specific models.
- Orderings, comparisons between models and top-10 statements are identical; gaps between the leading models move by under 0.03 points.
- The cost is meaning: values are no longer on the 130/150 scale that readers know (in z units the P0 anchors sit at -0.04 and 0.71), they depend on which models are in the fitted set (adding a batch of weak models shifts the mean and SD), and they cannot be compared across releases without a reference. A reporting convention that keeps Epoch's scale for the headline and adds the z-scored interval as a check would carry both.

## A3 and the optional A4
`runs/wa_w5_anchor.py` repeats A1 on the W5 grid (each entry and P0 re-anchored on each pair; reports whether any S1 to S3 or S4 pass flag changes against the original anchoring). Tested on W2 draws as a stand-in (seed 22345 and 32345 against seed 12345): all eight pairs ran, within-entry invariance 0, and no flag changed. It runs once `runs/W/W5/*.npz` exists. A4 (leave-one-benchmark-out refits for the eight benchmarks on which both anchors have scores) is specified in M11a and not run.

## Limits
The alternative anchors lie in the top 27 points of the scale because no other model has 20 scores; a pair that included a low-ECI anchor (for example a well-measured older model) is not tested. Only the W2 fit (default priors) is re-anchored; A3 will extend this to the prior grid. The z-scores depend on the 256-model set.
