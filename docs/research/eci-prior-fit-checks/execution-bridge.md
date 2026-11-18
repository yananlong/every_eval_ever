# Execution Bridge

This file tells an engineer what to build and run. Formulas and rules are in the "Methods Specification" section of experiment-plan.md (M1 to M14); block fields are in run-blocks.json.

## Setup (once, before W1 and W2)

Working directory for every command: the project root (`v11/` in the original layout; any directory works). External inputs live under `ext/` and are read-only; our code and outputs live under `runs/`. No interpreter is started with its working directory inside `ext/`.

1. Check input digests: `ext/epoch_zip/benchmark_data.zip` sha256 `9d728f9f8635069812530a157aef7a6cec935fffc93f33d3031bad5c6888b1d5`; `ext/eee/entries.jsonl` sha256 `98e5f48af77952d478013cf578ca00ecd17e5e41f7a647bbc80e8e37b2b120fe`; `ext/eci-public` at git `e04929ab751531e558b1a61e86f436487c710ef8`.
2. Copy `ext/eci-public` (without `.git`) to `runs/vendor/eci-public` and confirm the copy is identical file by file. Install from the copy so that no build step writes under `ext/`.
3. Create the uv project `runs/` (Python >= 3.12; the machine has 3.13) with dependencies: the vendored `eci` package as a path dependency, and pymc (>= 6.0), pytensor, arviz (>= 1.0), numpy, scipy, pandas, matplotlib at the versions in `ext/eci-public/uv.lock`, plus pyarrow. Save `uv pip freeze` to `runs/env.lock.txt`. This step needs network access.
4. Write `runs/strata.json` (M2) from the published files and `runs/freeze.json` with the digests above.
5. Smoke test: `uv run --project runs python -c "import eci, pymc, arviz; print(pymc.__version__, arviz.__version__)"`.

