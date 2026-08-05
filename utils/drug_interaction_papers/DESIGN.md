# Design specification: `drug_interaction_papers` adapter for Every Eval Ever

**Status:** Proposed design; implementation not started  
**Target code repository:** `evaleval/every_eval_ever`  
**Target data repository:** `evaleval/EEE_datastore`  
**Adapter package:** `utils/drug_interaction_papers/`  
**Review state:** First draft completed, adversarially reviewed, and patched in place  
**Evidence class:** Design-ready, with explicit pre-implementation gates; not yet implementation-verified

---

## Document sections

The design is split into review-sized sections for repository storage. The sequence below is normative; all sections form one design specification.

- [1. Executive decision through 4. Non-goals](design/01-1-executive-decision.md)
- [5. Terminology through 6. Source-of-truth policy](design/02-5-terminology.md)
- [7. Selected source tables through 8. Scope matrix](design/03-7-selected-source-tables.md)
- [9. Repository layout through 10. Source bundle schemas](design/04-9-repository-layout.md)
- [11. Inclusion and exclusion rules through 12. Protocol catalog](design/05-11-inclusion-and-exclusion-rules.md)
- [13. Metric mapping through 15. Dataset identity and licensing](design/06-13-metric-mapping.md)
- [16. EEE record mapping through 17. Adapter API and CLI](design/07-16-eee-record-mapping.md)
- [18. Conversion algorithm through 21. Test plan](design/08-18-conversion-algorithm.md)
- [22. Adapter README requirements through 26. Acceptance criteria](design/09-22-adapter-readme-requirements.md)
- [27. Pre-implementation blockers](design/10-27-pre-implementation-blockers.md)
- [Adversarial verdict through EEE implementation references](design/11-adversarial-verdict.md)
