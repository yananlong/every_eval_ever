<!-- Part 7 of 11. Previous: 06-13-metric-mapping.md. Next: 08-18-conversion-algorithm.md. -->

## 16. EEE record mapping

### 16.1 Log grain

One `EvaluationLog` per:

```text
source snapshot × study × dataset × method × condition
```

A log may contain several protocols and metrics, but only one dataset collection and one evaluator-relationship classification.

Examples:

- TextDDI × DrugBank × TextDDI × zero-shot: one log with three metrics for the chronological unseen-drug protocol;
- ExDDI × DDInter-explanation corpus × ExDDI-MTS: one log with three protocols × four metrics;
- DTI-LM × BindingDB × DTI-LM × balanced: one log with warm/cold-drug/cold-protein × AUROC/AUPRC;
- LLMDDI × DrugBank × GPT-4o-reported × fine-tuned: one log with four metrics.

Separating datasets avoids logs whose filesystem collection and `source_data` disagree.

### 16.2 Datastore collection slugs

```text
data/llmddi-drugbank/
data/textddi-drugbank/
data/textddi-twosides/
data/zeroddi-drugbank/
data/exddi-drugbank/
data/exddi-ddinter/
data/dti-lm-drugbank/
data/dti-lm-bindingdb/
```

The ExDDI directory names remain concise, but `source_data.dataset_name` carries the paired-corpus qualification.

### 16.3 `evaluation_name`

Pattern:

```text
<study>.<dataset>.<task>.<protocol>[.<condition>]
```

Examples:

```text
textddi.drugbank.ddi-event-multiclass.chronological-unseen-drug
textddi.twosides.ddi-event-multilabel.vanilla-known-drug
zeroddi.drugbank.ddi-event.unseen-relation-czsl
exddi.ddinter.ddi-explanation.one-unseen-drug
dti-lm.bindingdb.dti-binary.cold-protein.balanced-1-to-1
llmddi.drugbank.ddi-binary.random-pair-stratified.fine-tuned
```

Condition is included when it changes training/adaptation or sampling and therefore changes comparability.

### 16.4 `evaluation_result_id`

Pattern:

```text
<evaluation_name>/<metric_id>
```

Sanitize path-unsafe characters but preserve semantic uniqueness.

### 16.5 `evaluation_id`

Pattern:

```text
paper-results/<source_snapshot_id>/<dataset_id>/<method_id>/<condition_id>
```

This identifier is stable across regeneration and does not depend on wall-clock time or UUID filenames.

### 16.6 Timestamps

- `retrieved_timestamp`: immutable snapshot creation time from `manifest.yaml`;
- `evaluation_timestamp`: `null` unless the paper or repository establishes when the evaluation was run;
- publication date belongs in `source_metadata.additional_details`, not `evaluation_timestamp`.

### 16.7 Source metadata

```text
source_name: exact paper title plus source snapshot
source_type: documentation
source_organization_name: stable paper-author group label, e.g. “TextDDI paper authors”
source_organization_url: final paper landing page
```

Additional details include:

- DOI/persistent identifier;
- venue;
- publication date;
- source snapshot ID;
- PDF hash;
- repository and commit;
- table IDs;
- source provider kind `paper_authors`;
- result provenance.

The publisher is not represented as the evaluator.

### 16.8 Eval library

Use:

```text
name: unknown
version: unknown
```

unless the source explicitly identifies an evaluation library. Custom training scripts, hosting platforms, and model APIs are not mislabeled as evaluation libraries. Repository and execution details go in `additional_details`.

### 16.9 Model information

Required additional details:

```text
raw_method_label
method_category
identity_status
source_snapshot_id
paper_owned
backbone_if_reported
parameter_count_if_reported
exact_release_not_reported
original_method_citation
implementation_evidence
```

All values are serialized as strings as required by EEE.

### 16.10 Source data details

Required protocol-linked details:

```text
dataset_id
dataset_version
study_specific_variant
raw_source_name
task_output_type
protocol_id
paper_protocol_label
drug_entity_overlap
target_entity_overlap
relation_class_overlap
pair_overlap
temporal_ordering
candidate_label_space
negative_sampling
train_split_description
test_split_description
preprocessing_summary
```

### 16.11 Score details

Required details:

```text
reported_text
reported_unit
source_table
source_page
source_row_label
source_column_label
aggregation_count
aggregation_unit
result_provenance
```

Typed uncertainty is added separately when justified.

### 16.12 Generation configuration

Populate only for evaluated systems where relevant parameters are explicitly reported.

- LLMDDI: adaptation regime, prompt setting, and reported generation parameters where available;
- ExDDI-IC: GPT-3.5 release and in-context demonstration count where established;
- ExDDI fine-tuned models: beam size and relevant decoding settings where they directly define evaluation output;
- non-generative baselines: omit.

Do not duplicate generic protocol metadata into `GenerationConfig`.

---

## 17. Adapter API and CLI

### 17.1 Public pure functions

```python
load_catalog(path) -> Catalog
validate_catalog(catalog) -> ValidationReport
select_rows(catalog, filters) -> list[SourceResult]
build_logs(rows, catalog) -> list[LogBundle]
validate_logs(logs) -> ValidationReport
write_logs(logs, output_dir, replace=False) -> list[Path]
```

Pure construction functions allow complete offline testing.

### 17.2 CLI

```bash
uv run python -m utils.drug_interaction_papers.adapter \
  --output-dir /tmp/eee-drug-interaction-papers
```

Filters:

```bash
--study textddi
--dataset textddi-twosides
--protocol chronological-unseen-drug
--condition zero-shot
--method textddi
```

Operational options:

```text
--list
--verify-only
--replace
--output-dir PATH
```

Defaults:

- all enabled source snapshots;
- no network access;
- refuse a non-empty adapter-owned output collection unless `--replace` is supplied;
- no silent exclusions.

### 17.3 Filter semantics

Filters select complete log groups. A filter may not emit only some metrics from a selected table row unless a dedicated metric filter is explicitly added later. This prevents accidental partial benchmark records.

---


---

[Previous](06-13-metric-mapping.md) · [Design index](../DESIGN.md) · [Next](08-18-conversion-algorithm.md)
