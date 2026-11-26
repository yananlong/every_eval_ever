# Results audit: Zeng and Papailiopoulos (2606.24020v2) and Helm et al. (2611.03614)

`results-audit.json` is the authority, and this file explains it. Each audit keeps its exact heading and bounded-verdict line; the remaining fields are tabulated.

## Audit Summary

| Item | Detail |
|---|---|
| Paper ID | none (standalone audit of two published preprints) |
| Identity version | 1 |
| Audit status | complete |
| Assurance boundary | exploratory, record review only. Each headline claim is checked against the tables, captions and appendix text of the paper that makes it. Nothing was rerun, figures were not rendered, and the BenchPress repository was not cloned. A positive verdict here means the paper's own evidence is adequate for the bounded reading stated under "Scope". It says nothing about replication. |
| Sources | LaTeX e-prints under `ext/papers/`, the memory packs under `runs/LIT/helm2611/` and `runs/LIT/zeng2606/`, and the Helm Space build of 2026-11-24. Line pointers are in the packs. |

| Audit | Claim | Bounded verdict |
|---|---|---|
| AUD-ZENG-RANK-HELDOUT | held-out scores are best recovered with two factors | supports_exploratory_follow_up |
| AUD-ZENG-RANK-VARIANCE | two factors explain over 90% of variation | internally_consistent_only |
| AUD-ZENG-HELDOUT-ERROR | held-out scores recovered to within 4.6 points | supports_exploratory_follow_up |
| AUD-ZENG-PROBE | five probes recover the rest of a scorecard to 3.93 | does_not_support_claim |
| AUD-ZENG-RANKING | 92.1% of pairwise orderings preserved at a 5-point margin | supports_exploratory_follow_up |
| AUD-ZENG-TEMPORAL | five seed scores give 4.83 on new models | inconclusive |
| AUD-ZENG-RELIABILITY | reliability layer says when to trust a prediction | supports_exploratory_follow_up |
| AUD-HELM-QE | PKPS matches the sample score with up to 8x fewer queries | supports_exploratory_follow_up |
| AUD-HELM-COMPLETION | ensemble cuts completion error by up to 28% | supports_exploratory_follow_up |
| AUD-HELM-THEORY | theory establishes query efficiency and the experiments mirror it | internally_consistent_only |

## Audit AUD-ZENG-RANK-HELDOUT

| Item | Detail |
|---|---|
| Claim ID | CLM-ZENG-RANK-HELDOUT |
| Claim under audit | the 84 by 133 score matrix is approximately rank 2, in that scores hidden from the matrix are best recovered using two factors. |
| Scope | May 2026 matrix; Soft-Impute hard-rank sweep in raw and logit space; held-out MedAPE on random per-model folds and on a block holdout of the newest 17 models. |
| Source mode | standalone |
| Requested assurance class | exploratory |
| Attained assurance class | exploratory |
| Audit kind | record_review |

- Bounded verdict: supports_exploratory_follow_up

| Item | Detail |
|---|---|
| Audited claim effect | strengthen |
| Run-selection rule | no runs; every passage bearing on the claim was read. |

### Required checks

| Check | Status | Rationale |
|---|---|---|
| Protocol integrity | pass | Rank is chosen on held-out cells, and the appendix repeats the sweep with the newest fifth of models removed as a block, with 95% cluster-bootstrap intervals. |
| Metric validity | pass | Held-out MedAPE identifies the hard rank that predicts best under Soft-Impute. That is narrower than the dimension of the underlying structure. |
| Baseline fairness | inconclusive | Only Soft-Impute is swept. Under the same nested validation NMF selects rank 1 for every transform and PMF selects rank 3 or 5. The adopted Bias ALS predictor has its rank fixed at 2 and never swept. |
| Complete outcome accounting | inconclusive | The main rank figure has no uncertainty and the text gives no numbers for ranks 1 and 3. In raw space under block holdout the authors report that ranks 2 and 3 fall within each other's interval. |
| Inferential support | inconclusive | Whether rank 2 is separated from ranks 1 and 3 in logit space beyond the bootstrap interval is not stated in text. |
| Confound control | inconclusive | At 23.3% fill an optimum at low hard rank can reflect the need for regularisation as much as intrinsic dimension. |
| Provenance | pass |  |
| Snapshot continuity | not assessed |  |
| Independence | not assessed |  |

