<!-- Part 2 of 11. Previous: 01-1-executive-decision.md. Next: 03-7-selected-source-tables.md. -->

## 5. Terminology

### 5.1 Corpus label

Use:

> **Paper-reported evaluations of language-model-centered drug-interaction systems**

Do not label the complete corpus “LLM benchmarks.” TextDDI and ZeroDDI use pretrained biomedical/text encoders; DTI-LM uses chemical and protein sequence language models; ExDDI uses MolT5 and a ChatGPT prompting baseline; LLMDDI directly evaluates general-purpose LLMs.

### 5.2 Method categories

Each method has one of:

```text
general_purpose_generative_llm
text_encoder_plm
molecular_text_to_text_plm
chemical_sequence_lm_system
protein_sequence_lm_system
paper_defined_neural_method
retrieval_method
graph_or_kg_baseline
classical_ml_baseline
paper_ablation
```

The category is descriptive metadata; it does not affect score conversion.

### 5.3 Generalization dimensions

Do not reduce generalization to one Boolean. Protocol metadata must separately state:

```text
drug_entity_overlap
target_entity_overlap
relation_class_overlap
pair_overlap
temporal_ordering
candidate_label_space
negative_sampling
```

---

## 6. Source-of-truth policy

### 6.1 Authority order

For each result cell:

1. **Final published paper or official supplement**
2. **Author repository result artifact pinned to an exact commit**, when it clearly corresponds to the final paper
3. **Author preprint**, only as a separately named source version if the final table cannot be obtained
4. **Papers With Code**, for discovery or cross-reference only

A lower-priority source may corroborate a value but may not silently override a higher-priority source.

### 6.2 Version immutability

Every study source bundle has a `source_snapshot_id`, for example:

```text
textddi-emnlp2023-final
zeroddi-ijcai2024-final
exddi-aaai2025-final
qian-dtilm-bioinformatics2024-final
llmddi-kbs2026-final
```

The manifest records:

- title;
- authors;
- venue;
- DOI or persistent paper identifier;
- publication date;
- source file SHA-256;
- page count;
- selected tables;
- author repository and commit, if applicable;
- snapshot creation timestamp;
- extraction verifier status.

A corrected source creates a new snapshot ID. Existing source bundles are not edited in a way that changes their meaning without changing the snapshot ID.

### 6.3 LLMDDI version gate

LLMDDI changed between the 2025 arXiv preprint and the 2026 Knowledge-Based Systems publication. The final paper reports DrugBank 5.1.12 and updated headline values. Therefore:

- the adapter PR must use the final 2026 article and its pinned author repository results;
- preprint values must not be mixed into the final snapshot;
- if the final table cannot be fully reconstructed, LLMDDI is either deferred or emitted under a distinct `llmddi-arxiv2025-v1` snapshot;
- a preprint snapshot must not be presented as the final journal evaluation.

This is a merge-blocking source-reconciliation gate.

### 6.4 Source transcription verification

Each selected table is transcribed into long-form rows. Before merge:

1. a first extraction pass records all cells and locators;
2. a second pass rechecks every row/column against the primary table, preferably by a materially independent method or reviewer;
3. a programmatic count and key audit confirms expected completeness;
4. a set of anchor cells is checked against author-repository outputs where available.

If only one review path is available, the source manifest must state `verification_status: single_pass`; it must not claim independent verification.

---


---

[Previous](01-1-executive-decision.md) · [Design index](../DESIGN.md) · [Next](03-7-selected-source-tables.md)
