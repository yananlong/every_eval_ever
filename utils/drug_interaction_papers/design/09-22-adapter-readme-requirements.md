<!-- Part 9 of 11. Previous: 08-18-conversion-algorithm.md. Next: 10-27-pre-implementation-blockers.md. -->

## 22. Adapter README requirements

The README must include:

1. scope and terminology;
2. study/table matrix;
3. source-version policy;
4. statement that values are paper-reported aggregates, not reruns;
5. statement that the adapter includes directly comparable baselines;
6. licensing and aggregate-only restriction;
7. CLI examples;
8. source update procedure;
9. expected coverage report;
10. explanation of protocol IDs;
11. known limitations;
12. datastore generation and validation commands.

It must not market the records as clinically validated or suitable for medical decision-making.

---

## 23. PR decomposition

### 23.1 Adapter PR: `every_eval_ever`

Proposed title:

> Add paper-results adapter for language-model-centered drug-interaction evaluations

Files:

```text
utils/drug_interaction_papers/**
tests/test_drug_interaction_papers_adapter.py
utils/README.md
```

No generated datastore JSON.

PR description must include:

- selected source snapshots;
- counts by study/dataset;
- explicit non-goals;
- validation commands;
- source verification status;
- unresolved warnings;
- link to the companion datastore PR once opened.

### 23.2 Datastore PR

Proposed title:

> [Submission] Add paper-reported drug-interaction LM evaluations

Contents:

```text
data/llmddi-drugbank/**
data/textddi-drugbank/**
data/textddi-twosides/**
data/zeroddi-drugbank/**
data/exddi-drugbank/**
data/exddi-ddinter/**
data/dti-lm-drugbank/**
data/dti-lm-bindingdb/**
```

The PR records:

- adapter commit SHA;
- source snapshot IDs;
- file/log/result counts;
- validation output;
- confirmation that no raw licensed data are included.

### 23.3 Merge order

1. source bundles and adapter reviewed;
2. adapter PR merged;
3. datastore regenerated from the merged adapter commit;
4. datastore validation rerun;
5. datastore PR merged.

---

## 24. Relationship to Papers With Code and the registry

The adapter has no code or runtime dependency on the Papers With Code PR. That PR is still open and has its own schema/metric dependency chain. This adapter needs primary-paper protocol detail that the PwC task/dataset/metric rows do not carry.

Allowed conceptual reuse:

- aggregate `source_type=documentation`;
- raw-value preservation;
- fail-closed conversion;
- stable logical IDs;
- separate code and datastore PRs.

Prohibited dependency:

```text
utils.paperswithcode.adapter
utils.paperswithcode.registry_metrics
pgdumplib
PwC task or dataset slugs as source authority
```

The first PR also does not modify `eval-card-registry`. Namespaced IDs and explicit metadata make later registry work possible without blocking ingestion.

---

## 25. Security, privacy, legal, and clinical constraints

- No secrets or API keys are needed.
- Runtime is offline.
- No patient or personal data are ingested.
- No raw DrugBank content is redistributed.
- Public database URLs do not imply a verified open license; the adapter records source provenance but does not relicense source data.
- Outputs are research documentation, not clinical recommendations.
- The README and source metadata must not imply prospective clinical validity, safety, or regulatory approval.

---

## 26. Acceptance criteria

The adapter PR is ready for review when:

1. all five source snapshots are immutable and version-pinned;
2. LLMDDI final-paper reconciliation is complete or LLMDDI is explicitly deferred;
3. every included cell has exact table/page/row/column provenance;
4. every selected table passes a second verification pass;
5. all methods have non-guessing identities;
6. all dataset variants and protocols are explicit;
7. BindingDB threshold/preprocessing matches the pinned code;
8. ExDDI uses Appendix A2 uncertainty values;
9. no raw licensed DrugBank material is present;
10. conversion is offline and atomic;
11. all tests pass;
12. full output passes EEE validation;
13. coverage counts match manifests exactly;
14. code PR contains no generated datastore files;
15. datastore PR identifies the exact merged adapter commit.

---


---

[Previous](08-18-conversion-algorithm.md) · [Design index](../DESIGN.md) · [Next](10-27-pre-implementation-blockers.md)