### Interpretation

| Item | Detail |
|---|---|
| What the result supports | on this matrix, with Soft-Impute, hard rank 2 gives the lowest held-out error, and the logit-space minimum survives a block holdout. |
| What it weakens | the abstract's statement that a model's scores "are largely determined by just two numbers". BenchPress itself uses a per-model offset and two factor scores, three numbers per model, and its fitted matrix can have rank 4 in transformed space. |
| Strongest evidence against the preferred interpretation | the selected rank depends on the estimator (1 for NMF, 3 or 5 for PMF), so "2" belongs partly to Soft-Impute at this sparsity. |
| Minimum corrective action | add_evidence. Sweep rank 0 to 4 for Bias ALS with intervals and report the rank-1 and rank-3 errors. |
| Later exploratory evidence | A separate in-house rerun (`runs/BENCHPRESS/rank_repro_contrasts.csv`, one hide-half split, version families not collapsed) sweeps the Bias ALS rank on the May matrix. Rank 2 improves on rank 1 by 0.53 MedAE points [0.27, 0.70] and rank 3 adds 0.05 with an interval of [-0.27, 0.13]. Its absolute errors exceed the paper's, so it bears on the ordering of ranks only and does not change the verdict. |

## Audit AUD-ZENG-RANK-VARIANCE

| Item | Detail |
|---|---|
| Claim ID | CLM-ZENG-RANK-VARIANCE |
| Claim under audit | two factors already explain over 90% of the variation among models on the benchmarks they share. |
| Scope | SVD of four column-centred, fully observed submatrices (4 by 42, 7 by 11, 10 by 7, 13 by 6 as benchmarks by models). |
| Source mode | standalone |
| Requested assurance class | exploratory |
| Attained assurance class | exploratory |
| Audit kind | record_review |

- Bounded verdict: internally_consistent_only

| Item | Detail |
|---|---|
| Audited claim effect | unchanged |

### Required checks

| Check | Status | Rationale |
|---|---|---|
| Protocol integrity | inconclusive | The blocks are the largest fully observed ones, which are the most popular benchmarks and models. The scale of the SVD (raw or logit) is not given. |
| Metric validity | fail | A centred 4 by 42 block has at most 4 components and a centred 13 by 6 block at most 5, so a two-component share above 90% carries little information. The first component alone explains 78.2% to 90.4% and the stable rank is 1.11 to 1.28. |
| Baseline fairness | not assessed | No noise reference of the same shape. |
| Complete outcome accounting | pass | All four blocks are tabulated. |
| Inferential support | inconclusive | No intervals; two blocks have 7 and 6 models. |
| Confound control | fail | Popularity-selected dense blocks are not a sample of the 133 benchmarks. |
| Provenance | pass |  |
| Snapshot continuity | not assessed |  |
| Independence | not assessed |  |

### Interpretation

| Item | Detail |
|---|---|
| What the result supports | the sentence is true of the four blocks (91.2% to 97.6%). |
| What it weakens | its use as a second, independent line of evidence for rank 2. The same table fits one dominant factor at least as well. |
| Strongest evidence against | stable rank near 1 in every block. |
| Minimum corrective action | sharpen_comparator. Compare the spectrum with a noise reference of the same shape, on the logit scale, and report the second component's increment with an interval. |

## Audit AUD-ZENG-HELDOUT-ERROR

| Item | Detail |
|---|---|
| Claim ID | CLM-ZENG-HELDOUT-ERROR |
| Claim under audit | BenchPress recovers held-out scores to within 4.6 points. |
| Scope | random per-model holdout of observed cells, 10 seeds by 3 folds, median absolute error in score points at full coverage, default configuration. |
| Source mode | standalone |
| Requested assurance class | exploratory |
| Attained assurance class | exploratory |
| Audit kind | record_review |

