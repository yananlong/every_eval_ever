# DrugBank leaderboard protocol scope

`DrugBank` is a dataset/source label, not a complete benchmark identity.
Drug-interaction results are comparable only after the evaluation protocol is
identified. In particular, **transductive**, **inductive/cold-start**,
**zero-shot relation**, and broader **OOD** settings must not be collapsed into
one DrugBank leaderboard.

## Required comparison axes

Protocol-qualified DrugBank evaluations should preserve, when the source
establishes them:

- `drug_entity_overlap`
- `target_entity_overlap`
- `relation_class_overlap`
- `pair_overlap`
- `temporal_ordering`
- `candidate_label_space`
- `negative_sampling`
- split-specific preprocessing or representation fitting

A database name alone is insufficient to infer any of those properties.

## Core split families

The earlier drug-interaction design uses the following distinctions:

| Family | Meaning | Treatment |
|---|---|---|
| random/IID or random-pair | Random row/pair split; entity overlap may be uncontrolled | Legacy/sanity comparison unless overlap is explicitly established |
| pair-held-out / edge-held-out | Test interaction pairs are unseen while constituent entities may recur | Transductive only when the source establishes entity reuse |
| one-unseen-drug / new-old | One drug in a test pair is absent from training | Inductive/cold-start; weaker OOD sanity case |
| two-unseen-drugs / new-new | Both drugs in a test pair are absent from training | Inductive/cold-start; first-class unseen-entity generalization |
| cold-drug | Drug entities held out for DTI | DTI-specific; do not merge with DDI |
| cold-target / cold-protein | Target/protein entities held out for DTI | DTI-specific; distinct from cold-drug |
| unseen relation CZSL/GZSL | DDI event/relation classes are unseen, with unseen-only or mixed candidate spaces | Relation OOD, not unseen-drug induction |
| scaffold / cluster / low-similarity | Chemical-structure OOD | First-class OOD when source construction is auditable |
| temporal / prospective | Test examples occur after a training cutoff | First-class OOD when cutoff and leakage controls are reported |
| source / cross-dataset | Dataset or evidence-source shift | First-class only when task/label ontology is compatible |

The exact `S1`/`S2`, `CS1`/`CS2`, or similar paper labels are source-specific.
Never assign their semantics from the token alone; map them from the paper's
split definition.

## Papers with Code limitation

The generic Papers with Code adapter currently identifies a leaderboard scale by
`(dataset_id, metric)` and builds `evaluation_name` from task plus dataset. It
does **not** carry a general protocol/split dimension. Therefore:

```bash
uv run python -m every_eval_ever.adapters.paperswithcode.adapter \
  --dump /path/to/paperswithcode.dump \
  --dataset-slug drugbank
```

means only "convert PwC rows attached to the dataset slug `drugbank`." It must
not be described as complete DrugBank coverage, transductive coverage, or
inductive coverage.

The three-row CADGL / SSI-DDI / MHCA-DDI fixture in
`tests/test_paperswithcode_drugbank.py` is intentionally a regression fixture
for that **generic PwC aggregate table only**. It proves aggregate conversion,
metric normalization, and model identity handling. It does not establish the
split semantics of those rows and does not substitute for protocol-qualified
leaderboards.

## Protocol-qualified EEE identity

The semantic dimensions are study, dataset, task, protocol, and sometimes a
condition, but the **current primary-paper adapter's concrete `evaluation_name`**
is intentionally narrower:

```text
<collection_slug>.<protocol_id>
```

The collection slug already scopes the study/dataset pair, while task type,
condition, candidate label space, and novelty axes remain explicit in the result
metadata and logical record identity. Existing examples include:

```text
textddi-drugbank.chronological-unseen-drug
exddi-drugbank.two-unseen-drugs
dti-lm-drugbank.cold-drug
zeroddi-drugbank.unseen-relation-czsl
```

The PwC qualification overlay must use that same namespace rather than inventing
a parallel `<study>.<dataset>.<task>.<protocol>` convention. Do not merge scores
across protocol identities merely because `dataset_name` is DrugBank.

## Coverage rule for future PwC/primary-source work

