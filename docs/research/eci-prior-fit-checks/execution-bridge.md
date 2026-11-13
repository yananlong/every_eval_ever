# Execution Bridge

This file tells an engineer what to build and run. Formulas and rules are in the "Methods Specification" section of experiment-plan.md (M1 to M10); block fields are in run-blocks.json.

## Setup (once, before B0)

Working directory for every command: the project root (`v11/` in the original layout; any directory works). External inputs live under `ext/` and are read-only; our code and outputs live under `runs/`. No interpreter is started with its working directory inside `ext/`.

1. Check input digests: `ext/epoch_zip/benchmark_data.zip` sha256 `9d728f9f8635069812530a157aef7a6cec935fffc93f33d3031bad5c6888b1d5`; `ext/eee/entries.jsonl` sha256 `98e5f48af77952d478013cf578ca00ecd17e5e41f7a647bbc80e8e37b2b120fe`; `ext/eci-public` at git `e04929ab751531e558b1a61e86f436487c710ef8`.
2. Copy `ext/eci-public` (without `.git`) to `runs/vendor/eci-public` and confirm the copy is identical file by file. Install from the copy so that no build step writes under `ext/`.
3. Create the uv project `runs/` (Python >= 3.12; the machine has 3.13) with dependencies: the vendored `eci` package as a path dependency, and pymc (>= 6.0), pytensor, arviz (>= 1.0), numpy, scipy, pandas, matplotlib at the versions in `ext/eci-public/uv.lock`, plus pyarrow. Save `uv pip freeze` to `runs/env.lock.txt`. This step needs network access.
4. Write `runs/strata.json` (M2) from the published files and `runs/freeze.json` with the digests above.
5. Smoke test: `uv run --project runs python -c "import eci, pymc, arviz; print(pymc.__version__, arviz.__version__)"`.

Shared library `runs/lib/`: `data.py` (read members of the zip with `zipfile`; never from an extracted copy), `fit.py` (wrapper around `fit_bayesian_eci` with the sidecar and skip logic), `anchored.py` (M1), `sens_metrics.py` (M3), `variants.py` (P8-P10 builders and the context manager that swaps `eci.bayesian.build_bayesian_model`, `_FREE_VARS` and `_DIAGNOSTIC_VARS` in memory), `generators.py` (M4), `ppc_checks.py` (M5, M6), `predict.py` (M8).

Facts about Epoch's code that the wrapper relies on (checked at e04929a):

- `fit_bayesian_eci(df, priors, performance_clip_eps=1e-3, draws=None, tune=None, chains=4, target_accept=0.95, random_seed=12345, evaluate=False, ...)` returns `(eci_df, edi_df, draws)`; `draws["eci"]` is the per-draw anchored ECI (draws x models, in `draws["model_names"]` order), `draws["trace"]` the full trace, `draws["attempts"]` and `draws["started_from"]` the sampler history, and `draws["evaluation"]` the diagnostic tables when `evaluate=True`.
- `df` needs columns `model_id`, `benchmark_id`, `performance`, `benchmark`, `Model`. The published fit input has them.
- `draws=None` means adaptive (1,000 up to 16,000 per chain in the dense stage); an integer fixes every run at that size.
- `evaluate=True` adds `log_likelihood` and `posterior_predictive` groups (each draws x 2,879 values). It does not store a log prior.
- Convergence failures are warnings. The wrapper must read `draws["attempts"][-1]` and record pass or fail itself.
- Epoch's dense-mass-matrix code looks up draws by the names in `eci.bayesian._FREE_VARS`; a model variant with different free variables fails with a KeyError unless that tuple is replaced for the duration of the fit.

Resource notes for 4 CPUs and 15 GB RAM: every fit runs 4 chains on 4 cores, so run fits one at a time. Memory per fit is under 2 GB (the largest arrays are the two draws x 2,879 groups under `evaluate=True`: about 0.2 GB at 4,000 total draws). Disk: about 1 GB for B0 to B3 and about 2.5 GB for the EEE objects.

## Block Hand-off

### B0

