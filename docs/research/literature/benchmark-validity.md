# Benchmark validity, selective reporting, and ranking uncertainty

This reading ledger supports the [consolidated evidence index proposal](../consolidated-evidence-index.md).
Review date and search cutoff: 2026-10-07. This targeted continuation contains four fully read primary papers, including substantive methods, results, discussion and available supplementary methodological material. Primary published versions replace preprints where available. References were screened for backward discovery. Relevant figures were rendered and actually inspected as images. The corpus is purposive and does not support an exhaustive systematic-review claim.

None of these papers establishes an empirical finding about EEE, validates an EEE evidence-support score, or justifies an automatic provenance penalty.

## Findings that matter for this proposal

The strongest addition is to make ranking discrimination explicit alongside aggregate rank correlation. Micro-benchmark results show that correlation across a broad model population can coexist with poor discrimination among nearby models. EEE's evidence layer should therefore test whether uncertainty and support predict reliable comparisons at the gaps users actually encounter, with the validation population and held-out unit stated. A benchmark-level MDAD from another paper cannot be copied into an archive that lacks the same per-item predictions and repeated random splits.

Scoring methods, prompt families and operational task definitions can alter both means and model order. The prompt paper supports recording scorer and response-extraction details as part of setup. The medical position paper supports checking whether eligible benchmarks represent a declared capability, while its small retrospective clinical demonstration has important denominator and abstention limitations. Reliability across reporters and reasonable aggregation choices addresses internal consistency. External task relevance requires a distinct criterion.

Selective disclosure, unequal exposure to evaluation data and disconnected comparisons threaten inference in ways that ordinary bootstrap intervals do not repair. The Arena audit supplies concrete evidence and simulations of those mechanisms, but it does not establish that every sampling imbalance biases Bradley–Terry estimates, that every model retraction invalidates an otherwise connected fit, or that each observed provider actually contaminated training. Its heterogeneous best-of-N uplift also includes improvement in the selected checkpoint's true in-distribution ability. The appropriate EEE consequence is an explicit selection/identifiability analysis and bounded estimand, not a universal trust discount.

## Included source register

| ID | Published source and canonical primary URL | Reviewed version and status |
|---|---|---|
| BV01 | Gregory Yauney, Shahzaib Saqib Warraich, Swabha Swayamdipta, **How Reliable is Language Model Micro-Benchmarking?** https://proceedings.iclr.cc/paper_files/paper/2026/hash/2e2960f2fe9e981f33f51c78656e3ca2-Abstract-Conference.html | Published ICLR 2026 conference paper; official 24-page PDF. Earlier arXiv 2510.08730 first posted 2025-10-09. Publication year verified, exact proceedings posting day not established. |
| BV02 | Andong Hua, Kenan Tang, Chenhe Gu, Jindong Gu, Eric Wong, Yao Qin, **Flaw or Artifact? Rethinking Prompt Sensitivity in Evaluating LLMs.** https://aclanthology.org/2025.emnlp-main.1006/ | Published EMNLP 2025, November 4–9, pp. 19889–19899, DOI 10.18653/v1/2025.emnlp-main.1006. Official 11-page paper reviewed. Earlier arXiv 2509.01790 first posted 2025-09-01. |
| BV03 | Ahmed Alaa, Thomas Hartvigsen, Niloufar Golchini, Shiladitya Dutta, Frances Dean, Inioluwa Deborah Raji, Travis Zack, **Position: Medical Large Language Model Benchmarks Should Prioritize Construct Validity.** https://proceedings.mlr.press/v267/alaa25a.html | Published ICML 2025 position paper, PMLR 267:80991–81004, July 13–19, 2025. Official linked 14-page PDF reviewed. Position paper with illustrative experiments, not a prospective deployment validation. |
| BV04 | Shivalika Singh and 12 coauthors, **The Leaderboard Illusion.** https://papers.neurips.cc/paper_files/paper/2025/hash/70a93f260a51123b3c0e33ecd1b4de97-Abstract-Datasets_and_Benchmarks_Track.html | Published NeurIPS 2025 Datasets and Benchmarks Track, DOI 10.52202/085713-2620. Official 55-page final reviewed. Earlier arXiv 2504.20879v2 (72-page downloaded PDF) was also read, but is superseded for reported numbers and locators. |

