# Consolidated evidence index for Eval Cards

> Status: exploratory research/design proposal. This document intentionally preserves minute detail for critique and pruning. It does **not** modify the EEE schema, adapters, validators, datastore semantics, or Eval Cards production behavior.

The [literature review and reading ledger](consolidated-evidence-index-literature.md), updated on 2026-10-07, grounds the proposal in source-level methodology, numerical results and visually inspected figures. The Performance / Evidence / Robustness decomposition remains the leading product hypothesis, with estimator choice, evidence calibration and temporal comparability subject to the research gates below.

## Motivation

Eval Cards currently expose many heterogeneous benchmark results per model. This is valuable for transparency, but it leaves a recurring interpretation problem: users can inspect dozens or hundreds of scores without an obvious higher-level answer to questions such as:

- What does the total body of available evaluation evidence suggest about a model's capability in a declared domain?
- How much direct and independent evidence supports that conclusion?
- How much do repeated reports disagree?
- How sensitive is the apparent conclusion to reasonable choices about benchmark inclusion, normalization, and aggregation?
- How should a displayed summary evolve as benchmarks saturate and new benchmarks appear, without silently erasing historical comparability?

EEE is a sparse, hierarchical archive of reported performance claims whose metric semantics, evaluation configurations, benchmark families and provenance vary across observations, so a useful summary must explain both the capability represented by the aggregate and the evidence supporting that representation. The proposed **higher-dimensional consolidated evaluation field** therefore accompanies a central capability estimate with direct coverage, repeated-report disagreement and sensitivity to defensible construction choices, preserving access to the benchmark-level results that make the summary interpretable.

## Product constraint

The output must be suitable for display as a field on an Eval Card. That constrains the research direction heavily.

A successful design should:

1. produce a compact model x capability summary;
2. preserve drill-down to underlying evidence;
3. not conflate low capability with weak evidence;
4. not hide substantial source disagreement;
5. not imply precision unsupported by EEE's data structure;
6. remain interpretable to users who do not know the statistical machinery;
7. degrade gracefully when evidence is sparse;
8. avoid requiring arbitrary "trust scores" for organizations;
9. avoid silently imputing unobserved benchmark results;
10. avoid presenting one ranking as uniquely correct when plausible aggregation choices materially change model ordering.

A UI sketch could eventually resemble:

```text
Reasoning Index 74.2
95% confidence interval for the declared mean: 71.8-76.9
Evidence: strong
9 benchmark families | 4 reporting organizations
Cross-source disagreement: moderate
Within 2 reference-scale points of the baseline in 88% of weighted specifications
```

The underlying field should retain all primitive quantities used to render labels such as "strong" or "moderate."

## Core design principle

**Capability and evidential support must be different variables.**

A weakly documented high score provides limited support for a capability conclusion, with the reported value retained and the documentation gap represented in the evidence layer.

Likewise:

- multiple independent, concordant reports should generally increase precision;
- multiple credible but conflicting reports should generally increase heterogeneity or uncertainty;
- missing configuration information should usually weaken evidential support or increase uncertainty rather than mechanically subtracting capability points;
- an unevaluated benchmark should not be silently treated as a zero;
- a benchmark appearing many times through slices, composites, aliases, or repeated reporting should not automatically count as many independent pieces of evidence.

## Candidate set after adversarial filtering

Three ideas survive current critique. The first two are the preferred near-term project. The third is a higher-risk temporal extension.

### Candidate 1: Evidence-Calibrated Capability Index

For model `m` and declared capability `c`, define a vector-valued result:

```text
ECCI_mc = [
    theta_hat_mc,
    uncertainty_mc,
    direct_coverage_mc,
    replication_independence_mc,
    heterogeneity_mc,
    capability_coverage_mc
]
```

Where:

- `theta_hat_mc`: consolidated capability estimate;
- `uncertainty_mc`: statistical uncertainty around the estimate;
- `direct_coverage_mc`: how much of the current capability representation is supported by directly observed evaluations on the model;
- `replication_independence_mc`: how much repeated support comes from meaningfully distinct reporters / runs / evidence paths;
- `heterogeneity_mc`: degree of disagreement among nominally comparable observations;
- `capability_coverage_mc`: breadth of the declared capability represented by the contributing benchmark families.

#### Why this is preferable to trust-weighted averaging

A tempting approach is:

```text
consolidated_score = sum(score_i * trust_i) / sum(trust_i)
```

This should not be the default.

A scalar trust weight is difficult to interpret and validate because:

- source reputation is not identical to measurement reliability;
- a source can be strong on one benchmark family and weak on another;
- source selection is non-random;
- incomplete documentation and actual measurement error are different phenomena;
- the same organization may produce multiple reports that share infrastructure or assumptions;
- trust weights can mechanically suppress a real score rather than represent uncertainty about it.

A better abstraction is a measurement model over repeated observations.

A minimal conceptual form is:

```text
z_mbr = theta_mb + alpha_source(r),b + gamma_setup(r),b + epsilon_mbr
```

Where:

- `z_mbr` is a normalized observation for model `m`, benchmark `b`, report `r`;
- `theta_mb` is latent model-benchmark performance;
- `alpha_source(r),b` captures source-specific deviations where overlap permits estimation;
- `gamma_setup(r),b` captures identifiable evaluation-setup effects;
- `epsilon_mbr` captures residual variation.

This is only a conceptual starting point. The actual estimator should be selected after EDA establishes the observation grain, target and identifiable contrasts.

