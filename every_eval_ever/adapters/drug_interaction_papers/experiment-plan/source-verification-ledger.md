# Source Verification Ledger

**Status:** Single-review primary-source check completed; independent review pending.  
**Authority:** Primary published paper or arXiv supplement first; author repository only as corroboration.  
**Promotion limit:** This ledger does not establish independent verification because the same agent assembled the bundles, ran the checks, and wrote this ledger.

| Snapshot | Selected source | Machine rows | Human anchors | Current status | Blocking issue |
| --- | --- | ---: | ---: | --- | --- |
| `llmddi-arxiv-2502.06890-v1` | arXiv Tables 3–4 | 92 | GPT-4o zero-shot F1 | Single-review verified | Later journal article reports revised values; this snapshot must remain explicitly arXiv-only. |
| `textddi-emnlp-2023` | EMNLP Tables 2 and 5 | 120 | TextDDI DrugBank zero-shot F1; TWOSIDES vanilla PR-AUC | Single-review verified | A second reviewer must check all transcribed rows and the known-drug wording. |
| `zeroddi-ijcai-2024` | IJCAI Table 1 | 120 | CZSL unseen average; GZSL harmonic average | Single-review verified | A second reviewer must verify the full table and the corrected Pu/Ps formulas. |
| `exddi-arxiv-2409.05592-v2` | Appendix Table A2 | 120 | DDInter two-unseen ROUGE-L | Single-review verified | ExDDI-IC is a single API run; no standard deviation is emitted. |
| `dti-lm-bioinformatics-2024` | Bioinformatics Tables 3–4 | 96 | BindingDB unbalanced cold-protein AUPRC | Single-review verified | DeepDTI rows are marked prior-paper results; other baseline provenance requires reviewer confirmation. |

## Evidence boundaries

- Bundle SHA-256 values detect changes to checked-in YAML and CSV files. They do not prove the transcription is correct.
- All five supplementary author repositories are pinned to 40-character Git commits, but the paper tables—not repository outputs—remain the score authority.
- The source freeze timestamp is `1786041600` (2026-08-06 18:40 UTC); publication dates are stored separately and are not reused as retrieval timestamps.
- `anchors.yaml` contains seven source-located spot checks. It is a guard against accidental drift, not a statistically meaningful independent sample.
- No raw DrugBank records, drug descriptions, identifiers, SMILES strings, or protein sequences were used as adapter source content.
- LLMDDI’s arXiv and 2026 journal values are treated as separate possible snapshots. Only the arXiv snapshot is implemented because complete final-journal tables were not available in an auditable primary form during this work.
- TextDDI standard deviations describe variation across five random seeds; ExDDI standard deviations describe five-fold cross-validation. They are retained in score details instead of being mislabeled as per-sample uncertainty.

## Independent review procedure

A second reviewer should select source cells without consulting generated EEE output, verify every selected table row against the primary PDF, confirm protocol wording and result provenance, and then update `sources/anchors.yaml` by setting `verification_status: independently_verified`, `independent_review_complete: true`, and the required reviewer, date, and notes fields. Any discrepancy must be corrected in the source bundle, followed by digest regeneration and a complete B1–B5 rerun.
