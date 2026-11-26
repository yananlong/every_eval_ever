# Executive summary for the "ECI Prior and Fit Checks" artifact: brief, claim ledger, approved outline

Approved by the author on 2026-11-22 with the defaults below. "Interpreting ECI" (epoch.ai/data-insights/interpreting-eci, dated 2025-11-06) is stale: do not use it as a source for Epoch's claims and do not include a row or sentence about it. Use only the current pages: https://epoch.ai/eci, https://epoch.ai/data/eci-documentation/methodology, https://epoch.ai/publications/eci-bayesian-methodology.

## Brief
- Job: an executive summary placed at the top of the published page, after the header and contents nav and before `<section id="summary">` (section 1). Unnumbered, heading "Executive summary", `<section id="exec">`, plus a nav link "Executive summary" first in the contents nav.
- Reader: technically literate readers of an EvalEval blog post / report (ML evaluation researchers, people who use ECI); not necessarily Bayesian specialists.
- Register: technical report. Results hold "under Epoch's model"; use "suggests"/"indicates" for interpretation; registered-rule wording exact (C1, C2 "falsified"). No em dashes. Never write "null" in prose ("model-true replicates"). No signpost adverbs, no kickers.
- Format: HTML matching the page (see the page file); table markup like section 1.3: `<div class="fig"><div class="tblwrap"><table>` with thead/tbody; verdict cells use `<span class="pill pass">`, `<span class="pill fail">`, or `<span class="pill pend">`. Links to Epoch use the verified `fragment_url` values from epoch_claims.json; internal links use the page's existing ids (#anchors, #real, #w4b, #prior, #prior-anchors, #prior-benchmarks, #status, #claims, #t1, #t2, #t5).
- Budget: about 450 words of prose plus the table (12 rows at most).
- Defaults taken: (1) the EEE rows stay, marked "EEE mirror, section to come" (the EEE section is not yet on the page); (2) the header dek paragraph is shortened to two sentences, since the executive summary carries the detail; (3) the two sentences that say every residual check uses z are corrected (T6 does not use z; see below).

## Claim ledger (assert nothing outside it; copy numbers from the sources)
| ID | Claim | Status | Source |
|---|---|---|---|
| E1 | ECI: one-dimensional Beta IRT, 2,879 scores, 256 models, 57 benchmarks, anchors Claude 3.5 Sonnet 130 and GPT-5 150 | ready | page section 1.1 |
| E2 | Computation sound: 0 divergences, max R-hat 1.004; 90% coverage 0.882 in simulation (0.903 frontier); held-out 0.898, LOO 0.895 | ready | page 1.3 |
| E3 | C2 falsified: T1, T2, T5 reject at adjusted p 0.0053 (beyond all 187 model-true replicates); misfit spans 16 benchmarks; deleting them leaves T1 and T2 rejecting (p 0.0055) | ready | page 1.3 |
| E4 | How far the misfit moves ECI has not been measured (W6 pending) | careful: must sit in the same paragraph as E3 | page 1.4, 1.5 |
| E5 | C1 falsified at the low end: P8/P9 move 59/61 of 254 models by more than a quarter of their interval width (limit 12); 42 models below ECI 100 rise 14 to 17 points on average, up to about 29 under P9; frontier rises at most 1.7; top-10 set unchanged | ready | page 1.3, dek |
| E6 | Only first place is clear: lead 3.64 points; ranks 2 to 9 within 3.29 points; most adjacent pairs ordering probability 0.51 to 0.76; top-10 set in 64.7% of posterior draws; exact top-10 order in 0.75% | ready | runs/EXEC/top10_ranks.json |
| E7 | Benchmark choice: removing OTIS Mock AIME stretches the frontier by 2.5 points and shifts every frontier model by more than a quarter of its interval width; random 20% drops move the low end by -15 to +15 | ready | page 1.3, section 15.5 |
| E8 | Anchors: values only rescale; other anchor pairs leave rankings and P(i>j) unchanged and move single-model widths by x0.45 to x2.01; with GPT-4o mini as the low anchor P9 also fails at the frontier | ready | page 1.3, section 11, 15.4 |
| E9 | EEE mirror (source resampling, 89 refits): frontier spread (SD) at most 0.38, top-10 set never changes; T5 rejects in 8 of 50 any-source refits, 1 of 20 independent-only, 0 of 19 own-run (adjusted p mostly 0.0104 against 0.01) | careful: not yet a page section; label "EEE mirror, section to come" | runs/EEE/PROV/SUMMARY.md, summary.json |
| E10 | Below ECI 100 the scale rests mostly on developer-reported scores: 13 benchmarks, 463 cells, mean ECI 95.7 | careful: our classification derived from Epoch's per-row source strings | runs/TAX/epoch_source_cells.csv, epoch_source_by_benchmark.csv |
| E11 | Pairwise probabilities are probably overconfident given correlated residuals | careful: untested inference, say so | (inference) |
| E12 | Epoch's public claims, verbatim and linked | ready: use only verified wording | runs/EXEC/epoch_claims.json (ids 1 to 14, 16) |
| E13 | Epoch's published Bayesian fit uses 2,810 scores, our snapshot 2,879 (2026-11-13 zip): slightly different data versions | ready | epoch_claims.json / Bayesian post; page 1.1 |