- Bounded verdict: supports_exploratory_follow_up

| Item | Detail |
|---|---|
| Audited claim effect | strengthen |

### Measurements

- Held-out MedAE 4.63 and MedAPE 7.77% for the default predictor (Table 4 and the full grid).
- Same protocol, benchmark mean 10.04, model mean 7.22, logit Soft-Impute 5.10, identity Bias ALS 5.17.
- Conformal interval width for the same predictor, 19.56 points at 80%, 27.01 at 90%, 35.43 at 95%.

### Required checks

| Check | Status | Rationale |
|---|---|---|
| Protocol integrity | pass | Nested validation; the validation ranking also puts the default first. |
| Metric validity | pass, with a wording caveat | The figure is a median, so half of held-out cells miss by more. |
| Baseline fairness | pass | All 84 transform and method pairs are tuned the same way on the same folds. |
| Complete outcome accounting | inconclusive | The hide fraction is stated three inconsistent ways (half, three folds, about 20,000 test predictions over 30 folds). |
| Inferential support | inconclusive | No interval on 4.63; the leading full-coverage configurations differ by 0.01 points. |
| Confound control | fail | Held-out cells are a random subset of cells that someone chose to run and report. The 76.7% of cells never observed are not represented, and the authors themselves describe the missingness as structured. |
| Provenance | pass |  |
| Snapshot continuity | not assessed |  |
| Independence | not assessed |  |

### Interpretation

| Item | Detail |
|---|---|
| What the result supports | a median absolute error of 4.63 points on random held-out observed cells, a little under half the benchmark-mean error. |
| What it weakens | reading "within 4.6 points" as a bound. The paper's own 90% interval is about plus or minus 13.5 points. |
| Strongest evidence against | error on unobserved cells is not estimated, and per-model error varies about 40-fold by the authors' account. |
| Minimum corrective action | add_evidence. Report mean and upper-quantile errors, and score the May predictions on cells that first appear in the August matrix. |

## Audit AUD-ZENG-PROBE

| Item | Detail |
|---|---|
| Claim ID | CLM-ZENG-PROBE |
| Claim under audit | five benchmarks (GPQA-D, HLE, Codeforces, MMLU-Pro, ARC-AGI-1) can recover the rest of a model's public scorecard to within 3.93 points, and a cheaper set reaches 4.55. |
| Scope | greedy forward selection minimising pooled MedAE over all observed cells of all 84 models, with probe cells scored as zero error. |
| Source mode | standalone |
| Requested assurance class | exploratory |
| Attained assurance class | exploratory |
| Audit kind | record_review |

- Bounded verdict: does_not_support_claim

| Item | Detail |
|---|---|
| Audited claim effect | weaken |

### Required checks

| Check | Status | Rationale |
|---|---|---|
| Protocol integrity | fail | The probe set is chosen by minimising the same pooled error on the same cells that are reported. The body says the curves "should not be read as held-out transfer estimates for a fixed universal probe set". |
| Metric validity | fail | Observed probe cells count as exact predictions and stay in the denominator, so the pooled median is not an error on "the rest" of the scorecard. |
| Baseline fairness | pass | Random orderings and exhaustive search over the low-cost list are both reported. |
| Complete outcome accounting | pass |  |
| Inferential support | fail | No out-of-sample estimate for the chosen sets. |
| Confound control | inconclusive | Models are evaluated on whichever probes they happen to have. |
| Provenance | pass |  |
| Snapshot continuity | not assessed |  |
| Independence | not assessed |  |

### Interpretation

| Item | Detail |
|---|---|
| What the result supports | on this snapshot, a greedy five-benchmark set gives an in-sample pooled MedAE of 3.926, well below random orderings, and the choice of probes matters more than their number. |
| What it weakens | the abstract's sentence, which drops the in-sample caveat that the body states. |
| Strongest evidence against | the authors' own remark quoted above. |
| Minimum corrective action | add_evidence. Select probes on some models and score on others with probe cells excluded, or score the May probe sets on models added in August. |