The estimator must first define the performance target: a fixed portfolio under a declared evaluation protocol, a mean across specified report conditions, or another explicitly bounded quantity. Source and setup effects require location constraints, an identifiable design and sufficient crossed observations, with graph connectivity serving as an initial diagnostic. A source that evaluates a distinctive subset of models or uses a distinctive setup can remain confounded with model selection or protocol effects even in a connected graph, and a fitted source effect consequently describes a conditional deviation rather than organizational accuracy or trustworthiness.

Uncertainty about the pooled mean and uncertainty when predicting another report have different targets, because a new report can add between-run or between-setup variation and its own measurement error. The [evidence-synthesis reading ledger](literature/evidence-synthesis.md) supports this distinction, while transferring random-effects methods to EEE requires defensible sampling variances, comparable outcomes and a dependency model. Version 0 should expose observed dispersion and support counts when those requirements cannot be established, with any inferential interval labelled by its target and assumptions.

#### Critical identifiability threat

The above model can fail if most model-benchmark-metric cells have only one observation, or if reporter overlap is too sparse.

If the data cannot identify source or setup effects, the system should fall back to simpler transparent quantities rather than overfit a hierarchical model.

A valid fallback may be:

- robust central tendency where repeated reports exist;
- explicit number of reports;
- explicit number of distinct reporting organizations;
- explicit direct benchmark-family coverage;
- explicit disagreement statistic where comparable repetitions exist;
- a low-support label or withheld inferential interval when the evidence cannot identify the requested uncertainty target.

#### Validation target

Learned evidence labels and source-aware adjustments must earn their interpretation through prediction and calibration, while descriptive support fields remain auditable properties of the observed archive.

A core test:

> Among model-benchmark cells with multiple reports, does evidence-aware synthesis improve prediction of a held-out reporter or later-arriving report relative to mean, median, first-report, or source-naive baselines?

If not, the complex evidence model should be simplified or rejected.

Successful prediction of later published reports supports the specified observed reporting population. Claims about unreported cells or the whole capability portfolio require explicit selection assumptions or additional evidence.

---

### Candidate 2: Stability-Aware Composite Index

Even perfectly measured benchmark scores do not determine a uniquely correct aggregate capability score.

There are defensible choices about:

- benchmark inclusion;
- benchmark-family balancing;
- treatment of benchmark slices;
- treatment of composites;
- normalization;
- score directionality;
- bounded versus unbounded metrics;
- duplicate / near-duplicate handling;
- redundancy adjustment;
- minimum-support thresholds;
- source aggregation;
- temporal inclusion windows;
- treatment of saturated benchmarks.

These choices can change rankings.

Instead of hiding this, define an admissible family of index constructions:

```text
A = {A_1, A_2, ..., A_K}
```

For each model-capability pair, report quantities such as:

```text
SACI_mc = [
    central_estimate,
    lower_specification_quantile,
    upper_specification_quantile,
    top_k_specification_share,
    specification_rank_range,
    specification_stability
]
```

This distinguishes:

1. **measurement uncertainty**: uncertainty in the observed evaluation evidence;
2. **evidence sparsity**: limited direct / independent support;
3. **aggregation ambiguity**: reasonable index-construction choices yield different conclusions.

These should not be collapsed into one undifferentiated error bar.

A specification share is the weighted fraction of the declared construction set that supports a stated outcome, such as top-k membership within a fixed model cohort. Calling that share a probability requires a separate probability model over specifications or sampling outcomes, so the default display should identify the construction set, its weights, the comparison cohort and the treatment of ties. Likewise, specification quantiles describe construction sensitivity, whereas confidence, credible and prediction intervals require their own inferential definitions. The composite-index and multiverse literature provides direct precedents for this separation ([CO01–CO03](literature/composite-methods.md)).

#### Admissible specification space

The major failure mode is an arbitrary multiverse.

The admissible set must be constrained before looking at which specification favors which model.

Reasonable axes may include:

- family-equal versus benchmark-equal weighting;
- with versus without redundancy shrinkage;
- robust location versus mean location for repeated reports;
- strict versus moderate benchmark inclusion thresholds;
- alternative defensible normalizations for metrics with known semantics;
- omission of one major family at a time.

Source-level and benchmark-family resampling belong in a separately declared sampling analysis, whose target population and dependency structure determine the resampling unit. Crossed source/family dependence, copied reports and small cluster counts can invalidate a simple bootstrap, while repeated computation on the observed archive alone cannot establish nominal coverage. Every construction should retain its exclusion decisions, failed fits and effective support, preventing a numerical summary from silently conditioning on successful specifications.

Unreasonable specifications should not be included merely to inflate a robustness analysis.

#### Validation target

A useful stability metric should anticipate real future movement.

A core test:

> Does a model-capability summary labelled "high stability" move less when genuinely new evaluation evidence arrives than a summary labelled "low stability"?

This is a predictive hypothesis about future updates, separate from the descriptive value of exposing present construction sensitivity. A failed backtest should remove the future-movement interpretation, while retaining the sensitivity view when the view helps users assess materially different conclusions. Multiverse and specification-curve methods motivate that disclosure without promising stability under future evidence ([CO02–CO03](literature/composite-methods.md)).

---

### Candidate 3: Dynamically Linked Capability Index

This candidate addresses continuity as benchmark portfolios evolve.

Suppose a capability index at time `t` is represented by:

```text
B_t = {b1, b2, b3, b4}
```

and later by:

```text
B_t+1 = {b3, b4, b5, b6}
```

