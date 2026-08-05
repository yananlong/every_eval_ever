<!-- Part 11 of 11. Previous: 10-27-pre-implementation-blockers.md. Next: ../DESIGN.md. -->

## Adversarial verdict

**Verdict:** structurally valid and implementation-ready after the three named source/provenance blockers are closed. The design supports an adapter PR without changing EEE, while preserving the scientific distinctions needed for the selected evaluations. It does not yet establish that the transcribed source corpus is independently verified; that assurance can be earned only during source-bundle construction and review.

---

# Appendix B. Reference inventory for implementation

## Primary papers

- De Vito, Ferrucci, and Angelakis. *LLMs For drug-Drug interaction prediction using textual drug descriptors*. Knowledge-Based Systems 338, 115486 (2026). DOI: 10.1016/j.knosys.2026.115486.
- Zhu et al. *Learning to Describe for Predicting Zero-shot Drug-Drug Interactions*. EMNLP 2023. DOI: 10.18653/v1/2023.emnlp-main.918.
- Wang et al. *ZeroDDI: A Zero-Shot Drug-Drug Interaction Event Prediction Method with Semantic Enhanced Learning and Dual-Modal Uniform Alignment*. IJCAI 2024.
- Sun et al. *ExDDI: Explaining Drug-Drug Interaction Predictions with Natural Language*. AAAI 2025. DOI: 10.1609/aaai.v39i24.34709.
- Qian et al. *DTI-LM: language model powered drug–target interaction prediction*. Bioinformatics 40(9), btae533 (2024).

## Author repositories to pin

- `gadevito/LLMDDI`
- `zhufq00/DDIs-Prediction`
- `wzy-Sarah/ZeroDDI`
- `ZhaoyueSun/ExDDI`
- `compbiolabucf/DTI-LM`

## EEE implementation references

- current `every_eval_ever/eval_types.py`;
- current `every_eval_ever/helpers/io.py`;
- `utils/README.md` adapter conventions;
- datastore contribution guide and validator.


---

[Previous](10-27-pre-implementation-blockers.md) · [Design index](../DESIGN.md) · [Next](../DESIGN.md)