Primary full-text download URLs: BV01 https://proceedings.iclr.cc/paper_files/paper/2026/file/2e2960f2fe9e981f33f51c78656e3ca2-Paper-Conference.pdf; BV02 https://aclanthology.org/2025.emnlp-main.1006.pdf; BV03 https://raw.githubusercontent.com/mlresearch/v267/main/assets/alaa25a/alaa25a.pdf (linked from PMLR); BV04 https://papers.neurips.cc/paper_files/paper/2025/file/70a93f260a51123b3c0e33ecd1b4de97-Paper-Datasets_and_Benchmarks_Track.pdf.

## BV01: Micro-benchmarking

### Design and assumptions

The study evaluates methods that select small benchmark subsets using cached per-example model predictions. The full benchmark defines the target model ranking. Section 4, pp. 5–6, uses 47 MMLU subtasks with 10,631 examples, all 24 BIG-Bench Hard subtasks with 5,761 examples, all 14 MMLU-Pro subtasks with 12,032 examples, and GPQA with 448 examples. Appendix D, p. 16, distinguishes the original available model pools from the complete-data analysis samples: 470 official Open LLM Leaderboard v2 models produce 447 complete MMLU-Pro, 409 BBH and 420 GPQA models; MMLU uses 366 models from the older leaderboard. The largest model is 141B. The subset analysis is therefore conditioned on complete cached predictions and a particular open-model population.

Most experiments use 300 source models to construct a subset and 50 target models to evaluate its utility. Model partitions are repeated 50 times, and each subtask's examples are randomly divided in half into a selection half and held-out half. Important nuance: the core source-model generalization experiments chiefly evaluate against the selection-half ranking, while Section 5.4 and Appendices I/J examine held-out-example performance. Appendix D says Section 5.2 and Appendix L use 300 random source models and a fixed, non-overlapping target set. Thus “all results on independently held-out models and examples” would overstate the design.

The six methods are uniform random sampling, equal allocation across subtasks, confidence-stratified sampling, diversity-based sampling, weighted Anchor Points, and tinyBenchmarks. Anchor Points clusters source-model confidence vectors and assigns cluster-size weights. tinyBenchmarks fits a ten-dimensional IRT representation (learning rate 0.1, 2,000 epochs). Confidence stratification uses ten strata and Horvitz–Thompson estimation. Diversity uses four dimensions. Subset sizes are 10,25,50,100,250,500,1000 for the large benchmarks and 10,25,50,100,200 for GPQA. Source-count sensitivity uses 10,50,100,150,200,250,300. Most main error bars are 95% bootstrap confidence intervals across the 50 trials; per-subtask experiments use ten trials.

Minimum distinguishable accuracy difference (MDAD), Section 3 equations 4–5, is based on the probability that subset and full-benchmark pairwise rankings agree conditional on a full-benchmark accuracy-gap bucket. The paper uses an 80% agreement threshold and rounds reported MDADs to the nearest 0.5 percentage point. This is a conditional agreement diagnostic, not a conventional pairwise significance test, a universal uncertainty interval, or a guarantee that all gaps above the first crossing behave monotonically.

### Printed quantitative evidence

