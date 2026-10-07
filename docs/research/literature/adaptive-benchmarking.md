# Adaptive benchmarking and evaluation acquisition

Reviewed on 2026-10-07. These two sources expand the critical evidence map with adaptive item administration and learned acquisition of outcomes. The included artifacts are the complete final ICML proceedings paper for AB02 and a complete conference-labelled author manuscript for accepted COLM paper AB01, whose final OpenReview PDF remained inaccessible. Each source has source-level methods, numerical results and actual figure inspection recorded below. The evidence concerns the papers' evaluated item pools and model populations, with EEE consequences stated as design inferences. No EEE estimate, acquisition policy or uncertainty field has been validated by this review.

## AB01 — Fluid Language Model Benchmarking

### Status, source, and coverage

**Verified accepted research paper, COLM 2025 Spotlight.** Title: *Fluid Language Model Benchmarking*. Authors, in order: Valentin Hofmann, David Heineman, Ian Magnusson, Kyle Lo, Jesse Dodge, Maarten Sap, Pang Wei Koh, Chun Wang, Hannaneh Hajishirzi, Noah A. Smith. The official COLM accepted-paper list names the paper/authors and marks it Spotlight: https://colmweb.org/2025/AcceptedPapers.html (entry links to https://openreview.net/forum?id=mxcCg9YRqj). The indexed OpenReview record states Published 7 July 2025; Last Modified 25 August 2025. The independent primary arXiv record lists one version, v1 submitted 14 September 2025 05:49:42 UTC, and comments COLM 2025: https://arxiv.org/abs/2509.11106.

**Actual artifact read:** author-deposited arXiv v1 PDF https://arxiv.org/pdf/2509.11106, 18 pages, all headed “Published as a conference paper at COLM 2025”; main §§1–8, acknowledgments/references, and appendices A–H were read in full. All eight figures were actually viewed in fitz-rendered PNGs on pages 2, 5, 9, 15, 18; all four numerical tables were also viewed on pages 7, 8, 16, 17. Page locators below refer to printed/PDF page numbers, which agree.

**Access gap:** direct OpenReview PDF https://openreview.net/pdf?id=mxcCg9YRqj and api2 record both returned challenge-required HTML/403 on 7 October 2026. Thus acceptance/status is verified from the official conference list and indexed OpenReview metadata, but the review did not obtain/byte-compare the final OpenReview PDF. The read artifact is a complete author-deposited conference-labelled manuscript, not merely an abstract. Avoid silently asserting exact identity with the final OpenReview artifact.

Primary supplementary resources: https://github.com/allenai/fluid-benchmarking and https://huggingface.co/datasets/allenai/fluid-benchmarking. The former's current main `scripts/run_experiments.py` and `fluid_benchmarking/evaluation.py` were read to clarify random sampling; they are unpinned supplementary code, not proof of the historical execution environment.

### Measurement target and method

The paper's object is **benchmark refinement**: select questions within a benchmark and aggregate their binary outcomes (§2, p. 3). It changes both the administered item portfolio and the score's meaning. This is adaptive measurement of a model on a benchmark; it is not an experiment predicting absent benchmark-level scores in a sparse heterogeneous aggregate archive.