- Claim IDs: C1, C2
- Decision gate ID: G0
- Current evidence class: exploratory
- Requested evidence class: exploratory
- Inputs required: the zip of 2026-11-13: members `epoch_capabilities_index/processed_data_for_eci.csv` (fit input), `eci_scores.csv`, `edi_scores.csv`, `eci_bootstraps.json` (published results)
- Declared input snapshot paths: ext/epoch_zip/benchmark_data.zip (sha256 at start)
- Declared evaluator snapshot paths: ext/eci-public at git e04929ab751531e558b1a61e86f436487c710ef8
- Expected implementation entrypoint: runs/b0_reproduce.py
- Expected command or notebook: `uv run --project runs python runs/b0_reproduce.py`
- What to compute: (1) B0a: fit the published fit input with defaults and `evaluate=True` for seeds 12345, 22345, 32345. (2) Add to each trace the summed log density of the three hyperpriors per draw (group `log_prior`) and the per-draw ECI. (3) Against `eci_scores.csv`, seed 12345: $d_m$, $d_m / W_m$, Spearman, width ratio; against `edi_scores.csv`: max abs difference of `edi` and `estimated_slope_scaled`; against `eci_bootstraps.json`: the nine top-10 adjacent-pair probabilities, ours and published. (4) Per seed: Epoch's `sampler_summary` row and `attempts`. (5) Seed-to-seed SD of posterior-mean ECI per model. (6) B0b: fit `prepare_benchmark_data(zip)` with seed 12345, list the rows that differ from the published input, and score S1-S4 against B0a.
- Output artifacts to produce: runs/B0/reproduction.json, runs/B0/seed{12345,22345,32345}.nc with sidecars, runs/B0/b0b_loader.nc with sidecar
- Auditor-facing checks: every G0 criterion with its value; per-seed diagnostics; the three differing rows in B0b
- Intended lineage relation: baseline
- Parent run ID or rationale: none (root)
- Hidden information unavailable to the evaluated system: not applicable
- Failure, skip, null, timeout, and retry states to retain: sampler stage, attempts list and warnings for every seed, including failed seeds; Epoch's own draw ladder is the only retry, plus one rerun at target_accept 0.99 if G0 asks for it
- Idempotency and restart requirements: each fit writes its .nc and sidecar atomically; a rerun skips a fit only if the sidecar's input digest, code digest, seed and arguments match (M10)
- Known blockers: the environment is not built yet (PyMC install needs network); the netCDF round-trip of an arviz 1.x DataTree should be tested on the first trace before the other seeds run

### B1

- Claim IDs: C1, C2
- Decision gate ID: G1
- Current evidence class: exploratory
- Requested evidence class: exploratory
- Inputs required: B0 seed-12345 posterior; the fit input (for the observation pattern, dates and organisations); prior-grid.json (positive-control prior)
- Declared input snapshot paths: ext/epoch_zip/benchmark_data.zip; runs/B0/seed12345.nc
- Declared evaluator snapshot paths: ext/eci-public; runs/lib/ppc_checks.py; runs/lib/sens_metrics.py; experiment-plan/prior-grid.json (all frozen, with digests in runs/freeze.json, before any generator or positive-control fit runs)
- Expected implementation entrypoint: runs/b1_simulate.py
- Expected command or notebook: `uv run --project runs python runs/b1_simulate.py --stage pc,prior,null,2d,offset,shape,disp,drift`
- What to compute: (1) positive control: refit real data with $\tau_\alpha \sim \operatorname{LogNormal}(\ln 0.05, 0.1)$ on 3 seeds and score S1-S4 against the B0 fit of the same seed. (2) G-prior shares. (3) For each of 199 G-null replicates: simulate, fit, test convergence, compute T1-T7 and the recovery indicators. (4) For each of 5 misfit generators x 20 replicates: simulate, fit, compute T1-T7 and the max-T adjusted p of the targeted check against the null reference. (5) Summarise: recovery coverage overall and by stratum; the null reference table; power per generator with its Clopper-Pearson interval; non-converged counts.
- Output artifacts to produce: runs/B1/calibration.json; runs/B1/rep/<generator>_<index>.json and .nc (400 thinned draws); runs/B1/truth/<generator>_<index>.npz
- Auditor-facing checks: recovery coverage by stratum; power per check; number of converged null replicates; positive-control S1-S4 per seed
- Intended lineage relation: negative_control (G-null), sensitivity (misfit generators and positive-control prior)
- Parent run ID or rationale: R001
- Hidden information unavailable to the evaluated system: true parameters stored in runs/B1/truth/, never read by ppc_checks.py
- Failure, skip, null, timeout, and retry states to retain: every replicate's convergence status and attempts; non-converged replicates excluded from reference and power, with counts
- Idempotency and restart requirements: replicate seed = first 4 bytes of sha256("<generator>:<index>") as a big-endian integer; a finished replicate (sidecar present and digests match) is skipped; calibration.json is rebuilt from the per-replicate files on every run
- Known blockers: about 10 hours of sampling; run the positive control first so G1's branch (b) is known early

### B2