| Locator | Exact reported values | Interpretation boundary |
|---|---|---|
| Fig. 1, p. 2 | MMLU-Pro ten-example Kendall correlations: random 0.52, confidence-stratified 0.41, tinyBenchmarks 0.50, Anchor Points 0.74. At 500 examples: 0.90,0.91,0.91,0.84, respectively. | Relatively strong broad rank correlation can coexist with weak discrimination at small model gaps. These are task-specific values. |
| Section 5, p. 7 | For ten-example subsets, reported lower bounds on MDAD: 3 points MMLU, 3.5 MMLU-Pro, 6 BBH and 6.5 GPQA. | The abstract mentions 4 points for BBH. Use the section locator and specify the precise setting, or avoid a blanket minimum claim combining these statements. |
| Section 5.3 and Fig. 5, p. 9 | 32 instruction-tuned 8B models, most between 27% and 40% MMLU-Pro accuracy. 51% of model pairs differ by at most 5 points; ten- and 25-example subsets have MDADs at least 5 points in this analysis. Even with 1,000 examples, most MDADs are 2 points and 21% of pairs differ by at most 2 points. | “51% of rankings are wrong” is incorrect. The 51% describes gap prevalence and motivates unreliable discrimination, not an observed misranking rate. |
| Appendix E Table 3, p. 16, 50 trials | For 50 examples, MDAD random 6.3±1.3, Anchor Points 4.10±1.3, tinyBenchmarks 5.4±1.8. For 100 examples: 4.4±1.3,3.6±1.1,3.8±0.8. Intervals are identified as 95% CIs. | Estimates retain substantial uncertainty. |
| Appendix H, p. 19 | BenTo's 801 selected examples from three subtasks: mean estimation error 1.34±0.39 vs random 1.30±0.38; Kendall 0.9332±0.0153 vs 0.9166±0.0175; both MDAD 1.5±0.5. | A correlation improvement does not automatically improve discrimination. |
| Appendix J Table 5, p. 20 | Mean MDAD increase on held-out subtask examples: random 1.18, confidence-stratified 1.12, diversity 1.12, Anchor Points 0.37, tinyBenchmarks 1.07 points. | Applies to these subtask-level selection/held-out comparisons. |

Section 5.2 reports that random selection becomes competitive at larger subset sizes (around 250 on the large benchmarks and 200 on GPQA). This does not establish a universal safe sample count for EEE, other model populations or other benchmark distributions.

### Actual figure inspection

Inspected PDF p. 2 (Fig. 1), p. 6 (Fig. 3), p. 9 (Fig. 5) and p. 16 (Tables 2–3 and methodological text). Fig. 1 visually shows that increasing sample count raises overall correlation while pairwise agreement near small gaps remains much lower than agreement at large gaps. Fig. 3's increasing subset sizes generally move the agreement curves left, and the methods become more similar at larger sizes. Fig. 5 shows many nearby models in the restricted 8B population, so a numerically modest discrimination threshold can affect many decisions. These are visual pattern interpretations; the table above quotes printed values, not guessed coordinates.

### Limits and EEE consequence

Random splits of cached models can place closely related fine-tunes in source and target sets, and complete-data selection removes missingness rather than studying it. “Full benchmark” is the reference measurement, not proof of real-world capability. These results cannot establish EEE source uncertainty, scorer uncertainty, benchmark-family representativeness or provenance calibration. They support adding close-pair comparison tests and varying the validation population. If EEE lacks item-level outcomes, use a clearly defined archive-level pairwise discrimination analogue and validate it empirically, rather than calling it MDAD or importing the published cutoffs.

## BV02: Prompt sensitivity and scoring

### Design and assumptions

Sections 3–4 examine seven models: Llama-3.1-8B-Instruct, Qwen2-7B-Instruct, Gemma-2-9B-it, the paper's Ministral-8B-Instruct-v0.2 label, GPT-4o-mini (July 2024), GPT-4.1-mini (April 2025) and Gemini-2.0-Flash (February 2025). Six benchmarks cover multiple-choice reasoning (ARC-Challenge, GPQA-Diamond, OpenbookQA), NarrativeQA, MATH and SimpleQA. GPT-4o generates twelve prompt templates, with a shared pool for the multiple-choice tasks and separate pools for the remaining tasks. Generation is greedy. NarrativeQA includes Llama plus the three proprietary models because of context limits. The paper does not clearly enumerate the item count/split used for every full main benchmark evaluation; do not substitute conventional benchmark sizes as if verified.

The multiple-choice heuristic computes answer likelihoods for the four open models. The alternative uses free generated responses and an LLM judge to judge correctness against reference answers across all seven models. NarrativeQA uses token-overlap F1 in the heuristic condition and judged correctness in the alternative. Consequently the multiple-choice comparison changes the response-production/scoring pipeline, and NarrativeQA changes score semantics. This is broader than applying two scorers to identical generated answers. Appendix A's MATH prompt set also varies supplied demonstration examples, which should not be described as only a wording perturbation. Gemini-2.0-Flash is the principal judge; GPT-4o-mini is an additional judge for ARC-Challenge.