For each benchmark, a two-parameter logistic IRT model gives `P(correct on item j | model i) = logistic(a_j (theta_i − b_j))`, with positive discrimination `a_j`, difficulty `b_j`, and one latent model ability `theta_i` (§3.1, p. 4, Eq 2). It assumes local independence and fits the full binary response matrix using MCMC with hierarchical priors. For a new model, item parameters are fixed; MAP estimates ability from administered responses (§3.1, Eq 3; the displayed likelihood is supplemented by the prose's MAP choice). Ability is the reported score, rather than accuracy or an imputed full-benchmark percentage.

At each evaluation step, Fluid chooses the unused item with maximal Fisher information `a_j² p_j(theta)[1 − p_j(theta)]`, then updates the ability estimate using responses so far (§3.2, p. 5, Eqs 4–5). Main experiments stop at a fixed item budget. Maximum information occurs at difficulty equal to current ability, with value `a_j²/4`; this favors highly discriminating, capability-matched items. Because observed answers affect later selections, two models can receive different question sets and a model's successive checkpoints can receive different sets. Shared calibrated item parameters supply the common latent scale.

A separate illustrative dynamic-stopping experiment stops when estimated ability's standard error falls below the **mean ability gap between rank-adjacent Open LLM Leaderboard models** (§6, p. 9, Fig5). That threshold is a particular reference-population criterion, not a universally calibrated confidence rule or a demonstrated coverage guarantee.

### Training/test separation and experimental support

- Six old Open LLM Leaderboard benchmarks: ARC Challenge, GSM8K, HellaSwag, MMLU, TruthfulQA, WinoGrande (§4.1, p. 6).
- Separate unidimensional IRT calibration per benchmark using **102 pretrained LMs** (§4.1; Appendix D, p. 16). Exclude all six test models and their families (e.g., OLMo1-1B), posttrained/finetuned, merged, fused, distilled, and continually pretrained models. Retain only final listed checkpoint when a calibration model has multiple entries; exclude solely non-English pretrained models, allow multilingual models containing English. This addresses family similarity in calibration and is stronger than an arbitrary cell-level split.
- Heldout test trajectories: Amber-6.7B **73** checkpoints; K2-65B **61**; OLMo1-7B **83**; OLMo2-7B **94**; Pythia-2.8B **78**; Pythia-6.9B **78** (Appendix C, p. 15). Total **467** checkpoints, evenly covering each training run. At six benchmarks, **2,802 checkpoint–benchmark combinations**, more than **13 million** item evaluations (§4.1, p. 6).
- This holds out model families from IRT calibration; it does **not** hold out benchmark definitions/items, impose a chronological archive split, or evaluate new benchmark-family transfer. Those benchmarks are known and calibrated in advance. Test checkpoints within each trajectory are dependent, not 2,802 independently sampled deployments.
- Budgets range **10–500 items** (§4.2). Random IRT uses random items but IRT ability; Random uses random items and accuracy (§4.3). Other baselines: Anchor Points (10/50), tinyBenchmarks (100), metabench (benchmark-specific sizes averaging 143), SMART hard subsets (460), MAGI hard subset (1,848). Fluid matches comparator item counts for Table 1, including exact per-benchmark metabench counts.
- The unpinned current author script draws one random subset for each benchmark/budget before looping over models/checkpoints (seed default **0**), reuses it across those loops, and initializes Fluid at calibration models' mean ability. Thus in that script the Random baseline is a static sampled portfolio; it is not fresh independent resampling at every checkpoint. The paper does not report repeated seeds, bootstrap intervals, or hypothesis tests for table means.

### What the quality metrics measure

**Validity** (§4.2, p. 6): rank distance between assessed performance on one benchmark and accuracy-based rank on another benchmark intended to target the same capability. Pairs are ARC Challenge/MMLU (knowledge/reasoning) and HellaSwag/WinoGrande (commonsense). GSM8K and TruthfulQA have no validity values (Table 3 displays dashes). This is cross-benchmark rank agreement, not benchmark-cell prediction RMSE, item correctness calibration, direct real-world task validity, or an expert-established latent construct. Table 1's caption describes averaging 2,802 values across six benchmarks; because validity is defined on four benchmarks, do not imply that all six contribute measured validity values.

**Variance**: normalized total variation along a pretraining curve, Eq 6 `n/(n−1) × sum_{t=1}^{n−1}|x_{t+1}−x_t| / |x_n−x_1|`. This is endpoint-normalized training-curve roughness. It is not an empirical variance from repeated independent evaluation draws. It can reflect real nonmonotonic learning as well as measurement fluctuation; endpoint normalization also affects interpretation, with zero or small endpoint changes requiring special handling. The absolute endpoint difference in the denominator was independently checked on the rendered page 6 equation, because plain text extraction can omit its absolute-value bars.

**Saturation**: absolute Spearman correlation of checkpoint order with measured performance. Stronger monotonicity is used as a proxy for delayed saturation. The absolute value can credit consistently decreasing trajectories (relevant to TruthfulQA); it does not universally prove improved capability or resistance to contamination. Figure 4 supplies a specific late-training illustration, rather than making monotonicity alone a definitive saturation test.

**Efficiency**: number of administered items at a quality level. Includes neither calibration collection/fitting cost nor a complete wall-clock/financial cost comparison. Abstract/introduction report MMLU higher validity and lower variance with **50 times fewer items**; retain it as the authors' scoped claim, not a universal speedup or an EEE result.

### All reported numerical tables

These are source-reported values, not reproduced experiments. In Tables 1–4 validity/total variation are lower-is-better, saturation higher-is-better. A cell below is `validity / variation / saturation`.

#### Table 1, p. 7 — matched-budget published-method comparison

| Comparator/budget | Comparator | Fluid, same budget |
|---|---:|---:|
| Anchor Points / 10 | 20.0 / 28.3 / 0.48 | 10.1 / 10.7 / 0.76 |
| Anchor Points / 50 | 15.2 / 19.1 / 0.62 | 8.8 / 6.5 / 0.86 |
| tinyBenchmarks / 100 | 9.8 / 30.5 / 0.69 | 8.7 / 6.1 / 0.85 |
| metabench / mean 143 | 8.7 / 17.9 / 0.79 | 8.6 / 5.5 / 0.85 |
| SMART / 460 | 15.9 / 10.0 / 0.88 | 14.0 / 2.8 / 0.97 |
| MAGI / 1848 | 14.5 / 20.4 / 0.64 | 8.3 / 4.8 / 0.77 |

SMART/MAGI concern their hard benchmark subsets; do not describe every column as an independently identical six-benchmark comparison without respecting §4.3's scope.

#### Table 2, p. 8 — ablations

| Items | Random | Random IRT | Fluid |
|---|---:|---:|---:|
| 10 | 20.0 / 29.0 / 0.47 | 14.1 / 18.2 / 0.48 | 10.1 / 10.7 / 0.76 |
| 50 | 15.2 / 19.1 / 0.62 | 11.1 / 15.7 / 0.69 | 8.8 / 6.5 / 0.86 |
| 100 | 16.9 / 19.8 / 0.64 | 10.6 / 17.8 / 0.71 | 8.7 / 6.1 / 0.85 |
| 500 | 9.1 / 10.2 / 0.79 | 8.4 / 10.9 / 0.85 | 8.3 / 4.9 / 0.88 |

Ablation implication: representing outcomes in IRT ability improves rank agreement more than it improves training-curve roughness; adaptive item selection accounts for much of the roughness reduction. With 500 items Random IRT roughness **10.9** exceeds Random **10.2**. At 100 items tinyBenchmarks roughness **30.5** exceeds Random **19.8** (§5, pp7–8). Do not attribute all benefit merely to using IRT.

#### Table 3, p. 16 / Appendix F — 100-item benchmark breakdown

| Benchmark | Random | Random IRT | Fluid |
|---|---:|---:|---:|
| ARC Challenge | 21.9 / 10.2 / 0.75 | 15.9 / 7.9 / 0.82 | 14.5 / 3.3 / 0.95 |
| GSM8K | — / 22.2 / 0.66 | — / 28.9 / 0.60 | — / 9.1 / 0.86 |
| HellaSwag | 12.9 / 3.8 / 0.88 | 5.0 / 12.0 / 0.88 | 4.5 / 2.0 / 0.98 |
| MMLU | 20.5 / 49.7 / 0.51 | 13.4 / 20.8 / 0.56 | 10.7 / 6.3 / 0.67 |
| TruthfulQA | — / 18.1 / 0.43 | — / 15.1 / 0.63 | — / 9.8 / 0.71 |
| WinoGrande | 12.4 / 14.6 / 0.61 | 8.2 / 22.1 / 0.76 | 4.9 / 5.8 / 0.93 |

#### Table 4, p. 17 / Appendix F — 100-item model breakdown

| Test model | Random | Random IRT | Fluid |
|---|---:|---:|---:|
| Amber-6.7B | 25.5 / 21.8 / 0.47 | 20.2 / 16.2 / 0.66 | 19.3 / 5.5 / 0.82 |
| K2-65B | 5.1 / 14.7 / 0.65 | 5.2 / 27.0 / 0.73 | 2.1 / 7.1 / 0.89 |
| OLMo1-7B | 10.7 / 10.2 / 0.77 | 8.0 / 11.4 / 0.83 | 6.7 / 5.8 / 0.91 |
| OLMo2-7B | 7.1 / 15.4 / 0.63 | 6.1 / 12.4 / 0.63 | 3.4 / 6.8 / 0.80 |
| Pythia-2.8B | 23.1 / 35.7 / 0.62 | 8.3 / 26.1 / 0.67 | 8.1 / 6.5 / 0.81 |
| Pythia-6.9B | 28.1 / 20.9 / 0.71 | 15.3 / 13.7 / 0.73 | 11.6 / 4.5 / 0.87 |

Table 4's caption abbreviates Amber as Amber-7B; experimental text specifies Amber-6.7B.

#### Other exact outcomes / illustrative numbers

- Appendix H, p. 17: full-benchmark accuracy vs Fluid 500: validity **9.1 vs 8.3**, variation **23.8 vs 4.9**, saturation **0.85 vs 0.88**. Fluid 50 (**8.8 /6.5 /0.86**) also beats those full-accuracy means. This compares measurement quality on the paper's metrics, not reconstruction accuracy against the full score.
- §6, p. 8: MMLU-Redux-labeled-error item exposure at budget 100, mean mislabeled count **0.01 Fluid vs 0.75 Random** across test models/checkpoints. The source interprets roughly one occurrence per100 Fluid sessions vs almost every Random session. Counts are not directly a calibrated probability of “any error”; avoid converting count0.75 into a75% session probability. Derived relative mean-count reduction is ~98.7%, but quoting original counts is safest.
- §6, p. 9: OLMo2-7B/HellaSwag at500 items, entire-trajectory monotonicity **0.91 Random vs 0.99 Fluid**; Figure 4 displays only final **30%** of training.
- §6, p. 9: dynamic-stop example on OLMo1-7B/HellaSwag varies from **around 20** items early to **over 80** midway; these are approximate readings reported by authors, not exact table outcomes.
- §3.2, Fig2, p. 5: illustrative simulated ability moves linearly **−7 to +7 over 50 checkpoints**. It is simulation, not an observed training trajectory.
- Appendix A, Fig6, p. 15: illustration curves use `(a,b)=(10,0), (0.1,0), (10,1)`; these are illustrative settings, not learned result estimates.
- Appendix E, p. 16: attempts at per-benchmark multidimensional IRT use **2–5 latent traits**, with no consistent fit improvement reported; no numerical fit comparison is supplied.

### Actual figure reading

- **Figure 1 (p. 2):** schematic calibration response matrix leads to differently selected item subsets for two LMs, then latent scores. Panel c's Pythia-2.8B/ARC30 plot shows much smoother Fluid ability than Random accuracy; axes represent different scores, so raw ordinate ranges are not a variance effect size. Panel d rank-distance curves decline with budget and Fluid stays lower, with the largest separation at small budgets.
- **Figure 2 (p. 5):** simulated linear ability underlies a diagonal bright Fisher-information band through item difficulty; strongest items change with ability. Upper information colorbar and lower ability plot distinguish mathematical simulation from measured checkpoints.
- **Figure 3 (p. 9):** observed OLMo1/HellaSwag50 selected items shift from negative difficulty early toward positive difficulty later; a pale constant line near 0 is the common first item. Colors encode within-session order of selection, not correctness or uncertainty. Figure supports changing question portfolios over a known benchmark's checkpoints; it does not show adding new benchmarks to an archive.
- **Figure 4 (p. 9):** Random HellaSwag accuracy oscillates near 0.81–0.82 over 70–100% OLMo2 training; Fluid ability trends approximately2.5–2.7 with some fluctuations. Supports the named example's continuing sensitivity, with distinct vertical scales.
- **Figure 5 (p. 9):** dynamic-stop item count rises from about 20 through a broad peak above 80 near mid-training, then declines toward around 60. A uniform item budget is not equally informative across checkpoints under this threshold.
- **Figure 6 (p. 15):** steep curves centered0/1 versus shallow curve centered0 illustrate discrimination and difficulty independently.
- **Figure 7 (p. 15):** HellaSwag item information at simulated ability0 concentrates around difficulty0; high-discrimination colors appear among high-information points, with a peak around 8. Far-away difficulty gives near-zero information even for high discrimination. No empirical uncertainty intervals shown.
- **Figure 8 (p. 18):** pairwise scatter over benchmark colors, model marker shapes, budget sizes100–500. Variance has most points below equal-performance diagonal; inset shows a cluster of high-roughness cases. Saturation mostly above diagonal but there are exceptions. Appendix G/caption explicitly says **almost all** combinations, narrower than the main prose's universal phrasing. No error bars, repeated-sampling distributions, or confidence bands shown.

### Missingness, uncertainty, and boundaries

Calibration requires per-item binary response patterns from a shared benchmark. Adaptive non-administration is induced by the policy with an explicit known item pool and calibrated parameters. The paper does not evaluate observational archive missingness, MNAR publication/test-selection, disconnected benchmark portfolios, heterogeneous metrics, incompatible harness versions, or selective aggregate reporting. The model-implied ability and Fisher-information quantities are conditional on fixed calibrated item parameters; table results do not propagate uncertainty in those parameters or establish frequentist coverage/calibration. The reference model set and local-independence/unidimensional assumptions matter.

Appendix E is especially relevant to aggregation choices: a **single latent scale over all six benchmarks obscured Amber's declining TruthfulQA accuracy by making estimated ability increase**, because items aligned with general trends were emphasized. Separate benchmark scales avoided this particular problem. This is source-grounded evidence against assuming a universal cross-benchmark factor has construct validity merely because it compresses scores.

The authors explicitly discuss calibration drift/generalization (§6, p. 10): if no calibration model answers certain items correctly, those items receive effectively indistinguishable maximum difficulty. A stronger future LM may reach them quickly, but fixed calibration cannot resolve their finer difficulty. They call for regular IRT updates with fresh evidence. Their heldout pretraining tests do not demonstrate stable measurement for arbitrarily stronger, posttrained, multilingual, or multimodal models; those are proposed extensions.

### Bounded EEE implication

**Supported citation role:** a method-level motivation for distinguishing measurement quality from agreement with a fixed aggregate and for treating evaluation item portfolios as adaptive. Fluid provides evidence that item-level calibration plus answer-dependent selection can improve cross-benchmark rank agreement and smooth known-benchmark pretraining curves with fewer evaluated questions. The changing subset and ability-score definition must accompany a reported measurement for interpretable comparisons.

**EEE-specific inference, not the paper's result:** an EEE aggregate archive could document source benchmark/metric/protocol, measurement budget, adaptive-selection policy and calibration version when available. It cannot recover response-pattern IRT calibration or execute this item-level policy from aggregate means alone. EEE's separate instance-level records might enable a future experiment on compatible item pools; presence of those records alone does not establish compatible calibration, sufficient overlap, policy provenance, or uncertainty.

**Do not claim:** Fluid validates EEE's sparsity, proves EEE matrix-completion performance, measures EEE sample efficiency, addresses EEE MNAR missingness, establishes a universal leaderboard score, guarantees stable rankings across changing benchmark definitions, or supplies EEE results. A bounded discussion can cite its empirical item-level findings and its explicit fixed-calibration caveat, while keeping archive representation/aggregate prediction a different task. No EEE data were analyzed in this review.

The transferable principle is to distinguish adaptive measurement quality from reconstruction of a fixed aggregate. Fluid combines item-response calibration with capability-dependent question selection, evaluating a model in a common latent ability space even when administered item subsets differ. Its held-out pretraining study supports improved rank agreement and training-curve stability under the tested conditions, while requiring item-level response patterns and calibrated benchmark-specific parameters (§§3–6 and Appendices D–E). An aggregate score archive alone does not supply those inputs.

## AB02 — Active Evaluation Acquisition for Efficient LLM Benchmarking

**Publication and exact version.** Yang Li, Jie Ma, Miguel Ballesteros, Yassine Benajiba and Graham Horwood, ICML 2025, PMLR 267:35581–35602. The [official proceedings record](https://proceedings.mlr.press/v267/li25bp.html) dates the conference to 13–19 July 2025 and links the [final proceedings PDF](https://raw.githubusercontent.com/mlresearch/v267/main/assets/li25bp/li25bp.pdf). All 22 pages were read, including Appendices A–G, reference list and impact statement. Main Figures 1–3 and Figure B.1 were visually inspected from locally rendered PDF pages 5–7 and 15, with equations and numerical tables inspected on pages 2, 4, 6–8, 16 and 19–22. No separately linked supplementary artifact is required for the numerical claims below.

### Target, method and training design

The target is a specified full-benchmark score for a new model, estimated from acquired item outcomes and predicted outcomes for the remaining prompts. Each prompt has a text embedding, and a neural process learns conditional distributions over unobserved outcomes given observed prompt–score pairs. An attentive neural-process architecture uses Set Transformer encoders/decoders, a Gaussian latent representation and an ELBO training objective, with categorical embeddings for discrete scores and metric-type embeddings for mixed outcomes (§§2–3, Appendices A–B). HELM-Lite and the Arena-labelled data use linear layers in place of Set Transformer layers because their small model samples otherwise overfit (Appendix B.4). This is an item-response prediction model, with dependence learned from historical evaluations, rather than a source-effect model for repeated aggregate reports.

Policies include uniform and stratified sampling, embedding/score/IRT clustering, greedy combinatorial search, uncertainty sampling, latent information gain and a PPO-trained adaptive policy. The adaptive policy conditions on acquired outcomes, prompt embeddings and neural-process auxiliary predictions/uncertainties, selecting different subsets for different models. During training, complete outcomes of training models supply a reward based on reduction in average squared prediction error over the remaining prompts (§3.2.3, Eq. 7). The final evaluation instead measures mean absolute error in a dataset-balanced aggregate, so the training reward and reported evaluation objective differ. Only training models' full outcomes are used in the stated main training protocol, with new test-model outcomes acquired sequentially.

Appendix F.1 specifies 2,084 models and 28,659 prompts across six Open LLM datasets, with the earliest 1,000 models used for training and the recently evaluated models held out. MMLU uses the same models, 57 subject datasets and 14,042 prompts. HELM-Lite uses 33 models and 13,021 prompts across ten datasets, randomly selecting 23 training models. AlpacaEval uses 130 models and 805 prompts, randomly selecting 70% of models for training. Model-selection dates describe evaluation chronology, not necessarily model release date. Main results therefore test temporal transfer for Open LLM/MMLU and random model transfer for the other datasets, with additional proprietary-to-open HELM and open-to-proprietary AlpacaEval splits (§5, Fig. 2).

The experiment labelled Chatbot Arena is more narrowly a cached pairwise-comparison dataset over 80 MT-Bench prompts and six models, using only first-turn annotations. A held-out model defines test pairs. Some pair–prompt annotations are missing, and Appendix F.1 explicitly says the trained neural process predicts missing scores when an acquisition requests an unavailable label. This means the experiment does not always acquire a genuine human annotation, despite the acquisition algorithm's general description. It is not a test of the full live Arena rating process, and this substitution complicates interpretation of its reference outcome and error.

For multiple datasets, the final score averages dataset scores, with MMLU further averaged over 57 subjects (Appendix F.2). Prompt sampling and dataset weighting thus represent separate operations. AlpacaEval's near-zero errors also concern the paper's continuous logistic-regression-derived win-rate representation, which Appendix F.4 describes as smoother than binary correctness, rather than a universally easy binary human-judgment target.

### Printed numerical results and their bounds

The tables below reproduce reported source results in score units. Standard deviations come from three runs, and rounded `0.000` does not establish zero variability or a calibrated interval.

| Benchmark and budget | Uniform selection with NP, mean absolute error ± SD | RL selection with NP, mean absolute error ± SD | Locator |
|---|---:|---:|---|
| AlpacaEval, 100 prompts | 0.005 ± 0.000 | 0.001 ± 0.000 | Tables 2 and F.1 |
| HELM-Lite, 200 | 0.038 ± 0.005 | 0.030 ± 0.005 | Tables 2 and F.1 |
| Open LLM, 200 | 0.022 ± 0.002 | 0.018 ± 0.001 | Tables 2 and F.1 |
| MMLU, 100 | 0.018 ± 0.001 | 0.013 ± 0.000 | Tables 2 and F.1 |
| MT-Bench pairwise data, labelled Chatbot Arena, 40 | 0.052 ± 0.010 | 0.034 ± 0.006 | Tables 2 and F.1, dataset definition F.1 |

Table F.5, p.21, provides the more precise budget comparison: AlpacaEval uniform 100 prompts at 0.0051 ± 0.0005 versus RL eight at 0.0051 ± 0.0008, MMLU 100 at 0.0179 ± 0.0010 versus 35 at 0.0172 ± 0.0023, HELM-Lite 200 at 0.0376 ± 0.0060 versus 50 at 0.0350 ± 0.0004, Open LLM 200 at 0.0225 ± 0.0026 versus 100 at 0.0223 ± 0.0024, and MT-Bench 40 at 0.0518 ± 0.0127 versus 23 at 0.0506 ± 0.0118. These correspond to respective retained budgets of 8%, 35%, 25%, 50% and 57.5%, calculated from the printed counts. The conclusion's `35–75% of prompts` wording therefore does not accurately summarize all five Table F.5 budget ratios. These are matching observed error levels, with no reported statistical equivalence test.

Table 1, p.6, compares the learned selection with tinyBenchmarks under IRT++ and NP prediction. On MMLU with 100 items, tinyBenchmarks plus IRT++ has error 0.022 ± 0.000 and RL plus IRT++ has 0.028 ± 0.002, reversing the main text's blanket claim that RL improves selection under either predictor. Under NP, RL's 0.013 ± 0.000 improves on tinyBenchmarks' 0.016 ± 0.000. Open LLM uses 200 total selected prompts for this comparison, whereas the original tinyBenchmarks release uses 600, so the comparison is a controlled budget modification, not a result for the unmodified released subset.

Table 2, p.7, also limits claims for prediction: uniform selection on the pairwise MT-Bench data has 0.052 ± 0.010 error with NP versus 0.036 ± 0.009 from acquired-score aggregation, and Open LLM stratified sampling has 0.030 ± 0.003 with NP versus 0.023 ± 0.001 without prediction. HELM-Lite score clustering has 0.054 ± 0.010 with prediction versus 0.051 ± 0.017 without. The RL-plus-NP entries improve on the corresponding RL acquired-score aggregates in that table, but learned prediction is not uniformly better for every policy and dataset.

The auxiliary-information/reward ablation in Table 4 changes plain PPO errors from 0.004/0.017/0.033 to 0.001/0.013/0.018 for AlpacaEval/MMLU/Open LLM after adding both components. This is an empirical ablation, without a significance test supporting the prose's use of “significantly.” Table F.2 reports HELM subset-level correlations between error and metric type (Spearman 0.783), task informativeness (0.720) and evaluation variability (0.885) across 28 subsets conditioned on 50 random prompts. Those exploratory associations do not isolate causal effects of metric type or difficulty.

### Figures and uncertainty inspection

Figure 1, p.5, has five separate error-versus-budget panels with different vertical ranges. Its shaded bands are standard deviations over three runs, not confidence or prediction intervals. The purple RL curve generally lies below competitors, with substantial overlap at some budgets and especially noisy pairwise MT-Bench trajectories. The plot includes legend entries for uncertainty/information-gain policies although the main prose says their results were moved to the appendix. Printed Table F.1 supplies the exact budget-specific comparisons, including 0.035 ± 0.003 uncertainty-selection versus 0.034 ± 0.006 RL on the pairwise data, which does not establish a meaningful strict superiority from point means alone.

Figure 2, p.6, shows worse transfer under proprietary/open model splits, with HELM error bands and curves separating differently from Figure 1. Figure 3, p.7, withholds outcome data from 15 of MMLU's 57 subject subsets while making the new prompt texts available, and evaluates all subjects at test time. The visual endpoint for RL is above its fully observed MMLU endpoint, supporting the stated cold-start degradation without supplying a numerical universal threshold. This is a synthetic within-MMLU new-subject test rather than evidence of temporal construct invariance.

Figure B.1, p.15, confirms that decoding uses observed prompt/score representations, candidate prompt representations and a shared latent vector. The method's uncertainty estimates guide selection, but Appendix F.3 explicitly notes that neural-process uncertainty combines aleatoric and epistemic uncertainty and may be unreliable with scarce training models. No coverage curve or calibrated prediction interval is reported for the full-benchmark score. Appendix E's cold-start pseudo-labeling admits predictions as synthetic training outcomes when their estimated uncertainty is below an unspecified threshold, which does not turn those outcomes into direct observations.

### Methodological cautions from the printed final

The final contains several claims that should not be imported as guarantees. Section 3.1 asserts stochastic-process marginal consistency when the approximate posterior equals the true posterior, then says sufficient training data achieve that condition, without demonstrating exact posterior equality or consistency for the fitted finite-data network. The experiment establishes prediction performance in its splits, not that mathematical guarantee.

The intermediate reward in Eq. 7 is an undiscounted difference of prediction-error potentials, and Eq. 8 uses an undiscounted sum, whereas Table D.1 lists PPO discount 0.99. With finite trajectories, a potential difference telescopes to a terminal residual objective under an undiscounted sum, but a general claim of preserving the original policy requires compatible reward, discount and terminal conditions. The printed discussion does not establish those conditions for the discounted implementation or equivalence to its benchmark-level absolute-error metric. This is a reviewer-derived caution about the claimed guarantee, not a refutation of the reported experiments.

Section 3.2.3 claims acquisition cost O(K) independent of benchmark size, but Eq. 10 computes scores and a normalization over all candidate prompt embeddings, and the described policy network processes the candidate set. The figure and architecture therefore do not justify benchmark-size-independent arithmetic cost. O(K) counts expensive model evaluations when one prompt is acquired per step, while policy/NP overhead and candidate scans require separate accounting. Appendix G contains a visibly unfinished sentence ending `less than 1` on p.22, so no quantitative fraction is inferred from it. No end-to-end measured timing establishes that overhead is universally negligible.

### EEE design consequence

AB02 expands the efficient-evaluation prior art and gives an available item-level baseline when prompt texts, historical outcomes and the ability to run new evaluations exist. Passive EEE aggregate archives may lack these inputs, and adaptively acquiring new item outcomes is an operational extension rather than a recovered missing score. CEI should distinguish direct acquisitions, predicted outcomes and pseudo-labels, retain the target's dataset weights, and evaluate model/time/family transfer separately from reporter transfer. Good mean absolute error under selected held-out models does not identify a reporter's trustworthiness, independently calibrated uncertainty, or representativeness of unpublished cells.

If EEE later funds additional measurements, compare a learned acquisition policy against random sampling with direct-score aggregation as well as random selection with the same prediction model, account for acquisition and policy costs separately, and validate any interval on genuinely acquired untouched outcomes. Changing the selected items across models can still target a common fixed benchmark through an explicit reconstruction estimator, but raw averages of model-specific selected items can change the target. AB02's own prediction ablations and missing-label substitution make this distinction consequential.

## Discovery, access and review limits

This lane followed two explicitly prioritized seed works from the continuing review: [Fluid's accepted OpenReview record](https://openreview.net/forum?id=mxcCg9YRqj) and [the AEA proceedings record](https://proceedings.mlr.press/v267/li25bp.html). The first was screened for capability-dependent item portfolios and measurement continuity, and the second for learned acquisition and reconstruction of unobserved evaluation outcomes. Both were included for methodological proximity to the proposal. Primary publication checks used the official COLM accepted-paper list, arXiv's versioned author record and the final PMLR proceedings entry. The exact discovery query was `"Fluid Language Model Benchmarking" COLM 2025`, run with engine 1 on 2026-10-07, followed by direct primary opens. AB02 used the nominated proceedings URL directly rather than an additional search query. This was targeted expansion, without an exhaustive adaptive-testing census or a recall test.

AB01's blocked OpenReview final and the accessed arXiv v1 are distinguished throughout the ledger. Its present-day author code was inspected only to clarify a baseline design, with the unpinned version limitation retained. AB02's final PDF downloaded successfully and opened as a complete 22-page document. Actual local PDF page images supported all plot claims, with printed values separated from visual approximations. No new evaluations were run, no reported experiment was reproduced, and neither paper supplies EEE-specific inference about provenance dependence or unreported benchmark-level results.