Shared library `runs/lib/`: `data.py` (read members of the zip with `zipfile`; never from an extracted copy), `fit.py` (wrapper around `fit_bayesian_eci` with the sidecar and skip logic), `models.py` (our PyMC implementations of the base model F0, the reference prior PR and the expansions F1-F7, with our own NUTS call and convergence ladder; M12 and M14; it imports Epoch's module only for constants and never patches it), `anchored.py` (M1), `sens_metrics.py` (M3), `variants.py` (P8-P10 builders and the context manager that swaps `eci.bayesian.build_bayesian_model`, `_FREE_VARS` and `_DIAGNOSTIC_VARS` in memory), `generators.py` (M4), `sbc.py` (M13), `ppc_checks.py` (M5, M6), `compare.py` (PSIS-LOO, K-fold, the W6 rule and the multiverse summary; M14), `predict.py` (M8).

Facts about Epoch's code that the wrapper relies on (checked at e04929a):

- `fit_bayesian_eci(df, priors, performance_clip_eps=1e-3, draws=None, tune=None, chains=4, target_accept=0.95, random_seed=12345, evaluate=False, ...)` returns `(eci_df, edi_df, draws)`; `draws["eci"]` is the per-draw anchored ECI (draws x models, in `draws["model_names"]` order), `draws["trace"]` the full trace, `draws["attempts"]` and `draws["started_from"]` the sampler history, and `draws["evaluation"]` the diagnostic tables when `evaluate=True`.
- `df` needs columns `model_id`, `benchmark_id`, `performance`, `benchmark`, `Model`. The published fit input has them.
- `draws=None` means adaptive (1,000 up to 16,000 per chain in the dense stage); an integer fixes every run at that size.
- `evaluate=True` adds `log_likelihood` and `posterior_predictive` groups (each draws x 2,879 values). It does not store a log prior.
- Convergence failures are warnings. The wrapper must read `draws["attempts"][-1]` and record pass or fail itself.
- Epoch's dense-mass-matrix code looks up draws by the names in `eci.bayesian._FREE_VARS`; a model variant with different free variables fails with a KeyError unless that tuple is replaced for the duration of the fit.

Resource notes for 4 CPUs and 15 GB RAM: every fit runs 4 chains on 4 cores, so run fits one at a time. Memory per fit is under 2 GB (the largest arrays are the two draws x 2,879 groups under `evaluate=True`: about 0.2 GB at 4,000 total draws). Disk: about 1 GB for W2 to W5, about 1.5 GB more for the W6 candidates' log-likelihood groups, and about 2.5 GB for the EEE objects.

## Block Hand-off

### W

- Claim IDs: C1, C2 (W1 and W6 test no registered claim)
- Decision gate ID: G0 (W2), G1 (W3), G3 (W4), G2 (W5), G7 (W6); W1 has no gate
- Current evidence class: exploratory
- Requested evidence class: confirmatory for W4 (C2) and W5 (C1); exploratory for W1, W2, W3 and W6, the PR entry and the targeted refits of W5
- Inputs required: the zip of 2026-11-13: members `epoch_capabilities_index/processed_data_for_eci.csv` (fit input), `eci_scores.csv`, `edi_scores.csv`, `eci_bootstraps.json` (published results); `experiment-plan/prior-grid.json`
- Declared input snapshot paths: ext/epoch_zip/benchmark_data.zip (sha256 at start)
- Declared evaluator snapshot paths: ext/eci-public at git e04929ab751531e558b1a61e86f436487c710ef8; runs/lib/ppc_checks.py; runs/lib/sens_metrics.py; runs/lib/sbc.py; runs/lib/compare.py; runs/lib/models.py; experiment-plan/prior-grid.json (digests in runs/freeze.json at the points M10 gives)
- Expected implementation entrypoint: runs/w_run.py (calls the stage entrypoints below; stops at a failed gate)
- Expected command or notebook: `uv run --project runs python runs/w_run.py --stage all`, or one stage at a time as below
- What to compute: the six stages below, in the order of the stage table: W1 and W2 first, then W3, then W4 and W5, then W6.
- Output artifacts to produce: runs/W/workflow.json (rebuilt from the stage summaries), and the stage outputs below under runs/W/W1 to runs/W/W6
- Auditor-facing checks: every G0 criterion, EQ item, G1 criterion and SBC flag with its value; the C1 and C2 verdict inputs; for W6 every candidate's elpd, estimator used and status
- Intended lineage relation: baseline (W2, W4a to W4c), negative_control and sensitivity (W3), ablation (W4d), parameter_variation (W5), alternative_hypothesis (W6)
- Parent run ID or rationale: none (root); stage dependencies are in the stage table and in the tracker
- Hidden information unavailable to the evaluated system: true simulation parameters in runs/W/W3/truth/, never read by ppc_checks.py; held-out scores removed before each fold fit; the C1 and C2 verdict files digested before W6 computes any elpd
- Failure, skip, null, timeout, and retry states to retain: sampler stage, attempts and warnings for every fit (Epoch's ladder, or ours for models.py fits); non-converged replicates, grid entries and candidates counted and shown, never dropped; a W6 candidate that fails its fallback is "not fitted"
- Idempotency and restart requirements: every fit writes its .nc and sidecar atomically and is skipped on restart only if the sidecar's input digest, code digest, seed and arguments match (M10); replicate seed = first 4 bytes of sha256("<generator>:<index>") as a big-endian integer; summary files are rebuilt from the sidecars on every run
- Known blockers: the environment is not built yet (PyMC install needs network); the netCDF round-trip of an arviz 1.x DataTree should be tested on the first trace before the other seeds run; `models.py` must be written and frozen before the first EQ fit

#### W1. Prior predictive check

- Depends on: none
- Entrypoint and command: runs/w1_prior_predictive.py; `uv run --project runs python runs/w1_prior_predictive.py`
- What to compute: M11. 1,000 datasets from Epoch's priors and 1,000 from PR on the 2,879 cells (streams from `SeedSequence(20261113).spawn(2)`); per dataset the share at the clip bounds and in $[0.1, 0.9]$; the PR criterion; the cell-level shares of $\mu$ and of $\lvert a(c - d)\rvert > 6.9$.
- Output artifacts to produce: runs/W/W1/prior_predictive.json, runs/W/W1/fig_prior_predictive.png
- Auditor-facing checks: Epoch's priors reproduce 0.89 and 0.05 within 0.01; the three PR criterion values; PR pass or fail
- Intended lineage relation: baseline
- Restart notes: pure numpy; reruns from scratch in minutes

#### W2. Fit and reproduction

- Depends on: none
- Entrypoint and command: runs/w2_fit.py; `uv run --project runs python runs/w2_fit.py`
- What to compute: (1) W2a: fit the published fit input with defaults and `evaluate=True` for seeds 12345, 22345, 32345. (2) Add to each trace the summed log density of the three hyperpriors per draw (group `log_prior`) and the per-draw ECI. (3) Against `eci_scores.csv`, seed 12345: $d_m$, $d_m / W_m$, Spearman, width ratio; against `edi_scores.csv`: max abs difference of `edi` and `estimated_slope_scaled`; against `eci_bootstraps.json`: the nine top-10 adjacent-pair probabilities, ours and published. (4) Per seed: Epoch's `sampler_summary` row and `attempts`. (5) Seed-to-seed SD of posterior-mean ECI per model. (6) W2b: fit `prepare_benchmark_data(zip)` with seed 12345, list the rows that differ from the published input, and score S1-S4 against W2a. (7) EQ (M12): the density check at 20 draws; F0 from `models.py` fitted with seeds 12345 and 22345 through our sampler call, saved with its log-likelihood; the fit and elpd_loo comparisons with W2a.
- Output artifacts to produce: runs/W/W2/reproduction.json, runs/W/W2/seed{12345,22345,32345}.nc with sidecars, runs/W/W2/loader_input.nc with sidecar, runs/W/W2/f0_seed{12345,22345}.nc with sidecars
- Auditor-facing checks: every G0 criterion with its value; per-seed diagnostics; the three differing rows in W2b; every EQ item with its value
- Intended lineage relation: baseline
- Restart notes: Epoch's draw ladder is the only retry, plus one rerun at target_accept 0.99 if G0 asks for it; one repair and rerun of EQ

#### W3. Computational and check calibration

- Depends on: W2
- Entrypoint and command: runs/w3_calibrate.py; `uv run --project runs python runs/w3_calibrate.py --stage pc,null,2d,offset,shape,disp,drift`
- What to compute: (1) positive control: refit real data with $\tau_\alpha \sim \operatorname{LogNormal}(\ln 0.05, 0.1)$ on 3 seeds and score S1-S4 against the W2 fit of the same seed. (2) For each of 199 G-null replicates: simulate, fit, test convergence, compute T1-T7, the recovery indicators and the SBC ranks (M13). (3) For each of 5 misfit generators x 20 replicates: simulate, fit, compute T1-T7 and the max-T adjusted p of the targeted check against the null reference. (4) Summarise: recovery coverage overall and by stratum; SBC Test 1 and Test 2 and the SBC verdict; the rank histograms of the descriptive parameters; the null reference table; power per generator with its Clopper-Pearson interval; non-converged counts.
- Output artifacts to produce: runs/W/W3/calibration.json; runs/W/W3/rep/<generator>_<index>.json and .nc (400 thinned draws); runs/W/W3/truth/<generator>_<index>.npz
- Auditor-facing checks: recovery coverage by stratum; SBC flags and pooled coverage; power per check; number of converged null replicates; positive-control S1-S4 per seed
- Intended lineage relation: negative_control (G-null), sensitivity (misfit generators and positive-control prior)
- Restart notes: about 10 hours of sampling; run the positive control first so G1's branch (b) is known early; a finished replicate is skipped if its sidecar matches

#### W4. Posterior predictive and LOO-PIT checks

- Depends on: W2, W3
- Entrypoint and command: runs/w4_ppc.py; `uv run --project runs python runs/w4_ppc.py`
- What to compute: (W4a) write Epoch's report with `save_evaluation` and copy its metrics table into ppc.json. (W4b) T1-T7 on the real data; unadjusted, max-T adjusted and raw p-values. (W4c) write folds.csv, fit 5 folds, compute PIT per held-out row, overall coverage with bootstrap interval, per-benchmark binomial tests; keep each fold's held-out row-wise log predictive density for W6. (W4d) only if something is rejected or flagged: build $F$, run the deletion test, refit without $F$, compute relative shifts. Then assign the C2 verdict.
- Output artifacts to produce: runs/W/W4/ppc.json, runs/W/W4/evaluation_report.pdf (Epoch's own report), runs/W/W4/folds.csv, runs/W/W4/fold{0..4}.nc with sidecars, runs/W/W4/fig_checks.png
- Auditor-facing checks: the three p-values per check; power label per check; held-out coverage table; $F$ and the W4d shifts if run
- Intended lineage relation: baseline (W4a to W4c), ablation (W4d)
- Restart notes: fold fits keyed by fold index and the digest of folds.csv; needs at least 150 converged null replicates from W3

#### W5. Prior sensitivity

- Depends on: W1, W2, W3
- Entrypoint and command: runs/w5_sensitivity.py; `uv run --project runs python runs/w5_sensitivity.py`
- What to compute: (1) S5 screen on the W2 seed-12345 draws (and, as a Monte Carlo check, on P0's draws once P0 exists); flag hyperpriors. (2) Fit P0 (seed 12345) and P0b (seed 22345) with default priors and draws=4000; compute the noise floor and apply the doubling rule of M3 if it fails. (3) Fit P1-P10, X1, X2 with draws=4000 and seed 12345; score S1-S4 per stratum against P0. (4) Fit PR through `models.py` (only if PR passed W1 and EQ passed), save its log-likelihood, and score it as an exploratory entry. (5) If S5 flagged a hyperprior: the two power-scaled refits at 0.8 and 1.25 (C1 rule) and the exploratory refits at 0.5 and 2 (at most 6 in all). (6) Assign the C1 verdict by the decision rule, then write the exploratory interpretation separately.
- Output artifacts to produce: runs/W/W5/sensitivity.json, runs/W/W5/fig_sensitivity.png, runs/W/W5/<entry>.nc (posterior group only; PR with its log-likelihood) with sidecars
- Auditor-facing checks: S1-S5 per prior and stratum beside the noise floor; the psens table; $P(\text{in top 10})$ per prior; convergence status of every entry; exploratory entries in a separate table
- Intended lineage relation: sensitivity
- Restart notes: an entry that fails Epoch's checks is retried once with draws doubled, then recorded as unresolved; one .nc and sidecar per entry. P8-P10 need model variants supplied at run time by runs/lib/variants.py (see Setup); P9 may need a non-centred parameterisation; confirm the arviz `psens` signature against the pinned version

#### W6. Model expansion and comparison

- Depends on: W1, W2, W3, W4, W5; refuses to start unless `runs/freeze.json` holds the digests of the C1 and C2 verdict files and of `compare.py` and `models.py`
- Entrypoint and command: runs/w6_expand.py; `uv run --project runs python runs/w6_expand.py`
- What to compute: M14. (1) Fit F1-F5 on the real data with `models.py`; reuse F0 (EQ seed 12345) and F6 (W5's PR fit). (2) PSIS-LOO elpd and SE of the difference to F0, and the Pareto-k share over 0.7. (3) For each pair over the 2% trigger, K-fold on `runs/W/W4/folds.csv` (F0's fold fits come from W4; refit the candidate with seed 12345 + fold). (4) Apply the preference rule. (5) For each preferred expansion: convergence checks and the reduced SBC. (6) If two or more single expansions are adopted: F7 once, by the same steps. (7) The adequate set, and S1-S4, S2 and S3 shares, $P(\text{in top 10})$ and per-model shifts of ECI under F0 and each adequate model, per stratum. F1 follows its fallback on sampler failure.
- Output artifacts to produce: runs/W/W6/expansion.json, runs/W/W6/<candidate>.nc with sidecars, runs/W/W6/sbc/<candidate>_<index>.json for the reduced SBC replicates, runs/W/W6/fig_multiverse.png
- Auditor-facing checks: every candidate with its elpd, SE, estimator, Pareto-k share, convergence, SBC result and status (not preferred, preferred not adopted, adopted, not fitted); the adequate set; the F1 fallback step used
- Intended lineage relation: alternative_hypothesis
- Restart notes: restartable per fit; may be stopped between candidates; no step may be added or repeated beyond M14's two allowed iterations

### B4

- Claim IDs: C3
- Decision gate ID: G4
- Current evidence class: exploratory
- Requested evidence class: exploratory
- Inputs required: EEE manifest dd7efcff entries.jsonl; all aggregate objects it lists; Epoch benchmark_metadata.csv, model_metadata.csv and the fit input; for stage b, the W2 seed-12345 trace (and, for the exploratory add-on, runs/W/W6/expansion.json and the adequate models' traces)
- Declared input snapshot paths: ext/eee/entries.jsonl (sha256 98e5f48a...); downloaded objects under runs/B4/objects/ verified against the manifest sha256; ext/epoch_zip/benchmark_data.zip; runs/W/W2/seed12345.nc (stage b); runs/W/W6/expansion.json (stage b, add-on)
- Declared evaluator snapshot paths: runs/B4/benchmark_map.csv, runs/B4/model_map.csv and runs/B4/source_class.csv (digests at freeze)
- Expected implementation entrypoint: runs/b4_run.py (stages implemented in runs/b4_crosswalk.py and runs/b4_transfer.py)
- Expected command or notebook: `uv run --project runs python runs/b4_run.py --stage a`, then the manual mapping and audit, then `uv run --project runs python runs/b4_run.py --stage b`; `--stage all` runs both and stops after stage a if the maps are not frozen
- What to compute: stage a follows M9 steps 1 to 8; stage b computes the same-upstream control, PIT and coverage, agreement and bias as in M9 on Epoch's base model, then assigns the C3 verdict; then, if W6 has adequate expansions, the same coverage under each (exploratory, reported beside the verdict).
- Output artifacts to produce: runs/B4/collection_screen.csv, runs/B4/crosswalk.parquet (one row per EEE result with its class), runs/B4/pairs.parquet, runs/B4/audit_sample.csv, runs/B4/transfer.json
- Auditor-facing checks: counts by class and exclusion reason; audit errors with the Clopper-Pearson bound; same-upstream differences; coverage with bootstrap interval and the two sensitivity cuts; EEE-vs-EEE agreement and its number of source pairs; the exploratory coverage under each adequate expansion, labelled as such
- Intended lineage relation: baseline
- Parent run ID or rationale: R002 for predictions (R006 for the add-on)
- Hidden information unavailable to the evaluated system: ECI predictions are not loaded in stage a; stage b refuses to run unless the map digests match runs/freeze.json
- Failure, skip, null, timeout, and retry states to retain: failed downloads listed and retried; every EEE result classified into exactly one class
- Idempotency and restart requirements: object cache keyed by sha256, files already present and verified are not fetched again; crosswalk and transfer outputs rebuilt from the cache and the frozen maps
- Known blockers: none for location: objects are fetched from the Hugging Face dataset `evaleval/EEE_datastore` at the `object_path` listed in manifest dd7efcff (`flat/manifests/sha256_dd7efcff.../entries.jsonl`), and each download is checked against its manifest sha256, so the pin is by content, not by repo revision; the benchmark map and the review of ambiguous models are manual; Epoch's model groups combine several versions, so an EEE record maps to a group only when model_metadata.csv lists that version or the reviewer records why it is the same model; the add-on needs a prediction function per expansion in `predict.py` (M8 generalised to the candidate's $\mu$ and noise)

### B5

- Claim IDs: C3
- Decision gate ID: G5
- Current evidence class: exploratory
- Requested evidence class: exploratory
- Inputs required: B4 crosswalk, matched-independent pairs only; W2 posterior for comparison
- Declared input snapshot paths: runs/B4/crosswalk.parquet; runs/W/W2/seed12345.nc
- Declared evaluator snapshot paths: ext/eci-public at e04929a
- Expected implementation entrypoint: runs/b5_eee_refit.py
- Expected command or notebook: `uv run --project runs python runs/b5_eee_refit.py`
- What to compute: build one row per (model group, benchmark) from the highest normalised independent score; apply Epoch's inclusion rule; fit with defaults; compare with W2 on shared models; if W6 adopted an expansion, fit the best adopted one on the same matrix once more (exploratory) and report it beside.
- Output artifacts to produce: runs/B5/eee_refit.json
- Auditor-facing checks: Spearman and interval intersection on shared models; models dropped by the inclusion rule
- Intended lineage relation: replication (different data source)
- Parent run ID or rationale: R007; opens only if G4 finds at least 15 benchmarks and 100 models meeting Epoch's inclusion rule
- Hidden information unavailable to the evaluated system: not applicable
- Failure, skip, null, timeout, and retry states to retain: as W2
- Idempotency and restart requirements: as W2
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
- What to compute: clip 1e-4 and 1e-2 on the fit input against P0; `prepare_benchmark_data(zip, min_mid_range_benchmarks_per_model=3 or 6)` and a metadata copy with every score_ceiling set to 1.0, each against a loader-input baseline fitted at W5 settings; anchor swap by re-anchoring P0's raw capability draws.
- Output artifacts to produce: runs/B6/handling.json
- Auditor-facing checks: S1-S4 per handling choice; models added or dropped
- Intended lineage relation: sensitivity
- Parent run ID or rationale: R005
- Hidden information unavailable to the evaluated system: not applicable
- Failure, skip, null, timeout, and retry states to retain: as W5
- Idempotency and restart requirements: one output per choice
- Known blockers: score_ceiling and inclusion changes go through prepare_benchmark_data arguments or a metadata DataFrame built under runs/, never by editing ext/