The human audit samples 50 questions per dataset and judges twelve responses per question, from one selected model per dataset: Gemma for multiple-choice and GPT-4.1-mini for the other tasks. This yields 600 responses per benchmark and 3,600 responses overall. Three fluent-English UCSB undergraduate annotators provide 10,800 judgments, which are not 10,800 independent test items. Each annotator works approximately six hours for $75. Majority-voted labels are compared with the judge. This is a local six-task correctness audit, not a validation of all judges, answer styles or capabilities.

### Printed quantitative evidence

Table 1, PDF p. 3, reports average Kendall rank correlation across prompt templates. The matched four-open-model values must be kept separate from the all-seven-model judge results:

| Benchmark | Heuristic, four open models | Judge, same four open models | Judge, all seven where available |
|---|---:|---:|---:|
| ARC-Challenge | 0.3036 | 0.9187 | 0.9546 |
| OpenbookQA | 0.4212 | 0.7360 | 0.9386 |
| GPQA-Diamond | 0.1542 | 0.5048 | 0.8960 |
| NarrativeQA | 0.5927 | 0.8662 | Uses four models including proprietary models, not the same four-open comparison |
| MATH | 0.9593 | 0.9647 | As labeled in Table 1; avoid silently mixing populations |
| SimpleQA | — | — | Judge 0.8121 |

NarrativeQA and MATH table cells should be quoted with their actual evaluation population rather than treating every row as an identical four-open-model design. Table 2, p. 5, gives Gemma ARC judged mean 0.9027, SD 0.0048 with GPT-4o-mini and 0.0046 with Gemini; corresponding mean rank correlations are 0.9621 and 0.9546. Table 3 gives the fraction of questions with stable judged correctness across all twelve templates: ARC 86%, OpenbookQA 80%, GPQA 52%, NarrativeQA 66%, MATH 68%, SimpleQA 88%, combined 73%.

Appendix D Table 4, p. 11, reports combined human–human Fleiss kappa 0.9010 and human-majority–judge Cohen kappa 0.9247. NarrativeQA is lower at 0.6870 and 0.6699. Other task values, respectively: ARC 0.9856/0.9785, OpenbookQA 0.9919/1.0000, GPQA 0.9083/0.9778, MATH 0.8943/0.8563, SimpleQA 0.7812/0.9849. The older-model appendix Table 5 reports Llama-2 heuristic mean/SD 0.3706/0.1413 vs judge 0.5587/0.0182, and Mistral 0.6125/0.0389 vs 0.6291/0.0098.

### Source inconsistencies to retain in the audit

The prose describing Gemma ARC gives a heuristic range 0.25–0.90 and SD 0.28, then a judged accuracy range of 0.17 with SD about 0.005. A literal 0.17 range among twelve numbers cannot coexist with an SD that small. The plotted judged values and Table 2 support narrow spread, but a correction to the range is not verified. The NarrativeQA prose gives rank correlation about 0.40 while Table 1 prints 0.5927. Quote the tabulated result with its locator, and do not silently reconcile inconsistent prose by inventing a decimal correction.

### Actual figure inspection

Inspected PDF p. 4 (Fig. 2), p. 5 (Tables 2–3) and p. 11 (Tables 4–5). Fig. 2 visually shows narrower judge-score spread for many models/tasks, particularly ARC, while the differences for MATH are smaller. Means also move, which matters because a scorer/pipeline switch changes more than variance. The NarrativeQA axis is labeled accuracy even though the heuristic is F1, reinforcing the need to retain metric semantics. Table inspection confirms lower human/LLM agreement on NarrativeQA than the combined value implies. Numerical values above are printed table entries rather than inferred box-plot coordinates.

### Limits and EEE consequence

The paper supports scorer-specific setup metadata and multiple prompt checks. Its broad conclusion that prompt sensitivity is an evaluation artifact exceeds what a finite generated-prompt set, one principal judge and a small task/model-specific human audit establish. Judged correctness remains variable on 48% of sampled GPQA questions across templates. For EEE, absent scorer or prompt information is a documented comparability limitation. Estimating setup effects requires actual overlap across models, sources and settings, and a particular LLM judge should not be installed as a universal truth source on this paper's authority.