A naive system either:

- freezes old benchmarks forever, preserving continuity while losing measurement quality; or
- replaces benchmarks aggressively, preserving contemporary relevance while breaking historical continuity.

A possible middle path is **dynamic scale linking** using models evaluated on both old and new benchmark portfolios as bridge observations.

This should be described as linking, not automatically as psychometric equating.

The resulting field might contain:

```text
DLCI_mct = [
    theta_hat_mct,
    linkage_uncertainty_mct,
    direct_fraction_mct,
    linked_fraction_mct,
    linkage_distance_mct
]
```

Example UI:

```text
Reasoning 67
Current-scale support: 62% direct / 38% linked
95% interval for the linked mean: 62.3-71.7 reference-scale points
```

#### Major threat: construct drift

Shared models do not imply that two benchmark portfolios measure the same construct.

A new benchmark can reorder models because it emphasizes a genuinely different capability, not merely because it is a harder measurement instrument.

Therefore the correct research question is:

> For which capability domains, if any, does EEE support stable longitudinal linking across changing benchmark portfolios?

A negative answer for some domains is acceptable and scientifically informative.

#### Gating condition

This candidate should not become the main implementation effort until linkability EDA shows:

- enough bridge models;
- enough ability-range coverage among bridge models;
- sufficient monotonicity / invariance of benchmark relationships;
- sufficient graph connectivity;
- acceptable drift under multi-link backtests.

---

## Preferred synthesis

The leading design is **Candidate 1 + Candidate 2**, with Candidate 3 treated as a later extension.

The user-facing field can be conceptualized as:

```text
ConsolidatedEvidenceIndex_mc = (
    Performance,
    Evidence,
    Robustness
)
```

With:

```text
Performance = (
    central_estimate,
    interval
)
```

```text
Evidence = (
    direct_coverage,
    reporting_organizations,
    provenance_clusters,
    dependency_assessment,
    repeated_support,
    heterogeneity,
    capability_coverage
)
```

```text
Robustness = (
    specification_stability,
    rank_stability,
    leave_family_out_sensitivity
)
```

The field should not necessarily expose every primitive number in the compact card. The backend should preserve them, while the UI can progressively disclose detail.

## Candidate data contract

This is illustrative only and must not be treated as a schema proposal yet.

```json
{
  "capability_id": "reasoning",
  "performance": {
    "estimate": 74.2,
    "interval": {
      "target": "mean under the declared portfolio and evaluation protocol",
      "kind": "confidence",
      "level": 0.95,
      "lower": 71.8,
      "upper": 76.9
    },
    "scale": {
      "name": "capability_index_v0",
      "min": 0,
      "max": 100
    }
  },
  "evidence": {
    "direct_benchmark_count": 14,
    "benchmark_family_count": 9,
    "reporting_organization_count": 4,
    "provenance_cluster_count": null,
    "dependency_assessment": "unassessed",
    "repeated_cell_count": 6,
    "direct_coverage": 0.79,
    "capability_coverage": 0.71,
    "heterogeneity": {
      "value": 0.18,
      "statistic": "TODO: select a comparable-cell dispersion statistic",
      "label_thresholds_version": "TODO",
      "interpretation": "moderate"
    },
    "documentation_support": {
      "value": 0.54,
      "note": "kept separate from performance"
    }
  },
  "robustness": {
    "construction_set_version": "TODO",
    "construction_weighting": "TODO: declare normalized specification weights",
    "comparison_cohort_version": "TODO",
    "specification_stability": 0.88,
    "stability_criterion": {
      "reference": "declared baseline on the common reference scale",
      "absolute_score_tolerance": 2.0
    },
    "specification_rank_range": [5, 11],
    "top_10_specification_share": 0.91,
    "leave_family_out_max_delta": 4.6
  },
  "linkage": {
    "enabled": false,
    "direct_fraction": 1.0,
    "linked_fraction": 0.0,
    "linkage_uncertainty": null
  },
  "provenance": {
    "snapshot_id": "TODO",
    "method_version": "exploratory-v0",
    "benchmark_set_version": "TODO",
    "generated_at": "TODO"
  }
}
```

Again, this is a research object sketch, not a request to modify the EEE schema.

All numerical examples in this document are illustrative, with no fitted EEE estimate behind the example scores, interval endpoints or labels. The prototype contract separates organization counts from assessed provenance clusters and labels the rank range and top-k share as descriptive specification outputs. A later inferential contract may add explicitly typed confidence, credible or prediction intervals after validation, while preserving the specification distribution separately.

## Benchmark inclusion protocol

"Which benchmarks belong in the index?" should be treated primarily as an eligibility and measurement problem, not as a novelty claim.

A benchmark should enter a capability aggregate only if it passes explicit checks such as:

1. **semantic relevance**: benchmark content plausibly measures the declared capability;
2. **metric interpretability**: metric direction and transformation are known;
3. **identity resolution**: the benchmark is not an unresolved alias or accidental duplicate;
4. **hierarchical placement**: slices and composites are not double counted as independent evidence;
5. **minimum support**: enough models / reports exist for the intended estimator;
6. **non-degenerate variation**: benchmark is not completely saturated or otherwise uninformative in the relevant model population;
7. **incremental information**: benchmark contributes information not fully duplicated by existing members;
8. **comparability diagnostics**: where repeated variants exist, setup instability is understood;
9. **temporal status**: benchmark age and saturation are recorded rather than silently ignored;
10. **capability taxonomy assignment**: benchmark-family membership is explicit and reviewable.

