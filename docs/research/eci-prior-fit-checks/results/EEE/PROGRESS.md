# Mirror of the ECI fit checks on EEE data: progress note

Updated 2026-11-21 07:55 UTC. Results hold under Epoch's model. This note replaces the 07:40 version, whose fit input contained a model-map error (see Audit).

## Data
- EEE: latest flat manifest 959f0e11 (2026-11-20T08:30Z, 127,491 aggregate records, 129 collections) at Hugging Face revision 5bce4753 (2026-11-20T11:34Z). All 127,491 object hashes verified. Difference from the pinned dd7efcff (2026-11-13): 4,630 records added, none removed.
- Crosswalk: 101 map entries included for 33 of the 57 ECI benchmarks; 1,356 EEE model ids mapped to 220 of the 256 fitted groups; 1,256 pairs (520 independent, 312 same-upstream, 424 upstream-unknown). Same-upstream control: median absolute difference 0.0000 (limit 0.02), 92% equal to 3 decimals.
- Audit: first sample (seed 20261113) failed, 8 errors in 50, all on the source class (benchmark home URL read as the score's reference). Fixed and rebuilt; second sample (seed 20261114) 0 errors in 50. A later check of the anchors found that the undated id `claude-3.5-sonnet` had been matched to the June 2024 group and carried an October 2024 score into the low anchor. Undated ids that fit two dated groups and rolling aliases are now left ambiguous. Rebuilt; third sample (seed 20261115) 0 errors in 50 (95% upper bound 5.8%). The fits started on the earlier input were stopped and set aside.

## Fit input (primary variant)
- Epoch's 2,879 cells, 256 models, 57 benchmarks, kept as they are. 688 cells (23.9%) have an EEE score: 280 independent, 210 same-upstream, 198 upstream-unknown. The EEE score replaces Epoch's in those cells (independent preferred, then same-upstream, then upstream-unknown; highest across sources within the class). 2,191 cells keep Epoch's value.
- 366 cells (12.7%) differ from Epoch's value by more than 0.0015; 241 by more than 0.02; 135 by more than 0.05; 71 by more than 0.10. Mean signed difference over the covered cells: -0.0027.
- 201 of 256 models and 33 of 57 benchmarks have at least one EEE cell. GPQA diamond carries 149 of the 280 independent cells. Both anchors remain: Claude 3.5 Sonnet 2 of 12 cells from EEE (GPQA diamond 0.403 to 0.431, MMLU 0.820 to 0.872), GPT-5 6 of 28 (2 changed: GPQA diamond 0.850 to 0.852, Terminal Bench 0.496 to 0.371).
- An EEE-only matrix is too thin: 48 models meet Epoch's inclusion rule and Claude 3.5 Sonnet is not one of them, so the plan's B5 size condition (15 benchmarks, 100 models) fails. It was not fitted.

## W2 on the EEE input
| Quantity | Epoch data | EEE data |
|---|---|---|
| Seeds converged | 3 of 3 | 3 of 3 |
| Divergences, seed 12345 | 0 | 0 |
| Max R-hat, seed 12345 | 1.0043 | 1.0054 |
| Min ESS, seed 12345 | 1,076 | 1,680 |
| Largest seed-to-seed SD of a posterior-mean ECI | 0.25 | 0.29 |
| elpd LOO | 3,450 | 3,386 |

ECI, EEE-data fit against Epoch-data fit (seed 12345, 254 non-anchor models):
- Spearman 0.9994 (frontier 20: 0.9985). All 254 pairs of 90% intervals intersect.
- Frontier: mean shift +0.08 points, largest 0.28 (Claude Opus 5); no frontier model moves by a quarter of its interval width. Top 10 is the same set; ranks 4 and 5 swap (Claude Opus 5.5 and GPT-6.1 Sol, 0.03 apart in the Epoch-data fit).
- All models: median absolute shift 0.32, 51 models shift by more than 2 points, 28 by more than a quarter of their interval width (the W5 limit for S2 is 12). The largest shift is 13.5 points (Cerebras-GPT-13B, interval width 41).
- The largest shifts are all upward and all in weak 2023 models with no changed cell of their own (82 models have none). Their scores did not change; the benchmarks they sit on were re-estimated from other models' EEE scores.

## Status (2026-11-21 21:05 UTC): all stages done
- W3: 192 of 199 G-null replicates converged (5 timeouts); misfit generators converged 9, 20, 18, 19, 15 of 20 (G-2D, G-offset, G-shape, G-disp, G-drift); 5 G-2D replicates crashed in anchoring. 90% coverage 0.875 (frontier 0.868).
- W4: T1 and T2 reject at 0.01 family-wise (adjusted p 0.0052); T5 does not (0.016). Held-out coverage 0.900, no benchmark flagged. F has 17 benchmarks; C2 falsified.
- W5: P8 and P9 fail (58 and 61 models over 0.25 W); C1 falsified. P1 to P10 all resolved at the first attempt; J2 unresolved (2 h cap).
- Anchors: rankings unchanged, largest gap change 1.00 point.
- Deliverables: SUMMARY.md, fragment.html, chart_data.json, side_by_side.json, headline.json.