## Approved outline
1. Bottom line (E1 to E5): what ECI is; what holds (computation, calibration); what fails (fit, C2; low end under priors, C1); E4 in the same paragraph.
2. How to read ECI rankings (E6 to E8): tiers, not ranks; gaps depend on the benchmark set; anchors.
3. Lead-in (E12, E13): one sentence on how Epoch's public claims (current pages) were compared with these results, noting the data-version difference.
4. Table "Epoch's claim (linked) | What we find under Epoch's model | Verdict" (E2, E3, E5 to E12), rows corrected as below.
5. Close (E4): where Epoch's documentation is candid and where it overstates the interpretation; pointers to sections 11, 14, 15 and to what is pending (W6, EEE section).

## Baseline table rows (corrected after verification; rewrite cleanly, keep the substance)
1. Single "broad, underlying capability"; unidimensionality stated as an assumption (ids 1, 2). Ours: T2 residual correlations and T1 within-benchmark trends reject in every variant; Epoch's reported checks (PIT, coverage, PPP variance and IQR; id 3) target the marginal spread, so cannot detect either pattern; nothing on the pages tests dimensionality (id 16). Verdict: Contradicted (C2 falsified). Note: Epoch's own PPP for the IQR is 0.078; do not say Epoch's checks all pass.
2. 90% intervals contain 89.6% of out-of-sample scores (id 4; also 80.5% for scores at or below 0.05). Ours: held-out 0.898, LOO 0.895. Verdict: Supported (the low-score shortfall is Epoch's own figure).
3. Hyperparameters "not sensitive" (id 5). Ours: hyperprior arms and the power-scaling screen pass; one arm (P3) unresolved. Verdict: Mostly supported.
4. Pairwise probabilities (id 6, GPT-6 Astra 72% over Claude Opus 5.5). Ours: 0.71; adjacent-pair probabilities change by less than 0.10 under every resolved prior; probably overconfident given correlated residuals (E11, untested). Verdict: Supported, with a caveat.
5. Frontier robust, about one point (id 7). Ours: E6 plus the top-10 set holding under priors, anchors, single-benchmark removal and EEE sources. Verdict: Supported for tiers, not for ranks.
6. Prior matters for weak models; "The data alone cannot distinguish the two priors" (id 8). Ours: E5. Verdict: Acknowledged by Epoch, confirmed.
7. Linear scale, hedged "in theory" (id 9). Ours: E7 and T1. Verdict: Not supported, especially across capability levels.
8. Progress from "relative changes in slope" (id 10). Ours: old-model placement moves with priors, benchmark choice and source. Verdict: Weak.
9. Cherry-picking mitigated by Epoch's own runs and independent leaderboards; benchmark optimisation acknowledged with no mitigation (id 11). Ours: T5 rejects on Epoch data, near call on EEE (E9); E10. Verdict: Under-mitigated at the low end.
10. Anchors "may be revisited"; anchors "have no uncertainty" (id 12). Ours: E8. Verdict: Not tested by Epoch (id 16: no re-anchoring reported).
11. Values "may shift slightly" (id 13). Ours: E9 frontier at most 0.38 but weak models up to 4.27 SD and 13.5 points in the single-score EEE fit. Verdict: "Slightly" holds only at the frontier. (EEE mirror, section to come.)
12. Benchmark selection: criteria stated ("diverse, economically valuable, unsaturated, and widely used"), domain ECIs shown, sensitivity to the benchmark set not tested (id 14). Ours: E7, the largest driver of scale and low-end placement in our checks. Verdict: Criteria stated, sensitivity not tested.

## Residual-wording fixes (default 3)
- Page line ~267 (primer 3.4): "Each is computed from the standardised residuals z of the fit to the same dataset..." -> T1 to T5 and T7 use z; T6 compares counts of scores at 0 and 1 with the Beta tail mass.
- Page line ~349 (section 6 intro): "Every check starts from one standardised residual per score" -> same correction.
Definition for reference: z = (y - mu_bar)/sqrt(v), mu_bar the posterior-mean predicted score over 400 draws, v = mean Beta variance + variance of mu across draws (runs/lib/ppc_checks.py:65-79).