## BV03: Construct validity in medical benchmarks

### Design and assumptions

The position paper separates content, criterion and consequential validity, and argues that exam-style tests may poorly represent clinical use. A PubMed search finds 361 papers; the authors inspect the top 100 most cited papers from the last five years, classifying 60% as using constructed data and 40% hospital data. This is a citation-selected sample, not an exhaustive prevalence estimate for medical LLM research.

Section 4.1 constructs an illustrative UCSF comparison: a MedQA item's correct drug/diagnosis is mapped to RxNorm/SNOMED and used to retrieve about ten physician notes with corresponding Assessment and Plan content. Appendix B removes Plan content and appends the original question **and answer choices** to the remaining clinical note. This is a clinical-note-conditioned multiple-choice proxy, not a prospective evaluation of care, and it preserves multiple-choice scaffolding. Seven model rows appear in Table 1. Other named models and appendix experiments should not be added to the Table 1 sample count.

The alpha coefficient is the conditional probability of a correct note-based answer given a correct original MedQA answer. The paper does not clearly report the paired item denominator or confidence intervals for this criterion-validity demonstration. Appendix C mentions 1,273 MedQA items for its content analysis; that count should not be transplanted into the Table 1 experiment. Content analysis separately samples 100 inpatient and 100 outpatient notes and assigns fifteen task categories. UMLS concepts are extracted using cTAKES. Another appendix experiment changes answer-choice counts from two through seven for MedQA test, six medical MMLU test subsets and MedMCQA development, with five models; the distractor construction, seeds and uncertainty are not fully specified.

### Exact Table 1, p. 6

| Model as labeled | MedQA accuracy | Clinical-note proxy accuracy | Alpha |
|---|---:|---:|---:|
| Llama3 | 0.54 | 0.48 | 0.56 |
| GPT4 | 0.71 | 0.28 | 0.29 |
| Chimera | 0.60 | 0.45 | 0.48 |
| Biomerge | 0.57 | 0.36 | 0.49 |
| Orpomed | 0.49 | 0.24 | 0.38 |
| JSL | 0.61 | 0.37 | 0.49 |
| PMY | 0.75 | 0.36 | 0.45 |

Section 4.3 reports GPT4 abstaining on 57% of note-based questions, with abstentions counted incorrect; among answered questions its accuracy is 0.64. The 0.71→0.28 headline decline therefore mixes answering behavior and correctness conditional on answering. A summary should report coverage and answered-question accuracy alongside the unconditional score. The prose calls GPT4 the highest MedQA model, while Table 1 has PMY at 0.75 versus GPT4 0.71. Retain the table values and flag the prose discrepancy rather than repeating that ranking.

### Actual figure inspection

Inspected PDF p. 6 (Fig. 4 construction schematic and Table 1) and p. 7 (Fig. 5 answer-choice, task-composition and UMLS concept panels). Fig. 4 confirms the clinical-note construction remains tied to an original exam question and its options. Fig. 5 generally shows lower accuracy as the answer-choice count grows, though at least one curve rises at an early step, so strict monotonicity is unsupported. Clinical-note tasks emphasize treatment/management, whereas the MedQA sample emphasizes diagnosis. Clinical-note UMLS concept counts have a much longer right tail than exam questions. These are qualitative plot observations; the lines lack printed exact coordinates and should not be quoted as exact percentage changes.

### Limits and EEE consequence

The criterion demonstration is retrospective and tied to one health system, incomplete experimental denominators and medical tasks. Its strong rhetorical claim that clinical benchmarks lack validity should be kept separate from the illustrative evidence. It supports capability inclusion criteria that name the intended task, population and evaluation format, and distinguishes internal score agreement from external criterion validity. It does not validate a broad AI construct or establish that reporter support predicts model quality. A capability index can be reproducible and stable while consistently measuring a narrow exam construct.

## BV04: Arena selective reporting, data access and connectivity

### Design and source composition

