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

- Primary paper tables and supplements are authoritative; Papers With Code is
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

The generic Papers with Code `drugbank` table is handled by the separate
`paperswithcode` adapter. It already contains aggregate model/metric rows, so it
does not require DrugBank XML or instance-level examples. **That generic table is
not complete DrugBank benchmark coverage:** a DrugBank dataset label alone does
not identify whether an evaluation is random/IID, pair-held-out transductive,
one- or two-unseen-drug inductive, scaffold/chemical OOD, unseen-relation
CZSL/GZSL, or a DTI warm/cold split. See
`../paperswithcode/DRUGBANK_PROTOCOL_SCOPE.md` for the split-aware coverage
contract and current PwC-adapter limitation.

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

Run the canonical experiment pack:

```bash
uv run python -m every_eval_ever.adapters.drug_interaction_papers.audit --block all
```

The audit writes evidence under `experiment-plan/evidence/`. A technical pass
is not an independent scientific verification; the release gate remains blocked
until a second reviewer checks the primary-source cells recorded in the source
verification ledger.

## Validation

```bash
uv run pytest -q tests/test_drug_interaction_papers_adapter.py
uv run pytest -q tests/test_paperswithcode_drugbank.py
uv run python -m every_eval_ever validate \
  '/tmp/eee-drug-interaction-data/*/*/*.json'
```

The adapter PR should contain code, tests, source bundles, and the canonical
experiment plan. Generated datastore records belong in a later data-only
submission.