Eligibility and weight should remain separate.

Eligibility should connect the declared capability to the evaluated content, population, response format and scorer. Reproducibility across comparable reports supports that measurement, while external criterion checks address its relevance to the intended use. The [benchmark-validity ledger](literature/benchmark-validity.md) documents why stable scoring and broad rank correlation alone cannot establish construct validity.

A benchmark can be eligible but receive limited effective contribution because it is redundant, highly saturated, or weakly connected.

## Metric normalization

EEE contains heterogeneous metric semantics. A valid consolidated index cannot treat every numeric value as a percentage or apply one global transformation blindly.

Normalization should use metric metadata where available:

- directionality;
- minimum / maximum;
- canonical score representation;
- metric units;
- bounded versus unbounded scale;
- chance or reference baselines where defensible;
- benchmark-specific score semantics.

Possible transformations to compare experimentally include:

1. min-max normalization using defensible semantic bounds;
2. distance above a reference baseline;
3. empirical percentile transformation within an explicit comparison population;
4. robust z-scoring within benchmark;
5. rank transformation;
6. latent-variable transformation where identifiability is sufficient.

No single normalization should be selected before stress-testing rank and scale sensitivity.

Every empirical normalization also requires a pinned comparison population and reference distribution, because adding models can change percentiles, z-scores and empirical bounds even when an existing model's reported scores remain constant. Weighting and redundancy diagnostics should use the same declared population and matched support, with a separate audit of effective influence because equal coefficients can produce unequal aggregate emphasis when indicator variances and correlations differ ([CO04](literature/composite-methods.md)).

Out-of-range values must be treated as a data/semantics diagnostic, not silently clipped.

## Hierarchy and multiplicity

Raw result count is not independent evidence count.

Potential multiplicity sources include:

- benchmark composites;
- sub-benchmarks;
- slices;
- alternate benchmark names / aliases;
- multiple metrics on the same task;
- repeated reporting of the same underlying run;
- multiple sources copying the same original report;
- benchmark versions;
- model aliases;
- duplicated model deployments;
- leaderboard snapshots.

The aggregate should define a canonical leaf unit before weighting.

A preliminary conceptual weight factorization is:

```text
W_mb =
    W_family,b
  * W_redundancy,b
  * W_measurement,b
  * W_evidence,mb
```

Where:

- `W_family,b` prevents families with many leaves from dominating;
- `W_redundancy,b` represents marginal information rather than naive benchmark count;
- `W_measurement,b` reflects discrimination / saturation diagnostics;
- `W_evidence,mb` is model-benchmark specific and depends on support / uncertainty, not source prestige.

This factorization is exploratory. It may be rejected if it becomes too arbitrary or statistically unstable.

For a capability estimate tied to a fixed portfolio, the target benchmark-family weights should be common across models, with evidence support displayed alongside the estimate. Model-specific evidence weighting changes which benchmarks determine each model's score and can therefore change the measured target, even when the weights are described as precision adjustments. Such weighting requires an explicit estimator model and a sensitivity comparison against common target weights, while missing-score renormalization must identify the resulting observed-portfolio target and restrict comparisons when models have materially different coverage.

## Missingness

EEE's reporting process plausibly creates selected coverage, with the mechanism to be investigated against a pinned snapshot.

Potential drivers of which model–benchmark cells become observable include:

- age;
- visibility;
- cost;
- API availability;
- benchmark relevance;
- organizational incentives;
- source preferences;
- expected competitiveness;
- benchmark release date.

Therefore:

- absent scores must not be interpreted as zero;
- matrix completion must not silently populate production index values;
- model-based prediction can be used diagnostically or for sensitivity analysis, but imputed values must be visually and statistically distinguishable from direct observations;
- published aggregates should preferably condition on observed support or propagate explicit prediction uncertainty.

A missingness model may itself become useful for sensitivity analysis.

The eligible cell population must distinguish inapplicable evaluations and structural absence from genuinely absent or potentially undisclosed scores before any reporting-propensity analysis is fitted.

An observed reporting-propensity model can characterize associations between coverage and recorded metadata, while dependence on an unobserved score remains an assumption requiring sensitivity analysis. A directly observed subset can still be selectively favorable, so directness and unbiasedness must be assessed separately, with matched-portfolio comparisons and explicit reporting-selection scenarios preceding any claim that an observed-subset aggregate represents the whole capability portfolio.

## Evidence dimensions

The evidence layer should avoid becoming one arbitrary second composite.

Primitive dimensions should remain available.

### Directness

How much of the displayed estimate is based on direct observations of the model on benchmarks currently contributing to the capability representation?

### Independence

How much support comes from evidence paths that are meaningfully distinct?

Potential dependence sources:

- same organization;
- same evaluation harness;
- same model endpoint;
- same original leaderboard copied by multiple downstream sources;
- same underlying run;
- same benchmark family.

A simple count of URLs is not an independence measure.

Distinct organizations should initially be counted as organizations, and provenance should group copied results and shared runs into identifiable evidence clusters. Dependence from common prompts, harnesses, model endpoints or benchmark items can remain across those clusters, so any effective-independent-support quantity requires a documented covariance or resampling model. Where dependence cannot be estimated, the card should report provenance diversity and unresolved dependency rather than label the organization count independent evidence.

### Replication

How many model-benchmark-metric cells contain repeated observations?

Repeated support can increase confidence only if repetitions are sufficiently independent and comparable.

### Heterogeneity

How much do comparable observations disagree?

