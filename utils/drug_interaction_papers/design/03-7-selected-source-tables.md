<!-- Part 3 of 11. Previous: 02-5-terminology.md. Next: 04-9-repository-layout.md. -->

## 7. Selected source tables

### 7.1 LLMDDI

**Study:** *LLMs For drug-Drug interaction prediction using textual drug descriptors*  
**Dataset collection:** DrugBank 5.1.12-derived balanced DDI evaluation

Selected final-paper equivalents of:

- zero-shot model comparison;
- fine-tuned model comparison.

The 13 external validation datasets are deferred from v1 because they introduce another 13 dataset contracts, heterogeneous provenance, and a different evaluation matrix. Few-shot results are included only if the final paper exposes a complete numerical table; figure-only results are not transcribed.

**Protocol label:** `random-pair-stratified`  
**Entity novelty:** `uncontrolled`  
**Conditions:** `zero-shot`, `fine-tuned`

The source uses a large balanced positive/negative pool and a small stratified train/validation sample. No drug-disjoint constraint is established, so the adapter must not call this entity-transductive.

### 7.2 TextDDI

**Study:** *Learning to Describe for Predicting Zero-shot Drug-Drug Interactions*  
**Datasets:** DrugBank and TWOSIDES

Selected tables:

- main zero-shot comparison table;
- appendix vanilla known-drug comparison table.

Include every method row in each table except the derived “relative improvement” row.

Do not include in v1:

- the 100-sample GPT-3.5/GPT-4 appendix comparison;
- the language-model backbone ablation;
- few-shot values shown only in a figure;
- qualitative prompt examples.

The zero-shot split partitions drugs into chronologically ordered disjoint train, validation, and test drug sets. The vanilla split is paper-labeled as prediction between known drugs and distributes drugs across train/validation/test; it is represented as `vanilla-known-drug`, not generically as “transductive.”

DrugBank is multiclass with macro-F1, accuracy, and Cohen’s kappa. TWOSIDES is multilabel with PR-AUC, ROC-AUC, and accuracy. These are separate task contracts.

### 7.3 ZeroDDI

**Study:** *ZeroDDI: A Zero-Shot Drug-Drug Interaction Event Prediction Method with Semantic Enhanced Learning and Dual-Modal Uniform Alignment*  
**Dataset:** DrugBank 5.1.9-derived DDIE corpus

Selected table:

- the main CZSL/GZSL comparison table, all method rows and all reported metrics.

Do not include in v1:

- PLM-backbone ablation;
- component ablations;
- qualitative visualizations.

The unseen object is the DDI event class, not necessarily the drug. CZSL restricts candidate labels to unseen classes; GZSL evaluates seen and unseen classes together.

### 7.4 ExDDI

**Study:** *ExDDI: Explaining Drug-Drug Interaction Predictions with Natural Language*  
**Datasets:** paired interaction corpus with DrugBank explanations; the same paired interaction corpus with DDInter explanations

Selected table:

- Appendix Table A2, not merely the compact main Table 1, because A2 includes standard deviations.

Include all five methods and all three split regimes for both explanation sources.

Do not include in v1:

- binary prediction Table A3;
- multi-class prediction Table A4;
- human-evaluation count tables;
- qualitative examples.

Important dataset identity correction: the two ExDDI datasets are not independent raw DrugBank and DDInter samples. The paper intersects positive and negative pairs across the sources and changes the explanation supervision. The adapter therefore names them as paired ExDDI corpora, not simply `DrugBank` and `DDInter`.

### 7.5 DTI-LM

**Study:** *DTI-LM: language model powered drug–target interaction prediction*  
**Datasets:** processed DrugBank and processed BindingDB

Selected tables:

- DrugBank warm/cold table;
- BindingDB warm/cold table;
- balanced and 1:10 conditions;
- all four compared methods;
- AUROC and AUPRC.

Do not include in v1:

- Yamanishi_08 or Luo datasets;
- hyperparameter tables;
- representation-similarity analyses;
- runtime comparisons.

The BindingDB source is not merely “binary BindingDB.” The author code filters to Kd, averages repeated measurements, removes the ambiguous interval, labels Kd below 30 nM positive and Kd above 100 nM negative, and applies sequence/SMILES validity and length filtering. These details are part of dataset identity.

---

## 8. Scope matrix

| Study | Dataset collection | Task | Protocols | Conditions | Metrics |
|---|---|---|---|---|---|
| LLMDDI | DrugBank-derived | Binary DDI | Random-pair stratified; entity overlap uncontrolled | Zero-shot; fine-tuned | Accuracy, precision, sensitivity, F1 |
| TextDDI | DrugBank | Multiclass DDI event | Chronological unseen-drug; vanilla known-drug | Standard paper setting | Macro-F1, accuracy, kappa |
| TextDDI | TWOSIDES | Multilabel DDI event | Chronological unseen-drug; vanilla known-drug | Standard paper setting | PR-AUC, ROC-AUC, accuracy |
| ZeroDDI | DrugBank DDIE | DDI event-class prediction | CZSL; GZSL | Standard paper setting | Twelve class-aware top-k/generalized metrics |
| ExDDI | Paired DrugBank-explanation corpus | DDI explanation generation | Pair-unseen/drugs-overlap-allowed; one unseen drug; two unseen drugs | Standard paper setting | BLEU, ROUGE-1, ROUGE-2, ROUGE-L |
| ExDDI | Paired DDInter-explanation corpus | DDI explanation generation | Same three | Standard paper setting | Same four |
| DTI-LM | Processed DrugBank | Binary DTI | Warm; cold-drug; cold-protein | Balanced 1:1; unbalanced 1:10 | AUROC, AUPRC |
| DTI-LM | Processed BindingDB | Binary DTI | Warm; cold-drug; cold-protein | Balanced 1:1; unbalanced 1:10 | AUROC, AUPRC |

### Planning estimate

Using the currently verified published/preprint tables, the planned corpus contains approximately:

- **548 metric results**;
- **99 aggregate logs** when logs are separated by study, dataset, method, and condition.

The final source manifests, not this estimate, are the acceptance authority. LLMDDI counts remain provisional until final-paper reconciliation.

---


---

[Previous](02-5-terminology.md) · [Design index](../DESIGN.md) · [Next](04-9-repository-layout.md)
