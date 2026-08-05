<!-- Part 10 of 11. Previous: 09-22-adapter-readme-requirements.md. Next: 11-adversarial-verdict.md. -->

## 27. Pre-implementation blockers

### Blocker A — LLMDDI final source reconciliation

Acquire and hash the final 2026 paper, identify the final numerical zero-shot/fine-tuning tables, and cross-check them against `gadevito/LLMDDI` at a pinned commit. Decide whether the final article’s main DrugBank results supersede or reorganize the preprint tables.

**Resolution condition:** one internally consistent final source bundle with no mixed preprint values.

### Blocker B — baseline result provenance

For each external baseline in TextDDI, ZeroDDI, and DTI-LM, classify whether the current paper reran the method or copied a published number.

**Resolution condition:** every method row has `result_provenance` and a justified evaluator relationship.

### Blocker C — source-file hashes and commit locks

Download the final paper/supplement bytes and pin author repositories to full commit SHAs.

**Resolution condition:** all manifests pass immutable-source validation.

These blockers do not require EEE architectural changes.

---

# Appendix A. Adversarial review and incorporated patches

The first draft was stress-tested for correctness, selection bias, hidden assumptions, specification gaming, provenance, legal risk, and failure behavior. The following issues were patched into the design above.

| Severity | Draft issue | Failure mode | Patch incorporated |
|---|---|---|---|
| Critical | Mixed LLMDDI preprint and journal values were possible | A record could cite the final paper while containing stale preprint numbers | Added immutable source snapshots and a merge-blocking final-version reconciliation gate |
| Critical | DrugBank was treated like a redistributable benchmark | Adapter could accidentally package restricted raw data or imply public availability | Aggregate-only rule; `SourceDataPrivate`; explicit leakage/licensing tests |
| High | “LLM adapter” framing misclassified PLMs and baselines | Taxonomic error and misleading PR claim | Renamed adapter to `drug_interaction_papers`; added method categories and precise corpus label |
| High | Only LM/proposed rows might be extracted | Outcome-aware selection and loss of comparison context | Include all directly comparable rows in selected tables; exclude only declared non-result/relative rows |
| High | Generalization was represented as transductive/inductive Boolean | Unseen drugs, unseen classes, and cold proteins could be conflated | Added multidimensional protocol schema and semantic protocol IDs |
| High | LLMDDI random split was called transductive | Stronger entity-overlap claim than source supports | Renamed to `random-pair-stratified`; entity novelty `uncontrolled` |
| High | TextDDI vanilla was treated as formally entity-transductive | “Known drugs” and evenly distributed drugs do not prove every detailed overlap property | Retained paper-native `vanilla-known-drug`; no stronger derived guarantee |
| High | ExDDI datasets were named simply DrugBank and DDInter | Concealed that pair sets were intersected and explanation supervision differed | Renamed to paired ExDDI corpora with explicit construction metadata |
| High | BindingDB was represented as generic binary DTI | Lost Kd thresholds, exclusion band, averaging, and sequence filters | Added exact code-defined preprocessing contract and pinned code commit requirement |
| High | Paper main table means discarded available uncertainty | Underrepresented experimental variation | Selected ExDDI Appendix A2; typed SD for 5-fold models; no SD for one-run IC |
| High | Scores could be normalized heuristically | Silent scale changes and incorrect bounds | Preserve reported scale; declarative units/bounds; no observed-range inference |
| High | Ambiguous model names could be over-canonicalized | Silent misattribution to exact API/HF releases | Source-scoped IDs for ambiguous releases; exact global IDs require evidence |
| High | External baselines could be attributed to paper authors | Incorrect developer and evaluator provenance | Explicit method mappings, result provenance, and evaluator-relationship derivation |
| High | Multiple datasets could be grouped into one filesystem collection/log | Folder identity and `source_data` could disagree | One log per dataset; eight explicit collection slugs |
| Medium | Publication date could be used as evaluation date | False timestamp claim | `evaluation_timestamp=null` unless run date is established; publication date stays in source metadata |
| Medium | Repetition count could be converted into invented SD | False quantitative uncertainty | Typed uncertainty only when numerically reported; repetition count stored separately |
| Medium | Metric aliases implied unreported aggregation | False comparability, especially TWOSIDES and BLEU | Namespaced metric IDs when aggregation/version is incomplete |
| Medium | TextDDI kappa was given a nonnegative percentage bound | Negative kappa values would be invalid | Set reported percentage-point kappa bounds to `[-100, 100]` |
| Medium | Runtime PDF parsing was considered | Fragile extraction, network dependence, OCR error | Checked-in audited long-form source bundles; no runtime scraping/OCR |
| Medium | Conversion could delete old output before failing | Partial or destructive refresh | Two-phase build/validate/write and delayed atomic replacement |
| Medium | UUID filename churn was confused with logical instability | Unnecessary core-helper changes or duplicate accumulation | Stable semantic `evaluation_id`; explicit replace semantics; UUID helper unchanged |
| Medium | Source checksum was treated as proof of correctness | Immutable transcription errors could still pass | Added second verification pass, anchor cells, count checks, and explicit verification status |
| Medium | Empty filters or malformed rows could silently skip data | Clean exit with incomplete export | Fail closed, no silent skips, exact coverage report, nonzero exit |
| Low | Registry/PwC work could become a hidden merge dependency | Scope and sequencing risk | Explicitly prohibited imports/runtime dependencies; future registry work out of scope |


---

[Previous](09-22-adapter-readme-requirements.md) · [Design index](../DESIGN.md) · [Next](11-adversarial-verdict.md)