Heterogeneity should be displayed rather than averaged away.

Start with descriptive disagreement in interpretable score units within comparable cells, and estimate model-based heterogeneity only when outcome comparability, variances and dependence permit it. Sparse repeats may leave a disagreement label unavailable even when a fitted variance is zero.

Potential measures:

- robust within-cell range;
- median absolute deviation;
- random-effects tau;
- posterior predictive dispersion;
- fraction exceeding benchmark-specific comparability threshold.

### Coverage

Coverage should be explicitly defined at multiple grains:

- benchmark count;
- benchmark-family count;
- capability taxonomy coverage;
- direct weight mass observed;
- source coverage.

A model with 50 scores from one narrow benchmark family should not appear more broadly supported than a model with 10 well-distributed families.

### Documentation support

Current completeness/reproducibility signals can inform evidence interpretation, but they should not directly become capability penalties.

Documentation support may affect:

- confidence;
- usability;
- ability to compare setups;
- strength of claims about reproducibility.

## Robustness dimensions

The robustness layer should quantify how sensitive conclusions are to defensible design choices.

Candidate perturbations:

- leave one benchmark out;
- leave one benchmark family out;
- leave one reporting source out;
- resample benchmark families where a declared sampling analysis justifies the cluster structure;
- resample provenance clusters where a declared sampling analysis justifies the dependency model;
- alternate family weighting;
- alternate metric normalization;
- include / exclude high-saturation benchmarks;
- include / exclude low-documentation reports;
- robust versus mean pooling for repeated reports;
- alternative redundancy shrinkage;
- alternative minimum-overlap thresholds.

Potential outputs:

- median score across specifications;
- 5th/95th percentile score;
- specification rank range;
- top-k specification share;
- pairwise specification share;
- maximum leave-family-out shift;
- share of specifications reversing a comparison against nearby competitors.

Score quantiles should be calculated only across constructions with a common score meaning or an explicitly justified mapping, because different normalizations can change the unit and target. For differently scaled specifications, compare ranks or pairwise orderings within a fixed cohort and retain the underlying scores separately. A score tolerance, tie rule and comparison target must accompany any claim of specification stability, and statistical resampling results should remain distinguishable from these construction summaries.

## Dynamic linking extension

If later pursued, temporal linking should explicitly represent indirectness.

A linked estimate should be expressed on one declared reference scale, with direct and linked support retained as provenance attributes and linking uncertainty propagated into that scale. The direct and linked fractions describe the declared support accounting, with an additive score decomposition used only when an explicit estimator defines components and weights that reconstruct the estimate.

Longer link chains require uncertainty propagation and drift diagnostics, with multiple paths providing useful consistency checks when their shared calibration errors are accounted for. Path count alone cannot establish independent information, and bridge models require pinned model identities, evaluation protocols and coverage of the relevant ability range. The [scale-linking reading ledger](literature/scale-linking.md) distinguishes shared-model linking, psychometric equating and item-level anchor calibration, whose data requirements differ materially.

When a bridge fails the declared subgroup, range or temporal checks, retain the version-specific direct scores and withhold the affected linked comparison.

Possible diagnostic graph:

- nodes: benchmark portfolio versions;
- edges: bridge-model overlap sufficient for linking;
- edge attributes: sample size, ability-range coverage, transformation stability, invariance diagnostics;
- path uncertainty: propagated over links.

A future "calibration panel" could deliberately evaluate a stable set of models across newly introduced benchmarks to maintain stronger links, but this would be an operational extension beyond passive EEE aggregation.

## Highest-priority EDA

The next scientific step is not to implement a production formula. It is to determine whether the candidate quantities are identifiable in current EEE data.

### 1. Grain reconciliation

Quantify counts at:

- atomic fact row;
- model x benchmark x metric;
- model x benchmark x metric x source;
- composite;
- family;
- slice;
- canonical benchmark;
- displayed result.

Goal: prove exactly what "one observation" means.

### 2. Repeated-observation structure

For each canonical model-benchmark-metric cell:

- number of reports;
- number of distinct organizations;
- number of distinct source URLs;
- number of distinct configurations;
- number of distinct evaluation timestamps;
- first-party / third-party composition.

Primary question: is source-aware synthesis statistically estimable?

### 3. Cross-source overlap graph

Construct bipartite / multipartite graphs linking:

- sources;
- models;
- benchmarks;
- benchmark families.

Analyze:

- connected components;
- articulation nodes;
- degree distribution;
- source concentration;
- overlap sufficient for source-effect estimation.

Include evaluation-setup identities and provenance clusters in these diagnostics. For every proposed source or setup contrast, inspect design rank and overlap under the chosen reference constraints, then test leverage and sensitivity to influential bridge sources.

Primary question: can source effects be separated from source selection?

### 4. Within-cell versus between-model variation

For benchmark-metric cells with repetition:

- within-model repeated-report variance;
- between-model variance;
- source-specific residuals;
- setup-specific residuals.

Primary question: does repeated-result disagreement materially affect conclusions?

### 5. Missingness topology

Model the probability of a reported score conditional on:

- model developer;
- model release period;
- benchmark;
- benchmark family;
- reporting organization;
- model popularity / evaluation density;
- first-party versus third-party status.

Primary question: how selected is the observed matrix?

### 6. Metric semantics audit

Quantify:

- unit frequencies;
- direction metadata coverage;
- bound metadata coverage;
- canonical-score coverage;
- out-of-bound values;
- incompatible metric groups;
- percentage-looking values outside [0, 100].

