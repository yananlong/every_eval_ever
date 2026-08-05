<!-- Part 8 of 11. Previous: 07-16-eee-record-mapping.md. Next: 09-22-adapter-readme-requirements.md. -->

## 18. Conversion algorithm

1. Load `catalog.yaml`.
2. Load all selected study bundles.
3. Validate each file against typed source models.
4. Validate foreign keys across methods, datasets, protocols, metrics, and results.
5. Validate source snapshot consistency.
6. Validate cell-key uniqueness.
7. Validate expected counts from each manifest.
8. Validate numeric bounds and reported-unit consistency.
9. Validate `reported_text` against numeric score/uncertainty where mechanically possible.
10. Apply CLI filters to complete log groups.
11. Group rows by source snapshot, dataset, method, and condition.
12. Derive evaluator relationship from method and result provenance.
13. Build all `EvaluationLog` objects in memory.
14. Validate all logs with current EEE Pydantic models.
15. Run cross-log duplicate checks for `evaluation_id` and `evaluation_result_id`.
16. Write to a temporary output tree.
17. Re-read and validate written JSON.
18. If `--replace`, replace only the selected adapter-owned collection directories after all checks pass.
19. Print an exact coverage report and exit nonzero on any error.

No output is deleted or partially updated before step 18.

---

## 19. Failure policy

### Fatal

- missing source file;
- source hash mismatch;
- unrecognized source snapshot;
- duplicate cell key;
- unexpected or missing result count;
- unresolved method identity;
- unknown metric bounds/direction;
- score outside declared legal range;
- uncertainty type not established;
- result references missing method/dataset/protocol/metric;
- ambiguous table version;
- duplicate logical evaluation ID;
- EEE schema failure;
- write or re-read validation failure.

### Warning only

- exact public model release not reported, when a source-scoped ID is used;
- evaluation date unavailable;
- evaluation library unavailable;
- source provides repetitions but no numeric dispersion;
- baseline implementation details unavailable, if provenance is explicit.

Warnings are summarized and written to output metadata where relevant. They never silently alter values.

---

## 20. Output replacement and reproducibility

EEE’s helper allocates UUID filenames. Logical reproducibility therefore rests on stable `evaluation_id` values and byte-equivalent JSON content, not identical newly allocated filenames.

The adapter must:

- build into a temporary directory;
- refuse accidental accumulation by default;
- require `--replace` for regeneration of an existing collection;
- delete stale adapter-owned files only after successful validation;
- report added, removed, and retained logical evaluation IDs;
- never touch unrelated datastore collections.

A future stable-filename helper is outside this PR.

---

## 21. Test plan

### 21.1 Source schema tests

- every manifest validates;
- all source hashes and repository commits have valid formats;
- all foreign keys resolve;
- all `additional_details`-bound values are deterministically stringifiable;
- no duplicate source cell keys;
- no undeclared exclusions.

### 21.2 Completeness tests

Per study:

- exact method count;
- exact table cell count;
- exact protocol count;
- exact dataset count;
- exact log count;
- every selected table row represented;
- derived “relative improvement” or narrative rows absent.

The current planning baseline is 548 result cells and 99 logs, subject to the final LLMDDI source lock.

### 21.3 Anchor-cell tests

At least:

- two cells per table;
- one best-performing and one non-best row;
- one cell with uncertainty;
- one boundary or negative-capable metric where applicable;
- one cell per dataset/protocol combination.

Anchor tests assert score, uncertainty, scale, source locator, and method mapping.

### 21.4 Protocol tests

- LLMDDI entity novelty is `uncontrolled`, not transductive;
- TextDDI zero-shot uses disjoint chronological drug sets;
- TextDDI vanilla retains the paper-native known-drug label;
- ZeroDDI CZSL and GZSL have different candidate label spaces;
- ExDDI S2 maps to one unseen drug and S1 to two unseen drugs;
- DTI-LM cold-drug and cold-protein prohibit overlap on different entity axes;
- balance ratio is a condition, not conflated with protocol.

### 21.5 Metric tests

- no automatic percent/proportion rescaling;
- TextDDI kappa accepts negative percentage points;
- TextDDI DrugBank F1 is macro;
- TWOSIDES metrics remain namespaced when aggregation is not reported;
- ZeroDDI metrics carry class-subset and top-k semantics;
- ExDDI uncertainty comes from Table A2;
- DTI-LM means do not acquire invented SDs.

### 21.6 Identity tests

- all methods map explicitly;
- ambiguous LLM releases use source-scoped IDs;
- no source-scoped ID aliases itself to an unsupported global ID;
- external baselines are not attributed to the current paper’s authors;
- result provenance yields the expected evaluator relationship.

### 21.7 Licensing and leakage tests

- no raw DrugBank IDs, pair labels, descriptions, or source rows appear in committed source bundles or outputs;
- DrugBank-derived `source_data` uses `other`;
- TextDDI metadata records exclusion of the Drug Interaction text field as a leakage control;
- no instance-level sidecars are generated.

### 21.8 Error-path tests

- one malformed source row does not produce partial output;
- source count mismatch fails before writing;
- non-empty output without `--replace` fails;
- failed replacement leaves prior output intact;
- filter selecting nothing returns a nonzero user error;
- unknown filter value fails loudly.

### 21.9 End-to-end tests

- full offline conversion;
- every output validates with `EvaluationLog.model_validate`;
- every written file passes EEE validation;
- two builds have identical logical IDs and semantic JSON after ignoring UUID path names;
- generated collection paths match the eight declared slugs.

---


---

[Previous](07-16-eee-record-mapping.md) · [Design index](../DESIGN.md) · [Next](09-22-adapter-readme-requirements.md)
