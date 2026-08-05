<!-- Part 4 of 11. Previous: 03-7-selected-source-tables.md. Next: 05-11-inclusion-and-exclusion-rules.md. -->

## 9. Repository layout

```text
utils/drug_interaction_papers/
├── __init__.py
├── adapter.py
├── source_schema.py
├── README.md
└── sources/
    ├── catalog.yaml
    ├── llmddi/
    │   ├── manifest.yaml
    │   ├── methods.yaml
    │   ├── datasets.yaml
    │   ├── protocols.yaml
    │   ├── metrics.yaml
    │   └── results.csv
    ├── textddi/
    │   └── ...
    ├── zeroddi/
    │   └── ...
    ├── exddi/
    │   └── ...
    └── dti_lm/
        └── ...

tests/
└── test_drug_interaction_papers_adapter.py
```

No PDFs, raw DrugBank data, model weights, or generated datastore JSON are committed in the adapter PR.

---

## 10. Source bundle schemas

### 10.1 `catalog.yaml`

Lists enabled immutable snapshots:

```yaml
studies:
  - study_id: textddi
    source_snapshot_id: textddi-emnlp2023-final
    path: textddi
    enabled: true
```

### 10.2 `manifest.yaml`

Required fields:

```yaml
study_id: textddi
source_snapshot_id: textddi-emnlp2023-final
paper:
  title: Learning to Describe for Predicting Zero-shot Drug-Drug Interactions
  publication_kind: conference_paper
  venue: EMNLP 2023
  doi: 10.18653/v1/2023.emnlp-main.918
  publication_date: 2023-12-01
  source_sha256: <sha256>
  page_count: 16
repository:
  name: zhufq00/DDIs-Prediction
  commit: <full commit SHA>
selected_tables:
  - table_id: table-2
    page: 6
    purpose: zero_shot_comparison
  - table_id: table-5
    page: 12
    purpose: vanilla_known_drug_comparison
snapshot_created_at: <unix epoch string>
verification:
  status: independently_cross_checked | two_pass_same_reviewer | single_pass
  notes: <string>
expected:
  methods: 20
  result_cells: 120
  logs: 40
```

The count fields are source-specific regression invariants.

### 10.3 `methods.yaml`

```yaml
methods:
  - method_id: textddi
    source_label: TextDDI
    display_name: TextDDI
    model_info_id: textddi/textddi
    developer: textddi
    method_category: text_encoder_plm
    identity_status: verified_source_scoped
    paper_owned: true
    backbone: roberta-base
    result_provenance: paper_experiment
    evidence: paper_section_4_1_4
```

Required identity statuses:

```text
verified_global
verified_source_scoped
ambiguous_release_source_scoped
unresolved
```

`unresolved` is fatal. `ambiguous_release_source_scoped` is allowed only when the adapter uses a study-scoped ID and records the ambiguity; it may not map to a specific global model release.

### 10.4 `datasets.yaml`

```yaml
datasets:
  - dataset_id: dti-lm-bindingdb-kd-binary
    display_name: DTI-LM processed BindingDB Kd binary dataset
    collection_slug: dti-lm-bindingdb
    source_data_type: url
    task_output: binary_dti
    raw_source: BindingDB
    preprocessing:
      label_measurement: Kd_nM
      positive_rule: value_below_30
      negative_rule: value_above_100
      excluded_interval: 30_to_100_inclusive_boundary_as_implemented
      repeated_measurements: mean_by_drug_target_pair
      protein_length_max: 700
      smiles_length_max: 510
    source_repository_commit: <commit>
```

All fields eventually copied into `additional_details` must be stringified deterministically.

### 10.5 `protocols.yaml`

```yaml
protocols:
  - protocol_id: exddi-one-unseen-drug
    paper_label: Inductive Test S2
    task: ddi_explanation_generation
    split_unit: drug
    pair_overlap: prohibited
    drug_entity_overlap: exactly_one_test_drug_unseen
    target_entity_overlap: not_applicable
    relation_class_overlap: not_applicable
    temporal_ordering: none_reported
    candidate_label_space: not_applicable
    train_description: both drugs from M1
    test_description: one drug from M1 and one from M3
```

Unknown fields use explicit values such as `not_reported`, not omitted values that might be misread as false.

### 10.6 `metrics.yaml`

```yaml
metrics:
  - metric_key: textddi-drugbank-macro-f1
    metric_id: f1_macro
    metric_name: Macro F1
    metric_kind: f1
    metric_unit: percent
    score_type: continuous
    min_score: 0.0
    max_score: 100.0
    lower_is_better: false
    parameters:
      averaging: macro
      task_type: multiclass
```

Namespaced IDs are used when source semantics are incomplete:

```yaml
metric_id: textddi.twosides.pr_auc
metric_kind: pr_auc
parameters:
  task_type: multilabel
  label_aggregation: not_reported
```

### 10.7 `results.csv`

One row per paper table metric cell:

```text
study_id
source_snapshot_id
table_id
page
dataset_id
protocol_id
condition_id
method_id
metric_key
score
score_unit
reported_text
uncertainty_type
uncertainty_value
aggregation_count
aggregation_unit
row_label
column_label
result_provenance
notes
```

Example:

```csv
textddi,textddi-emnlp2023-final,table-2,6,textddi-drugbank,chronological-unseen-drug,zero-shot,textddi,textddi-drugbank-macro-f1,52.5,percent,52.5±0.7,standard_deviation,0.7,5,random_seeds,TextDDI,F1-Score,paper_experiment,
```

The adapter does not parse values out of `reported_text` as its primary path. `score` and uncertainty fields are audited numeric transcriptions; `reported_text` is retained for traceability and checked for consistency.

---


---

[Previous](03-7-selected-source-tables.md) · [Design index](../DESIGN.md) · [Next](05-11-inclusion-and-exclusion-rules.md)