The final paper audits approximately two million battles and 243 public models from 42 providers. Leaderboard-statistics analysis spans January 9, 2024–April 23, 2025. Appendix E Table 1, pp. 28–29, describes public preference data approximately 100K, tutorial/Colab battle data 1.9M, privately shared Cohere battles 43K, a live scrape 5.8K, provider API prompts 197K and leaderboard statistics 14.3K records. These overlap and are differently processed, so summing them is not an independent-data sample size. The appendix itself uses differing approximations (1.8M historical battles versus about 2M); preserve approximate totals.

Raw provider API logs contain 567,319 entries; dropping null/multi-turn records yields 197,217 single-turn conversations, November 2024–April 2025, 62% Aya and 38% Command family. A scrape collects 5,864 main-Arena battles January–March 2025, about 150/day, plus about 500 vision samples March 9–28. Private-model attribution asks models to identify themselves. This is inferred ownership with acknowledged possible misattribution, not verified provider testimony. Fourteen private aliases remain unidentified; some attributions have only one revealing response (Table 4). Maximum sampling rates consider days with at least 100 scraped samples. Cohere-associated authors' private data and experiment access make the audit possible but limit coverage of other providers.

### Printed results and simulated assumptions

| Locator in published final | Exact result/design | Boundary |
|---|---|---|
| Section 3.1 pp. 3–4, Fig. 9 p. 32, Table 2 pp. 33–34 | 27 Meta private variants in main Arena; 16 additional vision variants yield 43 across those leaderboards. | Finite scrape and inferred identities; not a census of all historical variants. |
| Section 3.2 Fig. 2 p. 4, Appendix M pp. 49–52 | Non-identical checkpoint true scores modeled Normal(mean 1200, SD 25); 3,000 synthetic votes per candidate; 20 variants yield approximately 50 points of maximum-score uplift, 50 variants around 70 relative to a randomly submitted checkpoint. | Uplift relative to the family mean includes real variation in true checkpoint skill. It is not all estimator bias against the selected checkpoint's own true skill. |
| Section 3.3 Fig. 3 p. 5 | Identical Aya-Vision-8B submissions: 1052, upper/lower 95% CI +21/−22, and 1069,+19/−23, four intervening models. Distinct Aya-Vision-32B variants: 1060,+18/−23 and 1097,+29/−25, nine intervening models. | CIs overlap. Point-score separation and displayed rank movement are not proof of a statistically established ability difference. The final low 32B value is **1060**, not the arXiv v2's 1059. |
| Abstract, Section 4 Fig. 4 p. 6, Appendix J p. 48 | Top two providers' estimated data shares 19.2% and 20.4%; 83 open-weight models together 29.7%. Counts derived from votes×two model API calls, approximately 6M calls overall; Fig. 4 shows a selected-provider subset about 5M. | Exposure estimates, not independently verified retained training data. Same prompt may reach two providers. |
| Appendix F Fig. 8 p. 31 and L Fig. 13 p. 49 | Mean within-month exact duplication 20.14%, March 26.5%; December→January exact 7.3%, cosine similarity>0.95 gives 9%. February excluded for insufficient logs. | Provider-side single-turn sample, not a complete Arena prompt census. |
| Section 4 p. 7 and Appendix Q Table 8/Fig. 18 p. 55 | Three 7B Command-family base fine-tunes with 0%,30%,70% Arena data, remaining mixture proprietary SFT. GPT-4o-2024-11-20 judges ArenaHard against Llama-3.1-8B-Instruct: win rates 23.5%,42.7%,49.9%; relative gains 81.7%,112.3%. Absolute 0→70% change 26.4 percentage points. Against 0% variant:50.0%,71.4%,79.2%. MMLU accuracy 66.5%,64.4%,65.9%. | Controlled distribution adaptation does not prove actual vendor training contamination or broad real-world degradation. Final omits some training hyperparameters included in arXiv v2. |
| Appendix N p. 52 |205 of 243 public models classified silently deprecated using average≤10 battles during March 3–April 23,2025, compared with 47 official deprecations. | This is an activity-based proxy and should not be restated as 205 confirmed official removals. |
| Section 5.1 Fig. 5 p. 8, Appendix O pp. 53–54 | Four models,two task distributions,1,000+1,000 synthetic battles; retire D between phases. A rank 1→2, B 2→1, D 3→4, C 4→3. | Illustrative task shift plus missing exposure, not a measured real-world rank-reversal frequency. Appendix also describes each model participating in 1,000 battles while scenarios say 2,000 total; avoid inventing a reconciled per-model count. |
| Section 5.2 Fig. 6 p. 9, Appendix P pp. 54–55 | Seven models,2,000battles per scenario; true ratings A 1450, B 1390, C 1250, D 1200, F 1150, E 1101, G 1000. Dense ranks A, B, C, D, F, E, G; disconnected sparse ranks A, C, B, F, D, G, E. | Cross-component relative levels are unidentified. A solver-returned total ordering is not a uniquely estimable ranking. Published ranks differ from arXiv v2. |

