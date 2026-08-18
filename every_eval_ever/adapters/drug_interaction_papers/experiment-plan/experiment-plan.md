# Experiment Plan

## Context

- **Problem:** Convert a narrative adapter design into a falsifiable, execution-bound plan and implement a paper-results adapter without changing EEE core schema or registry architecture.
- **Evaluation goal:** Decide whether the implementation is sufficiently source-faithful, semantically explicit, deterministic, and fail-closed to support an upstream adapter PR and a later data-only datastore PR.
- **Operating mode:** Standalone tracked experiment pack embedded in `every_eval_ever/adapters/drug_interaction_papers/experiment-plan/`.
- **Upstream artifacts used:** The superseded narrative design, current EEE schema/helpers at the branch tip, five primary papers and supplements, pinned author repositories, and earlier adversarial-review findings.
- **Main constraints:** Current EEE schema only; aggregate results; no raw DrugBank redistribution; no runtime network; no dependency on Papers With Code or `eval-card-registry`; no PR opened in this stage.
- **Dominant contribution:** A source-bundle-driven adapter that preserves 548 paper-table result cells in 99 logs across eight study-dataset collections, with explicit generalization protocols.
- **Critical reviewer concern:** Schema-valid records may still be scientifically wrong through source mixing, selective extraction, model misattribution, protocol conflation, metric-scale errors, or partial publication.
- **Current evidence class:** Implemented and self-audited exploratory evidence; no independent promotion.
- **Requested evidence class:** Confirmatory software-and-data mapping evidence after independent source-cell review; never scientific replication of the original models.
- **Outcome-informed selection history:** Study and table scope was selected before implementation tests. Directly comparable baseline rows are retained. Non-selected tables are documented rather than silently discarded.
- **Material predecessor failures:** Planning counts lacked machine-readable source authority; EEE schema changed after the first design; LLMDDI preprint/final values diverge; hashes were previously described too strongly.

## Claim Map

| Claim ID | Type | Why it matters | Minimum convincing evidence | Anti-claim to rule out | Falsifier | Decision if unproven |
| --- | --- | --- | --- | --- | --- | --- |
| C1 | Primary | Prevent plausible-looking but scientifically misattributed datastore records. | Source-lock audit, semantic invariant audit, exact full conversion, schema validation, and negative controls. | Schema validity alone is sufficient. | Any verified cell is omitted, duplicated, mixed, rescaled, or mapped to the wrong method/dataset/protocol/metric. | Drop affected rows or the adapter release. |
| C2 | Supporting | Prevent partial or non-reproducible datastore publication and licensed-content leakage. | Deterministic rerun comparison, atomicity matrix, failure accounting, leakage scan, and release audit. | Warnings plus partial valid output are adequate. | Any injected failure publishes partial output, changes prior output, exits cleanly, or leaks raw DrugBank content. | Defer publication until corrected. |

## Experimental Storyline

| Block | Role | Paper placement | Why it exists |
| --- | --- | --- | --- |
| B1 | Main anchor: source freeze | Main | Establish the admissible evidence and exact result-cell universe. |
| B2 | Novelty/semantic isolation | Main | Show that the adapter preserves distinct protocols, metrics, identities, and dataset variants. |
| B3 | End-to-end anchor | Main | Demonstrate complete current-schema conversion and logical determinism. |
| B4 | Negative controls | Appendix | Prove fail-closed atomic behavior under malformed inputs and I/O failures. |
| B5 | Release readiness | Appendix | Check datastore routing, collisions, provenance, and leakage before a later data PR. |

## Non-Vacuity Preflight

- **Discriminating case:** TextDDI DrugBank and TWOSIDES share a study but differ in task output and decisive metrics; ZeroDDI CZSL/GZSL differ in candidate label space; DTI-LM cold-drug/cold-protein differ in overlap axis. A conflated implementation produces observably different audit outcomes.
- **Plausible comparator win:** A simpler table-to-JSON converter can produce more files or pass basic Pydantic validation, so the robust adapter does not win by construction; it must satisfy stricter source, semantic, determinism, and failure gates.
- **Complete loss or outcome contract:** Count wrong acceptances, wrong rejections, omissions, duplicates, silent skips, malformed uncertainty, unresolved identities, source/version mismatches, validation failures, empty selections, retries, write failures, partial files, stale files, and leakage findings.
- **Case-selection independence:** Table scope and negative-control classes are frozen before implementation results; outcome-based removal requires explicit plan amendment and evidence reclassification.
- **Skip, failure, null, and retry accounting:** Every selected row ends as converted, declared excluded, or failed with source reference. Commands retain nonzero exit, failure report, and prior-output digests.
- **Gate result:** Technical non-vacuity preflight passes. Evidence remains exploratory because implementation, transcription, and review were performed in one session; release promotion is blocked pending independent primary-source verification.

