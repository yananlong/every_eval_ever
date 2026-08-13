# Adversarial Review of the Canonical Experiment Pack and Implementation

**Review date:** 2026-08-07  
**Reviewed target:** `every_eval_ever/adapters/drug_interaction_papers/` implementation and canonical experiment pack  
**Review class:** Self-review with external primary-source verification; not materially independent

## Bounded verdict

The implementation is structurally coherent, executable, fail-closed under the tested controls, and suitable for an exploratory adapter branch. It is **not authorized for a datastore submission or evidence promotion** until a second reviewer independently verifies the primary-source cells. Technical blocks B1–B5 pass; scientific/release gates G1 and G5 remain blocked by design.

## Claim ledger and patched findings

| Severity | Claim or control challenged | Adversarial finding | Patch applied |
| --- | --- | --- | --- |
| High | “Source provenance timestamps are deterministic.” | The first implementation copied publication dates into `retrieved_timestamp`, conflating when a paper appeared with when the EEE extraction was frozen. | Replaced every manifest value with the common extraction timestamp `1786041600`, retained publication dates separately, and added regression and B1 checks. |
| High | “Canonical experiment pack produces declared audit artifacts.” | The first draft bound B2 and B4 to `pytest` commands that did not write their declared JSON artifacts; B3/B5 referenced unsupported adapter flags. Field presence created a false execution contract. | Added `audit.py` with executable B1–B5 commands, changed every `run-blocks.json` entrypoint, and aligned `execution-bridge.md`. |
| High | “Source freeze is confirmatory.” | Bundle hashes and anchors were generated and reviewed in the same session. Calling them confirmatory would substitute self-consistency for independent verification. | Downgraded current claim/block evidence to `exploratory`, added requested-evidence fields and an independence statement, and blocked G1/G5 until a separate reviewer records completion. |
| High | “LLMDDI represents the published study.” | The arXiv and later journal report differ numerically. A generic study ID could silently launder preprint values as final-journal results. | Named the snapshot `llmddi-arxiv-2502.06890-v1`, attached a version warning to every log, and prohibited cross-version mixing. |
| High | “ZeroDDI metric IDs preserve the paper definition.” | The first mapping called `Pu`/`Ps` binary proportions, but the paper defines them as top-1 multiclass accuracy divided by correct seen/unseen binary accuracy. | Renamed them to source-scoped conditional-accuracy ratios, recorded numerator/denominator parameters, and corrected raw source-column labels to `Pu`/`Ps`. |
| High | “Typed uncertainty accurately represents reported variation.” | EEE’s `standard_deviation` field is described for per-sample scores, while TextDDI and ExDDI report across seeds/folds. Populating it would be schema-valid but semantically wrong. | Preserved standard deviations in `score_details.details` with an explicit repeated-run/fold basis; left typed uncertainty unset. |
| High | “Atomic replacement preserves prior output.” | Staging before replacement does not by itself cover a failure after the first collection is installed. | Added rollback bookkeeping and an injected post-install failure control that restores the prior collection and removes partial new collections. |
| Medium | “Method provenance distinguishes proposal, ablation, and external baseline.” | ZeroDDI1/2 were initially assigned to the external-baseline namespace even though the paper describes them as variants of the authors’ method. | Reclassified both as first-party ablations with author-scoped IDs; kept compatibility-loss baselines external. |
| Medium | “Transductive/inductive labels are comparable.” | The studies operationalize novelty along different axes. A Boolean would create false comparability. | Protocol IDs encode chronological unseen drugs, unseen relations, one/two unseen drugs, warm/cold drug/cold protein, and uncontrolled random-pair overlap. |
| Medium | “All model IDs can be canonicalized.” | Paper labels often omit exact release, instruction status, or provider endpoint. Global resolution would risk silent misattribution. | Unverified labels use source-scoped IDs; ambiguous IDs are rejected. Identity status is emitted in every log. |
| Medium | “Baseline evaluator relationship is known.” | Some table values are copied from earlier papers rather than rerun. Treating all as third-party evaluations by the current authors overstates provenance. | Result origin is per cell; known prior-paper rows use `evaluator_relationship=other`, and the uncertainty is disclosed. |
| Medium | “Source bundle declarations are safe and complete.” | Free-form catalog paths, mismatched source pages, unconstrained repository revisions, and inconsistent independent-review labels could pass superficial validation. | Added safe relative-path and slug validation, exact Git-SHA validation, table-page/origin checks, cross-snapshot collection uniqueness, and mandatory reviewer metadata for independent promotion. |
| Medium | “No DrugBank content is redistributed.” | Aggregate tables are safe only if source bundles and generated records are scanned for identifiers, sequences, and raw fields. | Added aggregate-only schemas and leakage scans in B2 and B5; source data uses `source_type=other` for DrugBank-derived corpora. |
| Medium | “Deterministic output means identical file paths.” | EEE’s helper intentionally writes UUIDv4 filenames. Comparing filenames would falsely fail deterministic semantics or encourage noncanonical filenames. | Determinism is evaluated by stable `evaluation_id` and normalized semantic JSON, while UUIDv4 path conventions remain intact. |
| Medium | “The implementation follows the branch’s adapter convention.” | The narrative design targeted the legacy `utils/` layout, while the current branch runs adapters from `every_eval_ever.adapters`. Source YAML/CSV/JSON would also be omitted from built wheels under the existing package-data patterns. | Moved the implementation and canonical plan under `every_eval_ever/adapters/drug_interaction_papers/`, updated all commands, documented the adapter, and extended package data for YAML/CSV/JSON. |
| Medium | “The module entrypoint is clean and repeatable.” | Eager imports from the package `__init__` loaded `adapter.py` before `python -m ...adapter`, producing a runpy warning and weakening warning-as-error smoke tests. | Removed eager re-exports from `__init__.py` and added a fresh-process regression test with `RuntimeWarning` promoted to an error. |
| Medium | “Audit evidence is deterministic.” | B4 retained random `TemporaryDirectory` paths inside expected error messages, so two scientifically identical audit runs produced byte-different evidence. | Redacted the per-run temporary root to `<TMP>` before recording failures and added a repeated-run equality test. |
| Low | “Current schema mapping follows the original design.” | The original narrative put source data at log level, but the current schema attaches it per `EvaluationResult`. | Implementation uses current `EvaluationResult.source_data`; the old split narrative is replaced by this canonical pack. |

## Negative-control coverage

The executed controls mutate bundle bytes, insert duplicate logical cells while refreshing the bundle digest, apply unknown filters, target occupied output without replacement, and inject failure after the first collection installation. Each control must exit through an exception, retain its failure reason, and preserve prior output. These controls establish tested behavior only; they do not prove immunity to every filesystem or process interruption.

## Remaining unresolved issues

1. A materially separate reviewer has not checked the full 548-cell transcription.
2. Source PDF SHA-256 values are not recorded because raw PDF bytes were not available to the execution runtime; repository bundle hashes are not substitutes.
3. The LLMDDI final-journal snapshot is deferred, not reconstructed.
4. Baseline provenance outside explicit paper footnotes remains conservatively classified and should be reviewed.
5. Local validation used a branch-compatible assembled runtime; upstream CI against a normal checkout remains required.

## Route decision

Proceed with committing the canonical plan, source bundles, adapter, and tests to the fork branch. Do not open the upstream PR or create datastore records as a release artifact until actual-repository CI passes and G1 is independently reviewed.