For DrugBank-associated leaderboard discovery, enumerate leaderboard **protocols
first**, then attach the models and score cells belonging to each protocol. At a
minimum keep these buckets separate:

1. generic/random/IID or pair-held-out results;
2. one-unseen-drug/new-old induction;
3. two-unseen-drugs/new-new induction;
4. scaffold/chemical OOD where published;
5. relation-class OOD (CZSL/GZSL), separately from entity OOD;
6. DTI warm/cold-drug/cold-target leaderboards, separately from DDI;
7. other audited OODs such as temporal, source, cross-dataset, or interaction
   cliffs when the paper exposes a reproducible split definition.

If PwC does not encode enough metadata to distinguish these variants, use the
primary paper or official result artifact to qualify the leaderboard rather than
inferring a protocol from the generic PwC dataset page.

## Reviewed protocol overlay

The implementation substrate lives in `protocol_overlay.py`. It is deliberately
separate from the generic PwC conversion so ordinary `--dataset-slug drugbank`
output remains unchanged until a caller explicitly applies reviewed protocol
metadata.

Reviewed entries live in `protocol_overlays/drugbank.yaml`. The manifest starts
empty: a paper enters it only after a primary paper or official result artifact
establishes the split semantics. Candidate papers and guessed mappings do not
belong in the runtime manifest.

Each non-empty entry is a **snapshot-bound review record**, not a rule that is
silently carried forward to future PwC dumps. It must include:

- the exact valid `YYYYMMDD` dump date it was reviewed against;
- stable PwC row anchors (`evaluations.id`, `paper_id`, `dataset_id`, `task_id`,
  and raw `model_name`);
- an explicit metric-name list, so later-added metrics are never implicitly
  qualified;
- a SHA-256 fingerprint of the complete raw PwC `metrics` object for that row;
- normalized protocol semantics and all required novelty axes; and
- an absolute HTTP(S) evidence URL plus a table/section locator and verification
  note.

Application is fail-closed. A non-empty overlay is rejected when the current dump
version is malformed or differs from the reviewed dump, when the source metrics
payload fingerprint changes, when an anchor or selected metric drifts, when metric
selectors overlap, or when an opaque source token such as bare `S1`/`CS2` is used
as a normalized protocol id. A newer dump therefore requires explicit re-review;
calendar ordering is not treated as evidence that an older qualification remains
valid.

The packaged empty manifest is a literal no-op and intentionally bypasses these
source checks, because no scientific qualification is being applied.

Qualification changes only the semantic benchmark identity and attaches audited
protocol metadata. It does not replace the PwC score or score provenance:

- `evaluation_result_id` remains `paperswithcode.<evaluation-id>.<metric>`;
- raw and canonicalized score values are unchanged;
- `source_metadata` remains Papers with Code;
- primary-source protocol evidence is added separately to result details;
- the reviewed metrics fingerprint is retained in result details; and
- a PwC source score cell is emitted at most once.

The qualified `evaluation_name` exactly follows the existing primary-paper
adapter:

```text
<collection_slug>.<protocol_id>
```

Study id, dataset id, task id, task type, condition id, candidate label space,
and the novelty axes are retained as explicit protocol metadata instead of being
encoded into a second naming convention. This lets a PwC-reported score and a
primary-paper-transcribed score refer to the same semantic evaluation while
retaining distinct source provenance and source cell identities.

`tests/test_paperswithcode_protocol_overlay.py` uses deliberately synthetic
method/paper identities for qualification mechanics. It covers the literal empty
no-op, exact dump pinning, valid calendar dates, metrics-payload fingerprinting,
explicit metric scope, evidence URL validation, wrapper integration, provenance
and score-cell identity preservation, missing/drifted anchors, disjoint versus
overlapping metric qualification, and opaque split-token rejection. The real
CADGL / SSI-DDI / MHCA-DDI names remain only in the generic PwC regression fixture
and are not evidence that those rows have been protocol-qualified.

The next data step is intentionally narrow: review post-2024 DrugBank DDI papers
with explicit one-unseen-drug/new-old or two-unseen-drugs/new-new splits first,
then auditable scaffold/temporal OOD, relation OOD, older legacy/random results,
and finally DTI warm/cold-drug/cold-target as a separate task family.
