<!-- Part 5 of 11. Previous: 04-9-repository-layout.md. Next: 06-13-metric-mapping.md. -->

## 11. Inclusion and exclusion rules

### 11.1 Include a row when

- it belongs to a selected numerical table;
- it uses the same dataset construction and protocol as the table header;
- the value is directly reported numerically;
- the method identity can be represented without guessing;
- metric direction and legal range are established;
- source provenance is classifiable.

### 11.2 Exclude a row when

- it is a derived relative-improvement row;
- it is a rank, bolding marker, or narrative conclusion rather than a metric;
- it is recoverable only from a plot;
- it uses a different hidden dataset or incomparable split;
- the exact model/method cannot be represented even with a source-scoped identity;
- it is a copied literature baseline whose dataset is materially different and the table itself warns against direct comparison;
- its source version conflicts with the selected snapshot.

Every exclusion is declared in the study manifest. Conversion code does not silently skip malformed or inconvenient rows.

### 11.3 Why include non-LM baselines

The selected paper tables are comparison artifacts. Extracting only the proposed LM-based rows would remove the context needed to interpret their results and could introduce selection bias. Baselines are therefore included when directly comparable under the selected table contract.

The adapter README must state that the collection is language-model-centered, not language-model-exclusive.

---

## 12. Protocol catalog

### 12.1 LLMDDI

#### `random-pair-stratified`

```text
split_unit: drug pair examples
split_method: random stratified sampling
pair_overlap: prohibited by row identity only
 drug_entity_overlap: uncontrolled
relation_class_overlap: not_applicable
negative_sampling: balanced with sampled non-interactions
```

Conditions:

```text
zero-shot
fine-tuned
```

Do not derive `transductive=true`.

### 12.2 TextDDI

#### `chronological-unseen-drug`

```text
drug sets: disjoint train/validation/test
ordering: chronological by drug development date
train: both drugs in training-drug set
test: at least one drug from test-drug set
pair novelty: train pairs excluded
candidate relation classes: seen
```

The test population mixes one-unseen-drug and two-unseen-drug pairs; do not split them unless the source provides separate results.

#### `vanilla-known-drug`

```text
paper claim: predicts interactions between two known drugs
drug distribution: drugs distributed across train/validation/test
pair novelty: not fully specified in source table
entity generalization: not the target
```

Use the paper-native label. Do not strengthen it to an audited drug-transductive guarantee.

### 12.3 ZeroDDI

#### `unseen-relation-czsl`

```text
train relation classes: seen
validation/test relation classes: unseen, three-fold class split
candidate label space at test: unseen classes only
drug novelty: not the controlled axis
```

#### `unseen-relation-gzsl`

```text
train relation classes: seen
validation/test: seen and unseen classes
seen validation/test instances: no instance overlap with train
candidate label space: seen plus unseen
drug novelty: not the controlled axis
```

### 12.4 ExDDI

#### `pair-unseen-drugs-overlap-allowed`

Paper label: transductive.

```text
random sample split: 0.7/0.1/0.2
pair novelty: test pairs unseen
 drug overlap: allowed
```

#### `one-unseen-drug`

Paper label: inductive S2.

```text
train drugs: M1
test pair: one M1 drug and one M3 drug
unseen drug count: 1
```

#### `two-unseen-drugs`

Paper label: inductive S1.

```text
train drugs: M1
test pair: both drugs from M3
unseen drug count: 2
```

The canonical IDs use semantic names; paper aliases S1/S2 are preserved as metadata.

### 12.5 DTI-LM

#### `warm`

```text
drug overlap: allowed
target overlap: allowed
```

#### `cold-drug`

```text
drug overlap: prohibited
target overlap: allowed
```

#### `cold-protein`

```text
drug overlap: allowed
target overlap: prohibited
```

Conditions:

```text
balanced-1-to-1
unbalanced-up-to-1-to-10
```

The condition name uses “up to” because the paper uses all samples when a full 1:10 ratio is unavailable.

---


---

[Previous](04-9-repository-layout.md) · [Design index](../DESIGN.md) · [Next](06-13-metric-mapping.md)
