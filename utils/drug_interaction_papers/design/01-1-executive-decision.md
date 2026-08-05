<!-- Part 1 of 11. Previous: ../DESIGN.md. Next: 02-5-terminology.md. -->

## 1. Executive decision

Implement one offline, source-bundle-driven adapter for selected paper-reported drug-interaction evaluations:

```text
utils/drug_interaction_papers/
```

The adapter will ingest audited, checked-in transcriptions of primary paper tables and convert them into schema-valid aggregate `EvaluationLog` records. It will not scrape PDFs at runtime, download DrugBank data, rerun experiments, import the Papers With Code adapter, call the entity registry, or modify the EEE schema.

The first release covers five studies and eight study–dataset collections:

1. LLMDDI × DrugBank
2. TextDDI × DrugBank
3. TextDDI × TWOSIDES
4. ZeroDDI × DrugBank
5. ExDDI × paired DrugBank-explanation corpus
6. ExDDI × paired DDInter-explanation corpus
7. DTI-LM × DrugBank
8. DTI-LM × BindingDB

The datastore submission remains a separate, generated-data PR.

### Core design choices

- **Paper tables are the authority.** Author repositories corroborate identity, preprocessing, and source version. Papers With Code is discovery metadata only.
- **The adapter is broader than “LLM-only.”** It is for language-model-centered drug-interaction papers and includes all directly comparable rows in each selected table, including non-LM baselines. This avoids selective extraction of favorable rows.
- **Protocol identity is explicit.** “Transductive,” “zero-shot,” “cold start,” and “inductive” are not treated as interchangeable binary flags.
- **Reported scales are preserved.** The adapter does not infer or rescale scores heuristically.
- **No raw DrugBank content is redistributed.** Only aggregate paper-reported metrics and high-level dataset/protocol metadata are stored.
- **Source versions are immutable.** A table may not combine values from a preprint, final paper, repository output, or later abstract unless they are represented as separate source snapshots.
- **Failures are atomic.** Source validation and log construction complete before any output is replaced.

---

## 2. Motivation and bounded contribution

EEE can represent aggregate evaluation results without a schema extension, but the source papers use materially different evaluation contracts:

- random drug-pair sampling with uncontrolled entity overlap;
- chronological unseen-drug testing;
- known-drug “vanilla” testing;
- unseen DDI relation classes under conventional and generalized zero-shot learning;
- one-unseen-drug and two-unseen-drug explanation generation;
- warm, cold-drug, and cold-protein DTI prediction;
- balanced and 1:10 negative-sampling conditions.

A useful adapter must preserve those distinctions within the existing EEE fields. The design therefore uses stable `evaluation_name` identifiers plus a structured, checked-in protocol catalog whose fields are copied into `source_data.additional_details`.

This PR is intentionally not an ontology or schema overhaul. It establishes a reliable source-to-EEE conversion for a bounded corpus.

---

## 3. Goals

### 3.1 Functional goals

1. Convert the selected paper tables into EEE aggregate records without network access.
2. Preserve exact table provenance down to paper version, table, page, row label, and column label.
3. Preserve dataset version, preprocessing, task output type, split construction, novelty axis, and evaluation condition.
4. Represent explicitly reported uncertainty using EEE’s typed uncertainty fields.
5. Emit stable logical identifiers and prevent silent duplicate or partial exports.
6. Support complete export and filtered development/smoke exports.
7. Generate the eight intended datastore collections from the same source bundle.

### 3.2 Scientific-integrity goals

1. Avoid conflating unseen drugs with unseen relation classes.
2. Avoid calling a random pair split “transductive” unless the source establishes entity overlap.
3. Avoid treating a database name as a complete benchmark identity.
4. Avoid presenting PLM, chemical-LM, protein-LM, and general-purpose generative LLM systems as one homogeneous model class.
5. Avoid selective extraction of only proposed methods or only language-model rows from comparison tables.
6. Avoid asserting metric aggregation details that the source does not report.
7. Avoid false model canonicalization when the exact model release is not stated.

---

## 4. Non-goals

The first adapter PR will not:

- alter `eval.schema.json`, generated Pydantic models, validators, or core EEE helpers;
- add a first-class protocol object to EEE;
- modify `eval-card-registry`;
- depend on or extend `utils/paperswithcode`;
- ingest raw DrugBank records, drug descriptions, drug-pair labels, or split membership;
- run model inference or training;
- export instance-level samples;
- scrape or OCR papers at adapter runtime;
- infer scores from plots;
- normalize all metrics to a single numeric scale;
- claim that every included method is an LLM;
- cover every result or ablation in the five papers;
- cover the separate 2025 DDI-JUDGE or 2026 DDI-LLM literature.

---


---

[Previous](../DESIGN.md) · [Design index](../DESIGN.md) · [Next](02-5-terminology.md)