Appendix D's strict maximum-greater-than-mean result assumes iid nondegenerate estimates with finite expectation. Correlated checkpoints and shared votes require different dependence analysis. Appendix M equations 5–6 print the Gaussian maximum expression involving sqrt(2 log N) as equality, but that is an asymptotic approximation, not the exact finite-N Gaussian maximum expectation. More importantly, heterogeneous checkpoint uplift against a family mean combines selecting a genuinely better in-distribution checkpoint with noisy winner selection. A valid calibration exercise for EEE must distinguish those estimands.

The final paper correctly states the strong directed win-graph connectivity condition for finite unpenalized Bradley–Terry MLEs (p. 8). A weakly connected undirected comparison graph alone is insufficient in the presence of one-sided wins. Unequal model sampling does not itself imply conditional-outcome bias if the comparison likelihood is correctly specified and sampled outcomes remain representative. Retractions or deprecations become problematic through selective publication, shifting task mix, separation or lost connectivity. These distinctions should survive any summary of this paper.

### Actual figure inspection, final version

Inspected final PDF p. 4 (Fig. 2), p. 5 (Fig. 3), p. 8 (Fig. 5), p. 9 (Fig. 6), p. 51 (Fig. 14) and p. 55 (Table 8 and Fig. 18). Fig. 2 heterogeneous-variant uplift is much larger than Fig. 14 identical-weight uplift on the shared score scale. Fig. 3 renders point scores without the confidence intervals quoted in its accompanying text, which can visually overstate decisiveness. Fig. 5 explicitly couples a changing task mixture with model retirement. Fig. 6 visibly has two disconnected clusters in its sparse condition; no between-cluster ranking is identified by those battles. Fig. 18 rises on ArenaHard while Table 8's MMLU accuracies remain near the baseline, supporting local distribution sensitivity rather than a claim that every external task worsens. Exact numbers above come from printed labels/tables/text, not eyeballed curve coordinates.

Earlier arXiv figures were also inspected on PDF pp. 12, 14, 17, 24, 25 and 68, but their locators are superseded. The final corrects the older broad summary claiming about 100 points for 10 variants, uses about 50 for 20 in Section 3.2, changes the 32B lower score to 1060, and changes the sparse-graph rank table. Do not merge numbers/figure references across versions.

### EEE implication

Separate provenance lineage, setup comparability and selection into distinct evidence fields. A small archive-level standard error need not cover selective missingness or undisclosed model selection. Fit source/setup effects only when the model–benchmark–source–setup design has separable variation and adequate overlap, and specify the population to which the inferred score pertains. Connectivity diagnostics should identify components and confounding, while partial summaries within comparable connected groups remain usable. Scenario sensitivity to source omission or benchmark choice should appear under Robustness rather than be mislabeled a probabilistic confidence interval.

## Search and screening log

All searches below were performed on 2026-10-07. Routine discovery used web search engine 2; ambiguous title matching and authoritative/current verification used engine 1, followed by opening canonical primary pages. Full PDFs were then downloaded from primary servers and extracted/rendered locally. Queries are recorded literally; repeated variants intentionally checked whether suggested titles were exact papers. No date filter was used because older methodological work was eligible, and current publication checks were added explicitly.