## Experiment Blocks

### B1 — Source freeze and transcription audit

- **Claim tested:** C1
- **Purpose:** Validate source bundles, exact counts, foreign keys, version isolation, and anchor cells before conversion.
- **Priority:** must-run
- **Gate:** G1
- **Output:** `experiment-plan/evidence/B1-source-audit.json`

### B2 — Protocol, metric, identity, and licensing audit

- **Claim tested:** C1
- **Purpose:** Reject schema-valid semantic conflation and unsupported identity resolution.
- **Priority:** must-run
- **Gate:** G2
- **Output:** `experiment-plan/evidence/B2-semantic-audit.json`

### B3 — Full conversion, schema validation, and deterministic replay

- **Claims tested:** C1, C2
- **Purpose:** Convert all enabled snapshots twice and compare exact coverage and normalized semantic output.
- **Priority:** must-run
- **Gate:** G3
- **Output:** `experiment-plan/evidence/B3-conversion-audit.json`

### B4 — Fail-closed and atomicity negative controls

- **Claim tested:** C2
- **Purpose:** Inject source, filter, identity, validation, and write failures and prove no partial publication.
- **Priority:** must-run
- **Gate:** G4
- **Output:** `experiment-plan/evidence/B4-negative-control-audit.json`

### B5 — Datastore release dry run

- **Claim tested:** C2
- **Purpose:** Audit output routing, logical collisions, provenance completeness, and licensed-content leakage.
- **Priority:** must-run
- **Gate:** G5
- **Output:** `experiment-plan/evidence/B5-release-audit.json`

Detailed machine-readable block contracts are authoritative in `run-blocks.json`.

## Run Order

| Order | Block | Purpose | Dependency | Gate ID | Stop / go gate | Est. cost |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | B1 | Freeze and audit source universe | None | G1 | Stop on any unexplained source discrepancy | Seconds + human anchor review |
| 2 | B2 | Audit semantic mapping | B1 | G2 | Stop on any unsupported mapping or leakage finding | Seconds |
| 3 | B3 | Full conversion and replay | B1, B2 | G3 | Stop on any count, schema, identity, or semantic-diff failure | Under one minute |
| 4 | B4 | Failure and atomicity matrix | B3 | G4 | Stop on any clean partial export or prior-output mutation | Seconds |
| 5 | B5 | Release dry run | B3, B4 | G5 | Authorize later PR work only with zero release-blocking findings | Seconds to minutes |

## Decision Gates

See `decision-gates.md`. Technical completion does not imply a passing scientific or release gate.

## Risks and Confounds

- **Source-version drift:** Freeze snapshot IDs and repository commits, record paper hashes when obtainable, and prohibit silent replacement. Repository revisions are supplementary context rather than score authority.
- **Transcription self-confirmation:** Separate machine validation from human anchor review and label single-review evidence honestly.
- **Schema validity mistaken for semantic validity:** B2 is a separate mandatory gate.
- **Outcome-shaped scope:** Preserve declared exclusions and selection history; changes after score inspection trigger reclassification.
- **Model identity overreach:** Ambiguous releases receive source-scoped IDs.
- **Metric comparability overreach:** Preserve paper-native units and aggregation parameters; namespace underspecified metrics. In particular, ZeroDDI `Pu` and `Ps` are conditional accuracy ratios, not binary accuracies.
- **Licensed-content leakage:** Commit only aggregate metrics and high-level protocol metadata; scan for forbidden raw fields and identifiers.
- **Atomicity gaps:** Stage and validate all outputs before replacing any adapter-owned destination.
- **Correlated review:** This execution remains self-review unless a second reviewer independently checks source cells and semantics.

## Implementation outcome

The adapter, source bundles, offline tests, and five executable audit blocks are implemented on this branch. Technical audits pass for 548 results and 99 logs. Gate G5 remains blocked because `anchors.yaml` records a single-review primary-source check and `independent_review_complete: false`. Generated datastore records are not committed and no data or upstream PR is authorized by this self-review.