## Audit AUD-ZENG-RANKING

| Item | Detail |
|---|---|
| Claim ID | CLM-ZENG-RANKING |
| Claim under audit | for same-benchmark pairs at least five points apart, predicted scores give the correct ordering 92.1% of the time. |
| Scope | per-model holdout; leaderboards completed with true scores on seen cells; pairs with at least one held-out cell; median across benchmarks. |
| Source mode | standalone |
| Requested assurance class | exploratory |
| Attained assurance class | exploratory |
| Audit kind | record_review |

- Bounded verdict: supports_exploratory_follow_up

| Item | Detail |
|---|---|
| Audited claim effect | strengthen |

### Required checks

| Check | Status | Rationale |
|---|---|---|
| Protocol integrity | pass |  |
| Metric validity | pass | A pair needs only one held-out cell, so many pairs compare a prediction with a true score. |
| Baseline fairness | fail | No baseline is given; a model-mean completion would also order well-separated models correctly. |
| Complete outcome accounting | pass | Margins 0, 1, 2 and 5 are reported (83.8%, 86.3%, 88.0%, 92.1%). |
| Inferential support | inconclusive | No interval; pairs are dependent. |
| Confound control | inconclusive | A five-point margin selects easy pairs. |
| Provenance | pass |  |
| Snapshot continuity | not assessed |  |
| Independence | not assessed |  |

### Interpretation

| Item | Detail |
|---|---|
| What the result supports | the reported accuracy under the stated protocol. |
| What it weakens | nothing directly, but the increment over a trivial completion is unknown, and top-10% shortlist recovery is 72.4%. |
| Minimum corrective action | sharpen_comparator. Report the same accuracy for model-mean completion and for pairs with both cells held out. |

## Audit AUD-ZENG-TEMPORAL

| Item | Detail |
|---|---|
| Claim ID | CLM-ZENG-TEMPORAL |
| Claim under audit | across 27 targets in a pre-specified window, five seed scores bring predictions within 4.83 points and ten seeds within 2.57. |
| Scope | training on models released before the target; k randomly revealed scores; revealed cells scored as zero error. |
| Source mode | standalone |
| Requested assurance class | exploratory |
| Attained assurance class | exploratory |
| Audit kind | record_review |

- Bounded verdict: inconclusive

| Item | Detail |
|---|---|
| Audited claim effect | inconclusive |

### Required checks

| Check | Status | Rationale |
|---|---|---|
| Protocol integrity | pass | The temporal split is real. |
| Metric validity | fail | Revealed cells contribute zero error. Targets have 21 to 79 observed scores, so at ten seeds 13% to 48% of a target's cells are zero by construction. |
| Baseline fairness | not assessed |  |
| Complete outcome accounting | pass | All 27 targets are tabulated. |
| Inferential support | inconclusive |  |
| Confound control | fail | The decline with k mixes information gain with the growing share of zero-error cells. The target with the fewest scores (Grok 3 Beta, 21) falls from 5.7 to 0.5. |
| Provenance | pass |  |
| Snapshot continuity | not assessed |  |
| Independence | not assessed |  |

### Interpretation

| Item | Detail |
|---|---|
| What the result supports | that more seed scores help, in direction. |
| What it leaves open | the size of the effect. The one-seed figure, 9.20, is the least affected. |
| Minimum corrective action | add_evidence. Recompute on hidden cells only with a model-mean baseline at each k. |

## Audit AUD-ZENG-RELIABILITY

| Item | Detail |
|---|---|
| Claim ID | CLM-ZENG-RELIABILITY |
| Claim under audit | reliability factors combined with predictor disagreement quantify when predictions can be trusted, with a trust probability and a conformally calibrated 90% interval. |
| Scope | hybrid risk model trained fold-out on held-out absolute errors; risk-coverage curve; leave-fold-out conformal scaling. |
| Source mode | standalone |
| Requested assurance class | exploratory |
| Attained assurance class | exploratory |
| Audit kind | record_review |

- Bounded verdict: supports_exploratory_follow_up