Primary question: which metrics can be safely normalized together?

### 7. Hierarchy / identity audit

Quantify:

- composite-to-leaf relations;
- benchmark aliases;
- naming near-duplicates;
- slice multiplicity;
- metric duplicates;
- model aliases.

Primary question: how much naive double counting exists?

### 8. Redundancy analysis

On matched model intersections only and with minimum sample-size thresholds:

- Pearson correlation where scale assumptions are defensible;
- Spearman correlation;
- rank agreement;
- residual correlation after capability-family effects;
- clustering;
- effective dimensionality.

Primary question: how much independent measurement information do nominally different benchmarks add?

### 9. Saturation / discrimination

For each benchmark:

- score spread;
- ceiling / floor mass;
- frontier-model spread;
- temporal trend;
- pairwise separability;
- discrimination around relevant model ranges.

Primary question: which benchmarks remain informative?

### 10. Aggregation sensitivity

Compare simple baselines first:

- unweighted normalized mean;
- family-balanced mean;
- median;
- rank average / Borda-style baseline;
- PCA / factor diagnostic;
- simple Bayesian / random-effects model if justified.

Perturb:

- normalization;
- family weighting;
- source choice;
- benchmark dropout;
- redundancy treatment.

Primary question: how unstable are model conclusions before adding sophisticated machinery?

### 11. Evidence calibration

Where later observations or repeated reports are available:

- fit on earlier / partial evidence;
- predict held-out / later evidence;
- evaluate interval coverage;
- evaluate error as a function of proposed evidence support.

Primary question: does "strong evidence" actually predict lower future error?

### 12. Temporal linkability

For Candidate 3:

- benchmark-pair model overlap matrix;
- temporal benchmark-overlap graph;
- bridge-model sample size;
- ability-range coverage;
- transformation monotonicity;
- subgroup invariance;
- single-chain versus multi-link drift;
- hold-new-benchmark-out prediction.

Primary question: can any capability sustain longitudinal linking?

## Baselines

Any method should be compared with deliberately simple baselines.

Minimum baselines:

1. equal-weight normalized mean;
2. family-balanced normalized mean;
3. median of normalized benchmark scores;
4. rank aggregation;
5. best-supported-only aggregation;
6. no consolidation: raw Eval Cards presentation.

Optional diagnostics:

7. PCA / factor scores;
8. IRT / latent trait model on coherent subsets;
9. Bradley-Terry / pairwise model on co-observed models;
10. matrix completion used only as sensitivity analysis.

## Candidate evaluation criteria

The preferred method should be judged on more than rank correlation.

### Predictive validity

Can the index predict held-out:

- benchmark results;
- reporters;
- future reports;
- benchmark families?

### Calibration

Do uncertainty intervals achieve nominal coverage?

Observed-report holdouts directly assess intervals for observed reports under the specified reporting process, using splits that hold out entire provenance clusters, model families or time windows as appropriate. Coverage of a mean parameter or latent outcome requires a defensible reference target, such as controlled simulations with known parameters or independently supported repeated measurements that account for reference uncertainty. Report interval width and the validation population alongside coverage. Close-model comparisons should also be checked for practical and statistical separation, because high whole-cohort rank correlation can coexist with unreliable local orderings.

Normalization reference distributions, eligibility thresholds, latent dimensionality, imputation, anchor selection and estimator tuning must be fitted or selected using training information. Ability profiles require out-of-family tests before a fitted low-dimensional structure is transferred to newly arriving models.

### Robustness

How much do scores / ranks change under defensible perturbations?

### Data efficiency

How quickly does uncertainty shrink as evidence accumulates?

### Interpretability

Can a user understand why a displayed score has high or low support?

### Provenance fidelity

Can every displayed component be traced to contributing observations?

### Graceful degradation

Does the field remain honest when:

- only one benchmark is available;
- only one reporting organization is available;
- metrics are incomparable;
- benchmark taxonomy is uncertain;
- repeated reports disagree strongly?

### External validity

Where appropriate, compare against external preference / capability indicators, but do not assume one external leaderboard is ground truth.

## Kill criteria

The project should be simplified or stopped if any of the following hold.

### Kill complex source modelling if

- reporter overlap is too sparse to estimate source effects;
- held-out prediction does not improve over robust averaging;
- source-effect estimates are dominated by source/model selection confounding;
- posterior / interval calibration remains poor.

### Kill elaborate evidence scoring if

- evidence labels do not predict future error or uncertainty;
- support dimensions collapse to raw benchmark count;
- results are highly sensitive to arbitrary evidence-weight choices.

### Simplify the robustness display if

- admissible specification definitions cannot be made outcome-independent;
- robustness summaries are less interpretable than direct sensitivity plots.

Remove a predictive stability label if H4 fails, preserving a descriptive sensitivity view when the current conclusions depend materially on construction choices. The choice between a compact robustness label and a direct sensitivity plot should follow user interpretation tests and decision value.

### Kill dynamic linking if

- temporal overlap graph is too sparse;
- bridge models cover only a narrow frontier range;
- benchmark relationships exhibit strong non-invariance;
- linking uncertainty grows too rapidly;
- capability construct drift dominates scale drift.

### Kill universal capability aggregation if

- within-capability benchmarks fail to support a coherent common construct;
- reasonable taxonomies imply incompatible rankings;
- one scalar consistently obscures decision-relevant tradeoffs.

## Novelty positioning

The project should **not** claim novelty for:

