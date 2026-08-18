# Drug-interaction paper-results adapter

This offline adapter converts frozen aggregate result tables from five papers
into Every Eval Ever `EvaluationLog` files. It covers eight study–dataset
collections and preserves the paper-native protocol and metric semantics:

- LLMDDI — DrugBank, random-pair zero-shot and fine-tuned results;
- TextDDI — DrugBank and TWOSIDES, chronological unseen-drug and vanilla
  known-drug settings;
- ZeroDDI — DrugBank CZSL and GZSL unseen-relation-class settings;
- ExDDI — paired DrugBank- and DDInter-explanation corpora under pair-held-out
  (paper-labeled transductive), one-unseen-drug, and two-unseen-drug regimes;
- DTI-LM — DrugBank and BindingDB under balanced/unbalanced warm, cold-drug,
  and cold-protein regimes.

The corpus is best described as **paper-reported evaluations of
language-model-based drug-interaction systems**. It includes directly comparable
non-LM baselines. It is not a set of rerun evaluations and it does not imply that
every method is a generative chat LLM.

## Safety and scope

- Primary paper tables and supplements are authoritative; Papers with Code is
  not a runtime or data dependency.
- The adapter is aggregate-only. It contains no DrugBank drug records,
  descriptions, SMILES strings, protein sequences, or instance-level examples.
- DrugBank-derived datasets use EEE `source_type="other"` and carry only
  high-level version and split metadata.
- LLMDDI is pinned as an arXiv snapshot because its later journal report differs.
  The two versions must never be mixed.
- Source bundles are validated by SHA-256, foreign keys, exact counts, bounds,
  logical uniqueness, and frozen anchor cells. These controls establish internal
  integrity, not independent transcription verification.

The generic Papers with Code adapter is separate work (upstream PR #209 at the
time this adapter was prepared) and is not part of this contribution. If that
adapter lands, a generic PwC `drugbank` dataset label still should not be treated
as proof of a particular split protocol: random/IID, pair-held-out transductive,
one- or two-unseen-drug inductive, scaffold/chemical OOD, unseen-relation
CZSL/GZSL, and DTI warm/cold regimes are distinct evaluation semantics.

## Usage

List source snapshots:

```bash
uv run python -m every_eval_ever.adapters.drug_interaction_papers.adapter --list-snapshots
```

Audit the frozen sources without writing datastore records:

```bash
uv run python -m every_eval_ever.adapters.drug_interaction_papers.adapter \
  --audit-only \
  --audit-output /tmp/drug-interaction-source-audit.json
```

Generate all collections into a temporary data root:

```bash
uv run python -m every_eval_ever.adapters.drug_interaction_papers.adapter \
  --output-dir /tmp/eee-drug-interaction-data
```

Select a study or dataset:

```bash
uv run python -m every_eval_ever.adapters.drug_interaction_papers.adapter \
  --study textddi --dataset twosides \
  --output-dir /tmp/eee-textddi-twosides
```

Existing non-empty collection directories are rejected unless `--replace` is
provided. Replacement is staged, re-read, semantically checked, and rolled back
on failure.

Run the canonical audit pack:

```bash
uv run python -m every_eval_ever.adapters.drug_interaction_papers.audit --block all
```

The audit writes evidence under `experiment-plan/evidence/`. A technical pass
is not an independent scientific verification. The adapter code can be reviewed
and merged while this remains true, but scheduled publication and any generated
datastore submission stay blocked until a materially separate reviewer checks
the primary-source cells recorded in the source-verification ledger.

## Validation

```bash
uv run pytest -q tests/test_drug_interaction_papers_adapter.py
uv run python -m every_eval_ever validate \
  '/tmp/eee-drug-interaction-data/*/*/*.json'
```

The adapter PR contains code, tests, aggregate source bundles, and its audit
artifacts. It contains no generated datastore records. Any later data submission
is a separate release step and must satisfy the independent source-verification
gate first.