- Claim IDs: C1
- Decision gate ID: G2
- Current evidence class: exploratory
- Requested evidence class: confirmatory
- Inputs required: the fit input; prior-grid.json; the G1 record in runs/B1/calibration.json (whether the S2 limit was tightened)
- Declared input snapshot paths: ext/epoch_zip/benchmark_data.zip; runs/B1/calibration.json
- Declared evaluator snapshot paths: ext/eci-public; experiment-plan/prior-grid.json; runs/lib/sens_metrics.py
- Expected implementation entrypoint: runs/b2_sensitivity.py
- Expected command or notebook: `uv run --project runs python runs/b2_sensitivity.py`
- What to compute: (1) fit P0 (seed 12345) and P0b (seed 22345) with default priors and draws=4000; compute the noise floor and apply the doubling rule of M3 if it fails. (2) S5 screen on P0. (3) Fit P1-P10, X1, X2 with draws=4000 and seed 12345; score S1-S4 per stratum against P0. (4) If S5 flagged a hyperprior, fit and score the two power-scaled refits. (5) Assign the C1 verdict by the decision rule.
- Output artifacts to produce: runs/B2/sensitivity.json, runs/B2/fig_sensitivity.png, runs/B2/<entry>.nc (posterior group only) with sidecars
- Auditor-facing checks: S1-S5 per prior and stratum beside the noise floor; the psens table; $P(\text{in top 10})$ per prior; convergence status of every entry
- Intended lineage relation: sensitivity
- Parent run ID or rationale: R001 (baseline), R002 (metric validity)
- Hidden information unavailable to the evaluated system: not applicable
- Failure, skip, null, timeout, and retry states to retain: an entry that fails Epoch's checks is retried once with draws doubled, then recorded as unresolved; unresolved entries appear in the table
- Idempotency and restart requirements: one .nc and sidecar per grid entry, skipped on restart if digests and arguments match
- Known blockers: P8-P10 need model variants supplied at run time by runs/lib/variants.py (see Setup); P9 may need a non-centred parameterisation; confirm the arviz `psens` signature against the pinned version

### B3

