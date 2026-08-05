<!-- Part 6 of 11. Previous: 05-11-inclusion-and-exclusion-rules.md. Next: 07-16-eee-record-mapping.md. -->

## 13. Metric mapping

### 13.1 Preserve reported scale

No score-distribution heuristic is allowed. The source bundle states the unit.

| Study | Unit |
|---|---|
| LLMDDI | proportion |
| TextDDI | percent |
| ZeroDDI | percent |
| ExDDI | proportion |
| DTI-LM | proportion |

Raw reported values remain in `score_details.details.reported_text`.

### 13.2 Bounds

- proportions: `[0, 1]`;
- percentage rates: `[0, 100]`;
- TextDDI Cohen’s kappa reported as percentage points: `[-100, 100]`;
- no observed-range bounds;
- no bounds inferred from table extrema.

### 13.3 Standard metric IDs

Use canonical-looking global IDs only when the source definition is sufficiently precise:

```text
accuracy
precision
recall
f1
f1_macro
cohen_kappa
auroc
auprc
```

### 13.4 Namespaced metrics

Use namespaced IDs when aggregation or variant details are source-specific or incompletely reported:

```text
textddi.twosides.pr_auc
textddi.twosides.roc_auc
textddi.twosides.accuracy
exddi.bleu
exddi.rouge_1
exddi.rouge_2
exddi.rouge_l
zeroddi.czsl.unseen_class_average
zeroddi.czsl.unseen_top_1
zeroddi.czsl.unseen_top_3
zeroddi.czsl.unseen_top_5
zeroddi.gzsl.unseen_class_average
zeroddi.gzsl.unseen_top_1
zeroddi.gzsl.seen_class_average
zeroddi.gzsl.seen_top_1
zeroddi.gzsl.harmonic_class_average
zeroddi.gzsl.harmonic_top_1
zeroddi.gzsl.p_unseen
zeroddi.gzsl.p_seen
```

`metric_kind` may still use a broad family for search, but the ID must not imply an unreported implementation.

### 13.5 Uncertainty

Typed uncertainty is emitted only when the source identifies it:

- TextDDI Table 2 and Table 5: `standard_deviation`, five random seeds;
- ExDDI Table A2: `standard_deviation`, five-fold cross-validation, except ExDDI-IC;
- ExDDI-IC: no uncertainty, one run;
- DTI-LM: ten split repetitions are recorded, but no numeric SD is invented when only means are published;
- LLMDDI fine-tuning: five repeated classifications and “no variability” are recorded as textual details; do not manufacture `standard_deviation=0` unless the final source reports a numeric zero;
- ZeroDDI: no uncertainty unless explicitly present in the final selected table.

---

## 14. Method and model identity

### 14.1 No name-only global resolution

The adapter does not call the registry and does not infer exact releases from labels.

Examples such as “Claude 3.5 Sonnet,” “Gemini 1.5,” or “GPT-4o” may omit a dated model version. They receive source-scoped IDs:

```text
llmddi/claude-3-5-sonnet-reported
llmddi/gemini-1-5-reported
llmddi/gpt-4o-reported
```

Their actual provider is recorded as `developer`, while `model_info.additional_details` states `exact_release_not_reported=true`.

An exact global/Hugging Face ID is used only when the primary paper or pinned repository establishes it.

### 14.2 Paper-defined methods

Use study-scoped IDs:

```text
textddi/textddi
zeroddi/zeroddi
exddi/exddi-s2s
dti-lm/dti-lm
```

Ablations use distinct IDs rather than overwriting the parent method.

### 14.3 External baselines

`methods.yaml` must explicitly map:

- original method name;
- developer/author namespace used for EEE;
- original citation;
- whether the current paper reran it or copied the result;
- implementation identity if reported.

No method is assigned to the current paper’s authors merely because it appears in their table.

### 14.4 Evaluator relationship

Derived per log:

| Situation | Value |
|---|---|
| Paper authors evaluate their own proposed method or paper-defined wrapper | `first_party` |
| Paper authors rerun an external model/method | `third_party` |
| Score copied from prior work, or evaluator cannot be established | `other` |
| Joint evaluation with method developers explicitly established | `collaborative` |

`result_provenance` in the source row controls this derivation and is retained in output details.

---

## 15. Dataset identity and licensing

### 15.1 Aggregate-only rule

The adapter and datastore records contain no:

- DrugBank XML/CSV/JSON content;
- drug descriptions;
- drug IDs or pair IDs;
- interaction labels at instance level;
- train/validation/test membership;
- model inputs or outputs.

Only aggregate published metrics and non-substitutive dataset statistics/protocol descriptions are stored.

### 15.2 DrugBank-derived datasets

Use `SourceDataPrivate` with `source_type="other"` for DrugBank-derived evaluations. This reflects restricted/licensed raw data and prevents EEE from implying that a redistributable benchmark dataset is attached.

Store:

- DrugBank version;
- study-specific extraction and filtering;
- high-level counts;
- task formulation;
- split policy;
- paper and repository provenance.

Do not link to or package unauthorized raw downloads.

### 15.3 Public database-derived datasets

Use `SourceDataUrl` for TWOSIDES, DDInter, and BindingDB-derived collections, pointing to authoritative database/paper/repository landing pages. Do not use `SourceDataHf` unless the selected source snapshot is actually grounded in a verified Hugging Face dataset artifact.

### 15.4 ExDDI paired corpus

Dataset names:

```text
ExDDI paired corpus — DrugBank explanations
ExDDI paired corpus — DDInter explanations
```

Both records state that positive and negative pair sets were intersected across sources and balanced, while explanation supervision differs.

### 15.5 DTI-LM BindingDB preprocessing

The output metadata records the code-defined label contract:

```text
measurement: Kd in nM
positive: Kd < 30
negative: Kd > 100
excluded: intermediate values
repeated measurements: mean per drug/target/SMILES/sequence tuple
protein sequence maximum: 700
SMILES length maximum: 510
```

This is necessary for benchmark identity and reproducibility.

---


---

[Previous](05-11-inclusion-and-exclusion-rules.md) · [Design index](../DESIGN.md) · [Next](07-16-eee-record-mapping.md)
