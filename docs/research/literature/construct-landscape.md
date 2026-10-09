# Construct validity across the benchmark literature

This reading ledger supports the [consolidated evidence index proposal](../consolidated-evidence-index.md). Review date and search cutoff: **2026-10-07**. It adds one fully reviewed primary source, CV01, to the critical evidence map. The source conducts its own systematic review; this ledger does not claim that the surrounding EEE literature search is systematic or exhaustive.

## CV01 — Measuring what Matters: Construct Validity in Large Language Model Benchmarks

**Publication and exact version.** Andrew M. Bean, Ryan Othniel Kearns and coauthors, NeurIPS 2025 Datasets and Benchmarks Track. [Canonical proceedings record](https://proceedings.neurips.cc/paper_files/paper/2025/hash/1967e0fc3aa6cbbace562f5cb8e3954e-Abstract-Datasets_and_Benchmarks_Track.html), [accepted 82-page PDF](https://proceedings.neurips.cc/paper_files/paper/2025/file/1967e0fc3aa6cbbace562f5cb8e3954e-Paper-Datasets_and_Benchmarks_Track.pdf), DOI [10.52202/085713-0590](https://doi.org/10.52202/085713-0590). The proceedings and PDF spell the title “Measuring what Matters,” with lowercase “what.” The accepted PDF, rather than the earlier [arXiv 2511.04703](https://arxiv.org/abs/2511.04703) text, supplies all paper results and page locators below. Its SHA256 is `0b43c8d2cf78f35f51f4695ff74d570a1d473abe11d63670e6b1ddbc50d718d3`.

**Reading coverage.** Read the complete substantive main text on pp. 1–11, the paper checklist on pp. 16–22, and Appendices A–E on pp. 24–51, including the complete taxonomy, codebook, screening prompts, confusion matrix and agreement methodology. The main references were read and the additional reviewed-paper bibliography was screened as a discovery resource. These bibliographic entries are not counted as separately reviewed sources. Figures 1–4, Tables 12–14 and the agreement equation were inspected as actual rendered page images. No PDF or appendix access gap remains. The linked author repository received a bounded audit of row counts, duplicate article keys and relevant analysis cells, rather than a complete independent reproduction of the review.

## Review population, screening and unit of analysis

The sampling frame is 46,114 conference articles: ICML, ICLR and NeurIPS proceedings from 2018–2024, and ACL, NAACL and EMNLP proceedings from 2020–2024 (§3, p. 3). The NLP range begins later because of abstract availability. Searching titles and abstracts for “benchmark” together with “LLM” or “language model” identifies 2,189 articles. Only 14 keyword hits come from 2018–2019. Keyword vocabulary and abstract availability therefore influence temporal coverage, alongside any genuine increase in benchmark publication.

Eligibility requires a capability benchmark with empirical LLM results, compatibility with text or vision, and a new benchmark or substantial modification of an existing benchmark. Papers concerned only with speed or energy, opinion/review papers, incompatible modalities, and minimally repackaged combinations are excluded. GPT-4o mini performs the initial filtering. Appendix D/Table 12, pp. 48–49, reports three successive exclusions: 1,251 articles removed, leaving 938; 92 removed, leaving 846; and 324 removed, leaving 522. The prompts ask whether a new benchmark is implemented, what modality is primary, and whether benchmarking is the primary contribution. These prompts should be read alongside the main inclusion criteria before attempting replication, rather than assumed to be a perfectly literal implementation of four separate eligibility questions.

Twenty-nine reviewers matched by expertise manually assess the 522 candidates, with **445 included articles** reported in the main text and Figure 1. The article is the review record: a benchmark may comprise many tasks or reused datasets, and several papers can share upstream materials. Consequently 445 is not a demonstrated count of independent evaluation datasets, independent tasks, or unrelated evidence lineages. The paper does not supply an independently validated benchmark-family deduplication count.

A random 50-article validation sample from the 2,189 keyword hits gives eight true inclusions, two false inclusions, 39 true exclusions and one false exclusion (Table 13, p. 49). The authors report precision 80%, recall 89% and F1 84%. The overall confusion matrix contains only nine human-positive articles, so those percentages are a small-sample check of automated screening, not a tightly estimated recall guarantee over the full proceedings population. The keyword stage itself is not validated by that sample. The 445/522 manual inclusion fraction is approximately 85%, a different quantity from recall. The review acknowledges possible undetected automated false negatives, exclusions of industry benchmarks without peer review and specialized venues, and changes in language use over time (§6, p. 10).

## Coding design and reliability

The codebook follows the chain from a declared phenomenon through a concrete task and scoring metric to the interpretation of results. It covers definitions and scope, task ecology, sampling and data provenance, response formats, scoring and aggregation, statistical comparison, and validity claims. The main text describes 21 question items and the agreement analysis describes 30 categorical fields, while Appendix C includes additional administrative, free-text and cleaned fields. These counts describe different levels of the annotation schema and should not be treated as interchangeable without documenting the mapping.

One primary reviewer codes each article. A second reviewer maps responses to simplified categories used for statistics, with that mapping checked by the primary reviewer. This second processing step is not equivalent to two independent full-paper readings for every article. Forty-six randomly selected papers are reported as independently double reviewed. The first author reads 50 articles and all 445 annotations to develop recommendations through open coding, then multiple authors refine the recommendations over five meetings (§3, p. 3).

Appendix E, pp. 50–51, reports mean percent agreement **68.11%** and mean Brennan–Prediger kappa **0.524** across 30 fields. For binary and multiclass questions, percent agreement uses exact labels. For multi-label questions, it averages Jaccard similarity of the selected sets. The kappa calculation uses a uniform-category chance baseline. Multi-label pairs are first converted to a binary agreement decision when Jaccard similarity exceeds **0.3**, then receive a binary kappa calculation. Thus the multi-label percent agreement and kappa do not measure the same agreement event. A mean over these fields also does not establish uniformly reliable coding of substantive validity judgments.

| Field, Table 14 (p. 51) | Percent agreement | Brennan–Prediger kappa | Interpretation |
|---|---:|---:|---|
| Inclusion | 93.48% | 0.870 | Eligibility agreement is substantially stronger than agreement on several interpretive features. |
| Task face validity | 95.12% | 0.927 | Agreement on a prima facie coding question is not independent external validation of capability measurement. |
| Metric access | 95.12% | 0.902 | A relatively objective property. |
| Whether phenomenon is defined | 53.66% | 0.073 | Weak reproducibility for a prominent headline classification. |
| Whether definition is contested | 48.78% | 0.317 | The consensus judgment remains interpretive. |
| Dataset sampling method | 37.80% | 0.122 | A multi-label field, with thresholded Jaccard used for kappa. |
| Task ecology | 31.71% | 0.146 | Low agreement on proximity to a real application. |
| Author discusses validity | 53.66% | 0.305 | The reported prevalence should retain annotation uncertainty. |

These results support transparent field-specific assurance rather than a blanket label of reliable validity classification. The paper's recommendations are a qualitative synthesis informed by the coded corpus, not an empirically calibrated scalar validity score or proof that adopting every checklist item improves downstream prediction.

## Numerical results, with denominators and claim boundaries

The following are **reported paper values**, not new EEE measurements or independently reproduced article-level estimates. The source inconsistencies in the next section limit attempts to reconstruct exact prevalence from the appendix or current released data.

| Locator | Reported result | Boundary |
|---|---|---|
| §4, p. 4 | 78.2% provide a phenomenon definition. Among definitions, 52.2% are described as widely agreed and 47.8% contested. | The conditional denominator matters. These are coded descriptions, not demonstrated construct validity. |
| Figure 3, p. 5 | Definition categories: 40.9% widely agreed, 37.4% contested, 21.7% undefined. | These unconditional displayed percentages should not be silently combined with the conditional prose percentages. |
| §4, p. 4 | 40.7% use constructed tasks; 28.5% exclusively constructed. Less than 10% use complete real-world tasks; partially real-world and representative tasks appear in 32.3% and 36.9%. | Task categories can overlap. “Real-world” remains a reviewer coding judgment with low reported agreement. |
| §4, pp. 4–5; Figure 3 | 12.3% use only convenience sampling and another 27.0% partially use it. Figure 3 shows 60.7% without convenience sampling. | Absence of convenience sampling does not establish representative coverage. §5.3's shorthand 27.0% omits the exclusively-convenience group. |
| §4, p. 4 | Task items are author crafted in 43.3%, reused from benchmarks in 42.6%, and LLM generated in 31.2%; 33.6% have a single source. | Multiple sources can contribute to one benchmark. These categories cannot be summed as disjoint source shares. |
| §4, p. 5 | Exact matching appears at least partially in 81.3% and exclusively in 40.7%; LLM judging in 17.1% and exclusively in 3.1%. | These are broad metric categories, not model performance or grader accuracy. |
| §4, p. 5; Figure 3 | 16.0% use uncertainty estimates or statistical tests to compare results; 53.4% present evidence or discussion of benchmark construct validity. | The coded statistical category is broader than hypothesis testing alone. Discussing validity does not mean validity was established. |
| §4, p. 5 | 35.2% compare with benchmarks of similar phenomena, 32.4% with human baselines, and 31.2% with more realistic settings. | The “more realistic” field includes benchmarks coded as realistic themselves in Appendix C; it is not necessarily a new external validation experiment. |

The eight recommendations address explicit construct definition, auxiliary task confounds, representative task sampling, limitations of dataset reuse, contamination, statistical model comparison, error analysis and justification of the measurement claim (§5, pp. 5–10; Appendix A). Their practical scope is useful, but the paper does not experimentally validate a universal ranking of these practices. For example, reusing a well-characterized dataset can have different strengths and weaknesses from constructing new items. An EEE inclusion policy should evaluate the specific operationalization and evidence rather than assign an automatic penalty to reuse.

## Source inconsistencies and released-data audit

Figure 4 on p. 48 **visibly prints 426** at the final inclusion node, whereas its caption, Figure 1 and the main text report 445. This is a source-internal flowchart discrepancy. No correction was verified in the targeted search. The ledger retains 445 as the main reported article count and does not invent a reconciled number.

Appendix C's summary counts sometimes exceed 445. On p. 42, phenomenon-defined counts are 348 yes and 99 no, totaling 447; definition-consensus counts are 225 contested, 203 widely agreed and 27 undefined, totaling 455. Other single-field totals also differ. These discrepancies make the appendix unsuitable for an unqualified reconstruction of per-article prevalence.

A bounded audit of the [author repository](https://github.com/am-bean/benchmark_review) at commit `ac85a25b618b9225fd92d1705119527d8ee1c7fa`, retrieved on 2026-10-07, gives a possible explanation for several appendix totals while exposing a reproduction limit:

| Released artifact at that commit | Audit result | Limit |
|---|---|---|
| `data/final_list.csv` | 522 rows and 522 unique titles, matching the post-LLM-screen count. | This file represents candidates before the final manual inclusion decision. |
| `data/clean_codebook.csv` | 455 rows, 445 unique `bibkey` values, ten surplus duplicate-key rows. Nine keys repeat, with one appearing three times. | Duplicate article keys are annotation records, not additional independent papers. A rule for choosing or reconciling them is needed before computing article-level frequencies. |
| `data/clean_codebook.csv` | Phenomenon-defined values: 348 yes, 99 no, eight missing; consensus values: 225 contested, 203 widely agreed, 27 undefined. | These counts match Appendix C's summaries. That agreement does not independently validate the main percentages or identify their exact denominator. |
| `data/merged_annotations.csv` | 82 rows and 41 unique article keys, two records per key. | The available file covers 41 double-annotated articles, fewer than the 46 described in the paper. The paper does not pin this repository revision, so this is a version-qualified reproduction discrepancy. |

The released agreement notebook includes alternative coefficient calculations and the coding notebook includes response-mapping and summary operations. Those files were inspected for the relevant count and duplicate logic but were not executed as a full reconstruction of Table 14 or Figure 3. An arbitrary first-row deduplication would silently decide disagreement, so no corrected prevalence is supplied here. The paper's stated sample size, appendix annotation totals and current release must remain distinct until the exact analysis version and resolution rules are verified.

Other interpretation discrepancies include §5.1 describing 47.8% as though it applies to all benchmarks although §4 conditions it on provided definitions, and the headline “statistical testing” language broadening a result that includes uncertainty estimates. Appendix B's task-format prose also uses different percentages from §4. These are reasons to cite the precise locator and category, rather than infer a single uniform denominator or repair the source silently.

## Actual figure and table inspection

Figure 1 (p. 2) shows the stated 46,114→2,189→522→445 selection chain and the phenomenon–task–metric–claim relationship. Figure 2 (p. 4) presents only the three most common categories within each of three broad groups, rather than the full taxonomy. Its year panel shows increasing counts concentrated in 2024. The growth in absolute articles discussing validity does not show an increasing proportion or a causal improvement in practice. Bar heights were read qualitatively; no unlabeled counts were treated as exact observations.

Figure 3 (p. 5) is an alluvial display of five selected coding questions. The printed category percentages are exact source annotations. The pale path described in the caption identifies records satisfying the selected preferred categories; its small width was not converted into an exact percentage. The vertical ordering expresses the authors' preference for certain practices, rather than a validated cardinal validity scale. There are no sampling confidence bands or annotation-error intervals in this plot.

Figure 4 (p. 48) was visually inspected, revealing the 426 final-node discrepancy that text extraction missed. Tables 12–13 (p. 49) were inspected to verify the screening counts and the eight/two/39/one confusion matrix. The agreement equation on p. 50 and Table 14 on p. 51 were inspected to verify the Jaccard threshold, uniform-category correction and low agreement on interpretive fields. Numerical values above come from printed tables, labels or prose, with reviewer computations explicitly identified as released-data audits.

## Consequences for the evidence-index proposal

CV01 supplies broad primary evidence for requiring a declared construct, task population and scoring procedure before interpreting a consolidated score as capability. It also makes the claim chain auditable: reporting provenance and consistency concern support for a measurement, while ecological, convergent, discriminant and external criterion validity concern what that measurement represents. A stable aggregate of well-documented reports can still consistently measure an unsuitable proxy. Neither reporter agreement nor high explained variance supplies the missing external validity evidence.

The proposal should therefore record benchmark eligibility and construct rationale separately from report provenance. Definition disputes, task reuse, scorers and format demands can enter explicit sensitivity analyses, with uncertainty in those classifications visible. The low agreement on task ecology and sampling method cautions against immediately converting qualitative review labels into precise weights or a single evidence score. A new EEE annotation protocol would require its own independently double-coded reliability assessment and adjudication procedure.

CV01 does not validate ECCI, SACI or DLCI, establish the prevalence of these problems in the EEE archive, or calibrate a capability penalty. Its survey frame stops at 2024 and does not represent the complete 2025–2026 benchmark landscape. It strengthens the need for a scoped capability interpretation and transparent measurement metadata, while retaining the proposal's empirical burden to show improved prediction, calibration and decision stability on its own data.

## Search and access log

All retrieval and verification occurred on 2026-10-07. The source was selected because the construct-validity review is directly relevant to benchmark inclusion and interpretation, rather than to increase citation count.

| Action or exact query | Outcome |
|---|---|
| Open canonical NeurIPS proceedings record and its Paper link | Verified exact title, NeurIPS 2025 Datasets and Benchmarks status, DOI and final 82-page PDF. |
| `"Measuring what Matters" "Construct Validity" "426" "445"` | Searched for resolution of the inclusion-flow discrepancy; no verified correction located. |
| `"Measuring what Matters" "Construct Validity" correction erratum` | Current source and author pages surfaced; no correction was verified. |
| Open linked Hugging Face dataset and GitHub repository | Hugging Face preview reported a schema-cast error mixing differently shaped CSV files. Public GitHub checkout succeeded, permitting the bounded row-count audit. |
| Backward screening of the source references | Identified BetterBench, HiBayES, Adding Error Bars to Evals, foundational construct-validity work and multi-prompt evaluation as follow-ups. They are not additional fully read sources in this ledger. |

The paper PDF and its substantive appendices were fully accessible. The unresolved gaps concern denominator reconciliation, exact paper-to-code version matching and a full independent reconstruction of annotation statistics, rather than an unread methods section. No secondary explainer or search snippet supplied the methodological or numerical findings used above.