- Claim IDs: C2
- Decision gate ID: G3
- Current evidence class: exploratory
- Requested evidence class: confirmatory
- Inputs required: B0 seed-12345 trace and its evaluation tables; B1 null reference values and power table; the fit input
- Declared input snapshot paths: ext/epoch_zip/benchmark_data.zip; runs/B0/seed12345.nc; runs/B1/calibration.json
- Declared evaluator snapshot paths: ext/eci-public (evaluation.py for B3a); runs/lib/ppc_checks.py
- Expected implementation entrypoint: runs/b3_ppc.py
- Expected command or notebook: `uv run --project runs python runs/b3_ppc.py`
- What to compute: (B3a) write Epoch's report with `save_evaluation` and copy its metrics table into ppc.json. (B3b) T1-T7 on the real data; unadjusted, max-T adjusted and raw p-values. (B3c) write folds.csv, fit 5 folds, compute PIT per held-out row, overall coverage with bootstrap interval, per-benchmark binomial tests. (B3d) only if something is rejected or flagged: build $F$, run the deletion test, refit without $F$, compute relative shifts. Then assign the C2 verdict.
- Output artifacts to produce: runs/B3/ppc.json, runs/B3/evaluation_report.pdf (Epoch's own report), runs/B3/folds.csv, runs/B3/fold{0..4}.nc with sidecars, runs/B3/fig_checks.png
- Auditor-facing checks: the three p-values per check; power label per check; held-out coverage table; $F$ and the B3d shifts if run
- Intended lineage relation: baseline (B3a, B3b, B3c), ablation (B3d)
- Parent run ID or rationale: R001, R002
- Hidden information unavailable to the evaluated system: held-out scores removed before fitting each fold; folds.csv written before any fold fit
- Failure, skip, null, timeout, and retry states to retain: per-fold convergence and attempts; a fold that fails convergence is reported and its rows are scored and also shown separately
- Idempotency and restart requirements: fold fits keyed by fold index and the digest of folds.csv; skipped on restart if they match
- Known blockers: needs at least 150 converged null replicates from B1

### B4

- Claim IDs: C3
- Decision gate ID: G4
- Current evidence class: exploratory
- Requested evidence class: exploratory
- Inputs required: EEE manifest dd7efcff entries.jsonl; all aggregate objects it lists; Epoch benchmark_metadata.csv, model_metadata.csv and the fit input; for stage b, the B0 seed-12345 trace
- Declared input snapshot paths: ext/eee/entries.jsonl (sha256 98e5f48a...); downloaded objects under runs/B4/objects/ verified against the manifest sha256; ext/epoch_zip/benchmark_data.zip; runs/B0/seed12345.nc (stage b)
- Declared evaluator snapshot paths: runs/B4/benchmark_map.csv, runs/B4/model_map.csv and runs/B4/source_class.csv (digests at freeze)
- Expected implementation entrypoint: runs/b4_run.py (stages implemented in runs/b4_crosswalk.py and runs/b4_transfer.py)
- Expected command or notebook: `uv run --project runs python runs/b4_run.py --stage a`, then the manual mapping and audit, then `uv run --project runs python runs/b4_run.py --stage b`; `--stage all` runs both and stops after stage a if the maps are not frozen
- What to compute: stage a follows M9 steps 1 to 8; stage b computes the same-upstream control, PIT and coverage, agreement and bias as in M9, then assigns the C3 verdict.
- Output artifacts to produce: runs/B4/collection_screen.csv, runs/B4/crosswalk.parquet (one row per EEE result with its class), runs/B4/pairs.parquet, runs/B4/audit_sample.csv, runs/B4/transfer.json
- Auditor-facing checks: counts by class and exclusion reason; audit errors with the Clopper-Pearson bound; same-upstream differences; coverage with bootstrap interval and the two sensitivity cuts; EEE-vs-EEE agreement and its number of source pairs
- Intended lineage relation: baseline
- Parent run ID or rationale: R001 for predictions
- Hidden information unavailable to the evaluated system: ECI predictions are not loaded in stage a; stage b refuses to run unless the map digests match runs/freeze.json
- Failure, skip, null, timeout, and retry states to retain: failed downloads listed and retried; every EEE result classified into exactly one class
- Idempotency and restart requirements: object cache keyed by sha256, files already present and verified are not fetched again; crosswalk and transfer outputs rebuilt from the cache and the frozen maps
- Known blockers: none for location: objects are fetched from the Hugging Face dataset `evaleval/EEE_datastore` at the `object_path` listed in manifest dd7efcff (`flat/manifests/sha256_dd7efcff.../entries.jsonl`), and each download is checked against its manifest sha256, so the pin is by content, not by repo revision; the benchmark map and the review of ambiguous models are manual; Epoch's model groups combine several versions, so an EEE record maps to a group only when model_metadata.csv lists that version or the reviewer records why it is the same model


### B5

- Claim IDs: C3
- Decision gate ID: G5
- Current evidence class: exploratory
- Requested evidence class: exploratory
- Inputs required: B4 crosswalk, matched-independent pairs only; B0 posterior for comparison
- Declared input snapshot paths: runs/B4/crosswalk.parquet; runs/B0/seed12345.nc
- Declared evaluator snapshot paths: ext/eci-public at e04929a
- Expected implementation entrypoint: runs/b5_eee_refit.py
- Expected command or notebook: `uv run --project runs python runs/b5_eee_refit.py`
- What to compute: build one row per (model group, benchmark) from the highest normalised independent score; apply Epoch's inclusion rule; fit with defaults; compare with B0 on shared models.
- Output artifacts to produce: runs/B5/eee_refit.json
- Auditor-facing checks: Spearman and interval intersection on shared models; models dropped by the inclusion rule
- Intended lineage relation: replication (different data source)
- Parent run ID or rationale: R005; opens only if G4 finds at least 15 benchmarks and 100 models meeting Epoch's inclusion rule
- Hidden information unavailable to the evaluated system: not applicable
- Failure, skip, null, timeout, and retry states to retain: as B0
- Idempotency and restart requirements: as B0
- Known blockers: anchor models may be missing from the EEE matrix; then report rank agreement only

### B6

- Claim IDs: C1
- Decision gate ID: G6
- Current evidence class: exploratory
- Requested evidence class: exploratory
- Inputs required: the zip (fit input for clip and anchor variants; raw files and metadata for inclusion and ceiling variants)
- Declared input snapshot paths: ext/epoch_zip/benchmark_data.zip
- Declared evaluator snapshot paths: ext/eci-public at e04929a; runs/lib/sens_metrics.py
- Expected implementation entrypoint: runs/b6_handling.py
- Expected command or notebook: `uv run --project runs python runs/b6_handling.py`
- What to compute: clip 1e-4 and 1e-2 on the fit input against P0; `prepare_benchmark_data(zip, min_mid_range_benchmarks_per_model=3 or 6)` and a metadata copy with every score_ceiling set to 1.0, each against a loader-input baseline fitted at B2 settings; anchor swap by re-anchoring P0's raw capability draws.
- Output artifacts to produce: runs/B6/handling.json
- Auditor-facing checks: S1-S4 per handling choice; models added or dropped
- Intended lineage relation: sensitivity
- Parent run ID or rationale: R003
- Hidden information unavailable to the evaluated system: not applicable
- Failure, skip, null, timeout, and retry states to retain: as B2
- Idempotency and restart requirements: one output per choice
- Known blockers: score_ceiling and inclusion changes go through prepare_benchmark_data arguments or a metadata DataFrame built under runs/, never by editing ext/