- generic composite indices;
- benchmark health scoring;
- benchmark subset selection;
- rank aggregation;
- IRT;
- Bradley-Terry models;
- random-effects meta-analysis;
- generic sensitivity analysis;
- benchmark redundancy detection.

Those areas have substantial existing literature.

The reviewed [AI aggregation sources](literature/ai-aggregation.md) already provide latent capability profiles and task-subset recovery. In *From Benchmarks to Skills*, the factor-score mean correlates .73 with Arena for 13 overlapping models, while a simple task average reaches about .86, so a more structured representation does not automatically yield a better scalar summary. The [scale-linking sources](literature/scale-linking.md) also provide close comparators: *A Rosetta Stone for AI Benchmarks* estimates a shared latent scale from aggregate scores on overlapping models, whereas *Growing Pains* extends an item-response scale through fixed item parameters and new anchor responses. EEE must distinguish the aggregate-score inputs currently available from the response-level data required by item calibration.

The published [general-scales study](literature/general-scales.md) adds explicit demand annotations, individual-model ability profiles and prediction across held-out benchmarks. Its demand-based random forest achieves weighted AUROC/ECE .747/.038 on that benchmark-held-out split, while fitted ability curves extend beyond observed demand levels through a heavily weighted artificial anchor. The supplement also acknowledges battery dependence in dominant slicing. These results motivate interpretable capability scales while leaving population transport, calibrated scale spacing and stability under future battery changes to separate tests.

The [HELM and construct-validity readings](literature/helm-and-construct.md) further constrain interpretation. HELM's OPT HellaSwag accuracies of 79.1%, 54.8% and 30.2% come from different adaptation protocols that also vary zero-shot/five-shot prompting, so the contrast supports protocol-aware comparison rather than an isolated answer-layout effect. Kearns's exploratory thesis reports lower transformed-score test MSE for a structured factor model than its PCA comparator, but the difference is nonsignificant under its reported test. A capability label should consequently state the measurement and validation supporting its interpretation, with descriptive factor structure kept distinct from construct validity.

The current integration target is:

> A provenance-aware, evidence-calibrated composite evaluation field for a heterogeneous live AI evaluation repository, separating model capability estimates from evidential support and aggregation robustness.

A stronger temporal extension is:

> Dynamic scale linking across evolving benchmark portfolios with explicit direct-versus-linked support and propagated linkage uncertainty.

The temporal claim should remain secondary until linkability EDA supports it. Existing work already covers latent skill profiles, sparse benchmark-score prediction and extensible benchmark calibration, and aggregate shared-model scale estimation is particularly close to DLCI, so the three provisional method names organize design alternatives without establishing novelty. The [literature synthesis](consolidated-evidence-index-literature.md) maps those overlaps and confines any prospective contribution to demonstrated provenance-aware inference and useful uncertainty disclosure on EEE's actual observation structure.

## Main research hypotheses

All hypotheses are currently exploratory.

### H1: Evidence-aware aggregation improves predictive validity

For model-benchmark cells with repeated observations, an evidence-aware estimator will improve held-out-report prediction and interval calibration relative to mean / median aggregation.

### H2: Evidence support is empirically calibrated

Models / capability estimates with higher measured evidence support will show lower subsequent prediction error and more reliable uncertainty intervals.

### H3: Aggregation ambiguity is substantial

A non-trivial fraction of model rank differences will reverse under defensible benchmark-family, normalization, and source-aggregation choices.

### H4: Robustness metrics predict future movement

Indices labelled more stable under the admissible specification set will move less when new real evaluation evidence is added.

### H5: Dynamic linking is domain-dependent

Some capability domains will admit stable longitudinal linking across benchmark generations, while others will fail because of construct drift or inadequate bridge structure.

## Possible method versions

### Version 0: transparent deterministic baseline

No learned source effects.

For each capability:

1. canonicalize benchmark / model / metric identities;
2. select eligible benchmark leaves;
3. normalize scores using metric semantics;
4. pool repeated comparable observations with robust location;
5. family-balance benchmark contributions;
6. output central aggregate;
7. output direct evidence counts / coverage;
8. output observed heterogeneity;
9. evaluate a declared construction set for sensitivity, adding cluster resampling only where the sampling target and dependency structure justify inference.

This version is likely implementable fastest and is the required baseline for all more complex models.

### Version 1: hierarchical repeated-report model

Add:

- source random effects where overlap supports them;
- configuration effects where identifiable;
- benchmark-level residual heterogeneity;
- posterior uncertainty propagation into capability aggregate.

### Version 2: redundancy-aware capability model

Add:

- benchmark redundancy shrinkage;
- effective information mass;
- latent structure diagnostic.

### Version 3: dynamic linked scale

Add:

- versioned benchmark portfolios;
- bridge models;
- link uncertainty;
- direct-versus-linked support.

Each estimator extension should justify its complexity against the simpler version on the declared prediction and calibration targets, while descriptive evidence and sensitivity fields should also be evaluated for auditability and user decision value.

## Proposed staged research plan

### Stage A: EDA and identifiability

Deliverables:

- grain map;
- repeated-result distributions;
- source-overlap graph;
- missingness map;
- metric-semantics audit;
- hierarchy / alias audit;
- redundancy analysis;
- saturation analysis;
- baseline aggregation sensitivity;
- temporal linkability graph.

Decision: whether Candidate 1, 2, and 3 are estimable.

### Stage B: baseline composite

Implement transparent Version 0.

Deliverables:

- per-capability aggregate;
- evidence primitive fields;
- construction sensitivity and, where justified, separately labelled cluster-resampling inference;
- validation suite;
- card rendering mock.

Decision: does a simple model already solve most of the product problem?

### Stage C: evidence model

Implement Version 1 only where replication permits.

Deliverables:

- source / setup heterogeneity estimates;
- held-out-report prediction;
- interval calibration;
- ablation against Version 0.

Decision: retain only if predictive / calibration gains justify complexity.

### Stage D: robustness model

Formalize admissible specification set.

Deliverables:

- specification stability;
- specification rank ranges within a fixed comparison cohort;
- top-k specification shares, with inferential probabilities added only under a validated probability model;
- leave-family-out sensitivities;
- future-update backtest.

Decision: retain a descriptive sensitivity view when it helps users assess construction-dependent conclusions, and add a predictive stability label only if the future-update backtest supports it.

### Stage E: temporal linking

Only if Stage A linkability is favorable.

Deliverables:

- bridge graph;
- invariance tests;
- link transformations;
- uncertainty propagation;
- historical backtest.

Decision: whether historical continuity can be supported for any capability.

## UI principles

The field should be understandable at three levels.

### Compact card

Example:

```text
Reasoning 74.2
Evidence: strong | Robustness: high
```

### Expanded summary

Example:

```text
Reasoning 74.2 [71.8, 76.9]
9 benchmark families
4 reporting organizations
Moderate cross-source disagreement
88% of weighted specifications within 2 reference-scale points of baseline
```

### Full evidence view

Expose:

- contributing benchmarks;
- source counts;
- direct observations;
- normalization;
- benchmark weights;
- uncertainty decomposition;
- sensitivity analyses;
- exclusions and reasons;
- method version;
- snapshot / timestamp.

No summary label should be impossible to audit back to primitives.

## Terminology

Preferred provisional names:

- **Consolidated Evidence Index (CEI)**
- **Evidence-Calibrated Capability Index (ECCI)**
- **Stability-Aware Composite Index (SACI)**
- **Dynamically Linked Capability Index (DLCI)**

Current recommendation:

- user-facing umbrella: **Consolidated Evaluation Index**;
- research method: **Evidence-Calibrated Capability Index**;
- robustness companion: **Stability-Aware Composite Index**;
- later temporal extension: **Dynamically Linked Capability Index**.

Avoid:

- "trust score";
- "truth score";
- "universal intelligence score";
- "benchmark quality score" as the main contribution;
- "equated score" unless psychometric equivalence assumptions are actually demonstrated.

## Open questions

1. What is the canonical capability taxonomy?
2. Who assigns benchmarks to capabilities, and how is disagreement handled?
3. What is the minimum model count for including a benchmark?
4. What is the minimum reporter overlap for learning source effects?
5. What constitutes an independent reporter when multiple sites copy one underlying source?
6. Should first-party and third-party evidence be modeled differently or only labelled?
7. How should model aliases / deployments be handled?
8. How should benchmark version changes be represented?
9. How should composite benchmarks and slices be prevented from double counting?
10. What normalization is defensible for unbounded metrics?
11. Should score scales be absolute, percentile-based, or latent?
12. How should saturation influence inclusion versus weight?
13. How should redundancy influence weight without over-penalizing legitimate convergent validity?
14. What minimum evidence is required to display an aggregate at all?
15. Should low-support capability scores be hidden, greyed out, or shown with warnings?
16. How should evidence support be binned into UI labels?
17. How often should the index be recomputed?
18. How are historical values versioned when methodology changes?
19. Which changes create a new index version?
20. Should the site expose current score and historical score snapshots?
21. Can future benchmark additions be used as pre-registered validation sets for support calibration?
22. How much product complexity is acceptable before the field becomes less useful than raw benchmark results?

## Non-goals

This proposal does not aim to:

- declare one globally correct AI ranking;
- replace benchmark-level Eval Cards;
- hide benchmark disagreement;
- infer missing results as facts;
- establish trustworthiness of organizations;
- certify model safety;
- collapse heterogeneous capabilities into one universal intelligence number;
- change EEE's core reporting principle of recording source data faithfully.

The consolidated index should remain an **interpretive layer over reported evidence**, not a mutation of the underlying EEE records.

## Immediate next decision

Before choosing an estimator, run the EDA / identifiability stage against a pinned EEE/Eval Cards snapshot.

The two decisive questions are:

1. Is repeated-report / cross-source overlap sufficient to support an evidence-aware measurement model?
2. How much do model-level conclusions change under defensible benchmark-family and aggregation choices?

If the answer to (1) is no, retain transparent evidence counts rather than force latent source effects.

If the answer to (2) is yes, robustness must remain a first-class displayed field rather than a supplementary analysis.

If temporal overlap is also strong, Candidate 3 becomes a serious follow-on project.

## Review status

Current research assessment:

- Evidence-Calibrated Capability Index: strongest overall candidate.
- Stability-Aware Composite Index: strongest robustness companion.
- Dynamic Linked Capability Index: high-upside, high-risk temporal extension.
- Novelty status: an integration hypothesis narrowed by direct prior art, with no first-of-kind claim established.
- Evidence status: literature-grounded design constraints alongside exploratory EEE hypotheses, with a source-level methodology, numerical and figure-reading ledger dated 2026-10-07.
- Required next step: pinned-snapshot EDA and closest-work comparisons focused on provenance-aware aggregation, interval targets, local ranking reliability, selected coverage and aggregate-versus-item-level scale linking.