| Search queries (literal) | Screening decision |
|---|---|
| `"Comparing Language Models the Hard Way"`; `"Comparing Language Models" "Hard Way"`; `Comparing Language Models the Hard Way statistical significance benchmark`; `"Comparing LLMs" "Hard Way"`; `"Language Models" "Hard Way" evaluation`; `"Comparing Language Models the Hard Way" paper` | No confidently identified exact scholarly source. Unresolved suggested title, not included or counted reviewed. |
| `"Don't use accuracy" language models benchmark`; `"Don’t use accuracy" "language"`; `"Don't Use" "Accuracy" LLM paper`; `"Don’t Use Accuracy" benchmark` | No unique matching primary paper established. Unresolved suggested source. |
| `"Deconstructing" "benchmarks" language model evaluation methodology`; `"Deconstructing" "MMLU"`; `Deconstructing Benchmarks language models 2025 2024 evaluation`; `"Deconstructing Benchmarks"` | Ambiguous/low-fit results, including an instruction-following MOSAIC item and translation/self-bias items; excluded from this targeted lane. |
| `language model benchmark accuracy statistical significance McNemar 2025`; `"Comparing" "Language Models" "Hard" statistical`; `"Beyond the Permutation Test" language models` | Statistical comparison discovery did not establish suggested exact titles. BV01 is the closest included full-text close-pair discrimination source. |
| `"benchmark" "missingness" "ranking" language models`; `"Ranking Under Biased Missingness"` | Found closest missingness candidate listed below; primary full-text access blocked. Not evidence. |
| `"Chatbot Arena" "The Illusion"`; `"The Leaderboard Illusion" publication 2026 2025` | Found arXiv, then verified NeurIPS 2025 final and replaced the preprint for extraction. Included BV04. |
| `benchmark evaluation "construct validity" LLM prompt sensitivity paper` | Found published medical construct-validity paper. Included BV03. Also surfaced an August 2026 judge item, candidate-only. |
| `"Prompt" "sensitivity" "rankings" benchmark large language models` | Found Hua et al. published EMNLP paper. Included BV02. |
| `"How Reliable is Language Model Micro-Benchmarking" arxiv` | Checked current official ICLR 2026 publication against preprint. Included BV01. |
| `"State of What Art" multi prompt evaluation` | Backward citation check from BV02; retrieved primary abstract, candidate-only, not fully read. |
| `"Investigating Data Contamination in Modern Benchmarks"` | Backward citation check from BV04; primary ACL publication identified, candidate-only, not fully read. |

This log records query strings and decisions rather than claiming search-engine result counts. It is a purposive four-paper corpus, with two evidence gaps left explicit: a full primary missingness/non-identifiability paper and a dedicated contamination-detection experiment.

## Candidate-only / inaccessible register

| Candidate | Primary verification/access | Decision and reason |
|---|---|---|
| **Ranking Under Biased Missingness: When Model Rank Is Not Identifiable from Sparse Leaderboards**, https://openreview.net/forum?id=JiCv1bYasi; PDF https://openreview.net/pdf?id=JiCv1bYasi | Search identifies title; primary forum presents verification challenge, PDF web open fails and direct download returns 403. A secondary author post alleges 2026 workshop acceptance, which was not verified from primary publication metadata. | High-fit inaccessible candidate. Not included, not full-text reviewed, no methodological or numerical claims drawn. Publication status/version/date remain unverified. |
| **Investigating Data Contamination in Modern Benchmarks for Large Language Models**, https://aclanthology.org/2024.naacl-long.482/ | Canonical primary NAACL 2024 record identified, pp. 8706–8719, DOI 10.18653/v1/2024.naacl-long.482. | Backward citation candidate. Full paper not read in this review; contamination-detection claims should await its own review. |
| **State of What Art? A Call for Multi-Prompt LLM Evaluation**, https://aclanthology.org/2024.tacl-1.52/ | Canonical TACL 2024 record/abstract retrieved, pp. 933–949, DOI 10.1162/tacl_a_00681. | Backward citation candidate. Abstract-only, not included as read evidence. |
| **The Judge Should Know What Changed**, arXiv 2608.24419 | Search-only recent candidate. | No full-text review, no claims used. Current judge validation deserves follow-up but title match alone is insufficient. |
| Suggested **Comparing Language Models the Hard Way**, **Don't use accuracy…**, **Deconstructing…benchmark** | Exact/variant queries above do not establish unique intended records. | Unresolved titles, not verified bibliography entries. |