| Item | Detail |
|---|---|
| Audited claim effect | strengthen |

### Required checks

| Check | Status | Rationale |
|---|---|---|
| Protocol integrity | pass | Risk models never see the fold they score. |
| Metric validity | pass |  |
| Baseline fairness | pass | Three estimators under one procedure. |
| Complete outcome accounting | inconclusive | Empirical coverage of the 90% interval is not reported; only an 80% interval in a 23-benchmark variant has coverage (0.798 to 0.800). |
| Inferential support | inconclusive |  |
| Confound control | inconclusive | Cells sharing a model or benchmark are not exchangeable. |
| Provenance | pass |  |
| Snapshot continuity | not assessed |  |
| Independence | not assessed |  |

### Interpretation

| Item | Detail |
|---|---|
| What the result supports | the risk score ranks predictions usefully (selective MedAE 1.83, 2.51 and 3.10 at the most trusted 20%, 40% and 60%). |
| What it weakens | any reading of the point predictions as precise. The 90% interval is 27 points wide. |
| Minimum corrective action | add_evidence. Report 90% coverage overall and by model and benchmark. |

## Audit AUD-HELM-QE

| Item | Detail |
|---|---|
| Claim ID | CLM-HELM-QE |
| Claim under audit | PKPS matches the accuracy of the sample score with up to an 8 times smaller query budget. |
| Scope | HELM-Lite suite (18 tasks, 93 models) and EEE suite (16 tasks, 45 models); dense matrices with uniform masking; unpaired query pools; leave-one-family-out; MAE on a 0 to 1 scale over 16 seeds. |
| Source mode | standalone |
| Requested assurance class | exploratory |
| Attained assurance class | exploratory |
| Audit kind | record_review |

- Bounded verdict: supports_exploratory_follow_up

| Item | Detail |
|---|---|
| Audited claim effect | strengthen |

### Required checks

| Check | Status | Rationale |
|---|---|---|
| Protocol integrity | pass | Targets are full-depth means that are never embedded, and the regressor excludes the target developer's models. |
| Metric validity | pass |  |
| Baseline fairness | inconclusive | IRT and DKPS are handicapped by the unpaired design the experiment constructs. The sample score is the informative comparator. |
| Complete outcome accounting | pass | Table 1 includes the cells where PKPS alone loses (HELM at eight queries: sample 0.092, PKPS 0.109). |
| Inferential support | pass | Wilcoxon over per-task differences, p of 8e-6 on HELM at one query, better on all 18 tasks. Uncorrected; tasks within a dataset are dependent. |
| Confound control | inconclusive | Uniform masking of models that ran everything; a transductive embedding; one embedding model. |
| Provenance | pass |  |
| Snapshot continuity | not assessed |  |
| Independence | not assessed |  |

### Interpretation

| Item | Detail |
|---|---|
| What the result supports | at one to a few queries per cell, PKPS beats the cell's own sample mean by a wide margin on both suites. |
| What it weakens | the generality of "8 times". That is the EEE maximum (0.070 at one query against 0.081 at eight); on HELM the factor is 4, and the sample score overtakes PKPS as the budget grows. |
| Minimum corrective action | add_evidence. Repeat under a selection-driven observation pattern and with a second embedder. |

## Audit AUD-HELM-COMPLETION

| Item | Detail |
|---|---|
| Claim ID | CLM-HELM-COMPLETION |
| Claim under audit | ensembled with low-rank matrix completion, PKPS reduces completion error by up to 28%, and PKPS-based methods outperform baselines across two large suites. |
| Scope | completion of cells with no responses at coverage and depth 0.5 (coverage 0.2 for the sparse column), cohorts of 10 and full; LRMC is the BenchPress recipe at rank 2 and ridge 0.1. |
| Source mode | standalone |
| Requested assurance class | exploratory |
| Attained assurance class | exploratory |
| Audit kind | record_review |

- Bounded verdict: supports_exploratory_follow_up

| Item | Detail |
|---|---|
| Audited claim effect | strengthen |

### Measurements

