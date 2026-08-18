# Adversarial Review of the Drug-Interaction Paper Adapter

**Review date:** 2026-08-18  
**Reviewed target:** `every_eval_ever/adapters/drug_interaction_papers/` implementation, frozen aggregate source bundles, tests, and audit pack  
**Review class:** Self-review with external primary-source verification; not materially independent

## Bounded verdict

The adapter is structurally coherent, executable, fail-closed under the tested controls, and suitable for an upstream **code review** while registered as `runnable=False`. The code PR does not publish datastore records and does not require the source corpus to be promoted beyond exploratory/self-reviewed status.

The generated corpus is **not authorized for datastore submission or scheduled publication** until a materially separate reviewer verifies the selected primary-source cells. Technical blocks B1–B5 pass; scientific/release gates G1 and G5 remain blocked by design.

The generic Papers with Code adapter is separate upstream work (PR #209 when this review was refreshed). This branch deliberately does not carry or fork that adapter.

## Claim ledger and resolved findings

| Severity | Claim or control challenged | Adversarial finding | Resolution |
| --- | --- | --- | --- |
| High | Source provenance timestamps are deterministic. | Publication dates had initially been conflated with extraction time. | All manifests use the common extraction timestamp `1786041600`; publication dates remain separate. |
| High | Audit blocks produce the artifacts they declare. | Earlier B2/B4 commands did not write their declared JSON and B3/B5 referenced unsupported flags. | `audit.py` now provides executable B1–B5 entry points and the run blocks match them. |
| High | Bundle hashes are independent verification. | Hashes and anchors were generated in the same development context as the transcription. | They are classified as internal-integrity evidence only; G1/G5 require a separate reviewer. |
| High | LLMDDI results represent one stable publication. | The arXiv and later journal reports differ numerically. | The source is explicitly pinned to `llmddi-arxiv-2502.06890-v1`; cross-version mixing is prohibited. |
| High | ZeroDDI `Pu`/`Ps` were ordinary binary proportions. | The source defines them as conditional top-1 multiclass-accuracy ratios. | Metrics are source-scoped conditional-accuracy ratios with numerator/denominator semantics recorded. |
| High | Repeated-run variation can use typed per-sample uncertainty. | TextDDI and ExDDI report variation across seeds/folds, not per-sample uncertainty. | Variation is preserved in `score_details.details`; typed uncertainty remains unset. |
| High | Replacement is atomic merely because output is staged. | Failure after the first installed collection could otherwise leave a partial replacement. | Rollback bookkeeping and injected post-install failure controls restore prior output. |
| Medium | Protocol labels are globally comparable. | The studies operationalize novelty along different axes. | Protocol IDs encode each paper-native split rather than collapsing them to a Boolean inductive/transductive field. |
| Medium | Every model label can be globally canonicalized. | Several paper labels lack enough release/provider information. | Unverified identities remain source-scoped; ambiguous identities fail closed. |
| Medium | All baseline rows share one evaluator relationship. | Some values are copied from earlier papers rather than rerun by the current authors. | Result origin is represented per cell and uncertain provenance is disclosed conservatively. |
| Medium | Aggregate-only packaging proves no DrugBank redistribution. | Raw identifiers or sequences could still leak through source bundles. | B2/B5 scan the package for DrugBank-style identifiers, long protein sequences, SMILES fields, and raw description fields. |
| Medium | Deterministic output means deterministic filenames. | Repository publication requires UUIDv4 filenames. | Determinism is defined over semantic records and logical evaluation IDs, not UUIDv4 path names. |
| Medium | Audit evidence is deterministic. | Temporary paths initially made B4 evidence byte-unstable. | Temporary roots are redacted to `<TMP>` and repeated-run equality is tested. |

## Negative-control coverage

The executed controls mutate source bytes, insert duplicate logical cells while refreshing the bundle digest, apply unknown filters, target occupied output without replacement, and inject failure after the first collection installation. Each control must fail, retain its failure reason, and preserve prior output. This establishes tested fail-closed behavior for those cases; it does not prove immunity to every filesystem or process interruption.

## Remaining limitations

1. A materially separate reviewer has not checked the full 548-cell transcription. This blocks datastore release and scheduling, not code review.
2. Source PDF SHA-256 values are not recorded because raw PDF bytes were unavailable to the original execution runtime; repository bundle hashes are not substitutes.
3. The LLMDDI final-journal snapshot is intentionally deferred rather than reconstructed or mixed with the pinned arXiv snapshot.
4. Baseline provenance outside explicit paper footnotes remains conservatively classified and should receive attention during independent source review.
5. The audit pack is self-review: the same development context designed the mapping and most checks. Green tests establish structural and behavioral properties, not independent scientific verification.

## Route decision

**Proceed with the upstream adapter code PR.** Keep the adapter registered as `runnable=False`, include no generated datastore records, and state the independent source-verification limitation explicitly in the PR body.

**Do not** submit or automatically publish generated records until G1 and G5 are independently satisfied. A later datastore submission should record the separate reviewer, the verified source-cell universe, and any corrections before promotion.