- EEE full cohort, LRMC 0.096, ensemble 0.069 (28% lower).
- HELM full cohort, LRMC 0.105, ensemble 0.100 (about 5% lower, 9 of 18 tasks, not significant).
- HELM cohort of 10, LRMC 0.139, ensemble 0.120 (about 14% lower, p of 1e-3).
- Space, live EEE data, 5-fold over model and collection pairs, LRMC 0.0587, PKPS 0.0584, ensemble 0.0577 (n of 1,374).

### Required checks

| Check | Status | Rationale |
|---|---|---|
| Protocol integrity | pass | PKPS and LRMC share one preprocessing pipeline, so the comparison isolates how the residual is modelled. |
| Metric validity | pass |  |
| Baseline fairness | inconclusive | LRMC's rank and ridge are inherited from an 84 by 133 matrix and not re-selected for 16 or 18 tasks and cohorts as small as 10. No additive-only baseline is tabulated on the real suites. |
| Complete outcome accounting | pass | The non-significant HELM result is disclosed. |
| Inferential support | pass |  |
| Confound control | inconclusive | Cells are missing completely at random by construction. |
| Provenance | pass |  |
| Snapshot continuity | not assessed |  |
| Independence | not assessed |  |

### Interpretation

| Item | Detail |
|---|---|
| What the result supports | the ensemble is at least as good as rank-2 LRMC everywhere tested, with the margin largest where LRMC is least identified. |
| What it weakens | "28%" as a typical figure, and "PKPS outperforms" as distinct from "the ensemble outperforms". |
| Strongest evidence against | the authors' own Space reports a margin of 0.001 on the live store under a different protocol and embedder. |
| Minimum corrective action | sharpen_comparator. Re-select LRMC rank and ridge per setting, add a two-way additive baseline, and test under the store's real observation pattern. |

## Audit AUD-HELM-THEORY

| Item | Detail |
|---|---|
| Claim ID | CLM-HELM-THEORY |
| Claim under audit | prediction with PKPS is query-efficient relative to methods that use only paired data (Theorem 2), and the experiments are its empirical counterpart. |
| Scope | Theorems 1 and 2 with their proofs, read against the estimator run in the experiments. |
| Source mode | standalone |
| Requested assurance class | exploratory |
| Attained assurance class | exploratory |
| Audit kind | record_review |

- Bounded verdict: internally_consistent_only

| Item | Detail |
|---|---|
| Audited claim effect | unchanged |

### Required checks

| Check | Status | Rationale |
|---|---|---|
| Protocol integrity | inconclusive | The proofs were read without finding an error but were not formally checked. The estimator in Theorem 2 (three-way split, Nystrom extension, guarded bandwidth choice, exact reference scores) differs from the experimental one (joint embedding, leave-one-model-out bandwidth choice, no guard, sample scores as targets). |
| Metric validity | pass |  |
| Baseline fairness | inconclusive | Part (i) holds for any family that contains the comparator and selects with a guard. Part (ii) compares against DKPS where it has no shared queries and can only predict the mean. |
| Complete outcome accounting | pass | Assumptions are explicit. |
| Inferential support | inconclusive | The Theorem 1 bound grows linearly in the number of models and is not evaluated on either suite. |
| Confound control | inconclusive | Uniform observation and i.i.d. models are assumed. |
| Provenance | pass |  |
| Snapshot continuity | not assessed |  |
| Independence | not assessed |  |

### Interpretation

| Item | Detail |
|---|---|
| What the result supports | the guarantee for the guarded estimator under uniform, i.i.d. sampling. |
| What it leaves open | why the real-data gains occur. They come from a different estimator and from an embedding whose informativeness is assumed. |
| Minimum corrective action | lower_assurance. Present the theory as motivation, or run the guarded estimator once to show the gap is small. |

## Claim trajectory

No predecessor audits exist and no claim was narrowed by this audit. Where a verdict is positive, the "Scope" line gives the reading that the evidence supports, and the "What it weakens" line gives the part of the published wording that goes beyond it. Project-level review is not required.
