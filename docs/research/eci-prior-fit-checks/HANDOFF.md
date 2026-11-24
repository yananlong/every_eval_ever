# Handoff: resuming the ECI prior and fit-check runs

This pack is everything needed to continue W3 and run W4 to W6 on another machine from git. Plan documents are in this directory; code is in `code/`; results so far are in `results/`.

## Resume here

**(a) Snapshot time.** Taken 2026-11-19 at about 16:54 UTC. The newest committed replicate file (`null_160.json`) was written at 16:53:43 UTC; `null_161.log` was created at 16:53:52 UTC. The original machine kept running W3 after this, so its own results may be ahead of this snapshot. This snapshot is what git holds.

**(b) Finished replicates in the snapshot.** 161 null replicates, indices 0 to 160, each with a `results/W/W3/rep/null_<i>.json`. No misfit replicate (`2d`, `offset`, `shape`, `disp`, `drift`) has started: 0 of 5 x 20.
- Converged: 155.
- Timed out at the 60-minute cap (recorded `timeout: true`, non-converged): null_40 (two ladder runs finished, 844 s and 856 s, then stopped) and null_158 (three runs finished, the last a 4,000-draw run of 2,410 s).
- Finished but not converged (convergence rule: 0 divergences, max R-hat <= 1.01, min ESS >= 400, after the whole draw ladder):
  - null_73: 3,774 divergences, R-hat 1.029, min ESS 132 (16,000-draw cold run, 1,210 s).
  - null_118: 3 divergences, R-hat 1.015, min ESS 309 (4,000-draw cold run, 362 s).
  - null_147: 1,484 divergences, R-hat 1.077, min ESS 39 (4,000-draw cold run, 2,641 s).
  - null_150: 1 divergence, R-hat 1.026, min ESS 158 (4,000-draw cold run, 553 s).
- Mid-run at snapshot time: **null_161** (a `.log` exists, no `.json`). It is not a result; it will be rerun from scratch with its deterministic seed. (The log is committed only as evidence; the rerun overwrites it.)
- Misfit counts so far: none. `results/W/W3/calibration.json` is stale (an interim summary of the first 13 nulls); `--summarise` rewrites it.

**(c) Queue order.** `w3_calibrate.py --stage` defaults to `pc,null,2d,offset,shape,disp,drift`. Within a stage replicates run in index order, one at a time, each in its own process with a 3,600 s cap. So: positive control (`pc`, done for seeds 12345, 22345, 32345; JSONs committed), then null 0 to 198 (199 planned), then `2d` 0 to 19, `offset` 0 to 19, `shape` 0 to 19, `disp` 0 to 19, `drift` 0 to 19 (5 x 20 = 100). **Next replicate: null_161**, then null_162, 163, ... 198. Remaining: 38 nulls (161 to 198) and 100 misfits.

**(d) Commands, from the repository root.**
```
git fetch origin research/consolidated-evidence-index && git merge --no-edit FETCH_HEAD   # or just check out the branch
bash docs/research/eci-prior-fit-checks/code/setup_workdir.sh eci_work    # work root eci_work/v11; clones Epoch's code, builds the venv
# put the two inputs that are not in git in place (see "Inputs outside git" below), then:
cd eci_work/v11
runs/.venv/bin/python runs/w3_resume.py 2>&1 | tee -a runs/logs/w3_resume.log
```
Skip logic (read from `w3_calibrate.py`, function `run_rep_capped`): a replicate is finished when `rep/<gen>_<r>.json` exists and either it has `timeout: true`, or its `code_sha256` equals the current code digest **and `rep/<gen>_<r>.nc` exists**. Any other case refits the replicate. The `.nc` files are not in git, so `w3_calibrate.py` itself would refit all 159 non-timeout replicates (about 3 minutes each or more, many hours). Workaround: the new `code/runs/w3_resume.py` imports `w3_calibrate` unchanged and replaces only that check, so a JSON with a matching code digest (or a timeout) counts as finished without its `.nc`. It runs the same stages in the same order and ends with `summarise`. The code digest covers Epoch's `bayesian.py` and our `ppc_checks.py`, `generators.py`, `sbc.py`, `fit_any.py`; if any differs from this snapshot's, every replicate is refitted, so keep Epoch's commit and the copied files exact. `w3_modrak.py` and `w3_resume` do need the W2 `.nc` (below); `w3_modrak.py` also needs the per-replicate `.nc` files, which are absent from git and are not recreated by `w3_resume.py` (see W4 below).

**(e) After W3 finishes.**
- **G1** is computed by `runs/w3_resume.py --summarise` (`calibration.json`, key `G1`): proceed only if coverage90 of the ECI across the converged nulls is in 0.85 to 0.95, at least 150 converged nulls, T2 power on `2d` and T5 power on `offset` each meet at least 16 of 20 rejections with at least 15 converged, and the positive control fails S1 to S4 in the frontier or all-model stratum on all 3 seeds. Stop if recovery is below 0.75. Rules in force: 60-minute cap per replicate, a timeout counts as non-converged and is excluded from the null reference, SBC and power; stop if more than 10 null replicates time out (currently 2); the summary also reports a censoring check comparing the truths of timed-out and converged nulls (Mann-Whitney). Currently 155 of 161 converge, so 150 converged nulls is already met.
- **W4 and the W3 rerun of the Modrak rank tests.** `runs/.venv/bin/python runs/w4_ppc.py` (Epoch's suite, T1 to T7 with max-T, five held-out folds, localisation), `runs/.venv/bin/python runs/w4_graphics.py`, and `runs/.venv/bin/python runs/w3_modrak.py` (add `--selftest` first; it takes `--w3`, `--w2`, `--out`, `--gens`). `w3_modrak.py` reads the `rep/*.nc` files. They are not in git. Either copy `results/W/EXCLUDED_FILES.tsv`-listed `.nc` files from the original machine (hashes there), or accept refitting each replicate (same seeds; NUTS output is not bit-identical across machines, so refitted draws will differ slightly from the committed T statistics and `u` ranks).
- Then **W5**, **W6** as in the run order below.

**(f) Seeds and RNG state.** There is no carried RNG state. Each replicate is independent: seed = first 4 bytes (big-endian integer) of `sha256("<gen>:<r>")` (`lib/generators.py: seed_of`); the pooled posterior draw it starts from is position `floor(r * S / R_g)` (S = pooled draws of `W/W2/seed12345.nc`, R_g = 199 for null, 20 per misfit generator); simulation uses `numpy.random.default_rng(seed)`; the NUTS call uses the same seed. Each JSON records `seed` and `position`; e.g. null_161 will use the seed and position the code computes, with no dependence on earlier replicates. Not pinned down: exact bit-for-bit NUTS reproduction on different hardware or BLAS builds (floating point differs, so a borderline replicate could change convergence status), and the exact value of S (it is the W2 file's chain x draw count; check the file). If the W2 `.nc` differs from the original (sha256 in `results/W/EXCLUDED_FILES.tsv`), the pooled draws differ and **all** null replicates must be refitted; do not mix.

## Environment setup

- Python 3.13.18 (`uv venv --python 3.13`), uv 0.11.32. `code/requirements.txt` is the pinned freeze (pymc 6.3.2, pytensor 3.3.2, arviz 1.3.0, numpy 2.5.3, scipy 1.18.1, pandas 3.0.5, xarray 2026.7.0, h5netcdf 1.8.3, netCDF4 1.7.5.1). Epoch's `eci` 0.2.0 is installed editable with `--no-deps` from the vendored copy (the freeze's editable line was removed because it held a local path). `results/env.json` records the same versions.
- Epoch's code: `https://github.com/epoch-research/eci-public.git`, commit `e04929ab751531e558b1a61e86f436487c710ef8` ("Merge pull request #16 from epoch-research/flat-priors", 2026-11-03). `ext/eci-public` is a clone at that commit; `runs/vendor/eci-public` is a copy without `.git` (identical file by file apart from bytecode caches; `vendor_tree_sha256` 781b5f93... in `results/freeze.json`). `setup_workdir.sh` does both. Epoch's code is not copied into this repository and must never be edited.
- Work root layout (built by `setup_workdir.sh`, untracked): `eci_work/v11/{runs,plan_src,ext}` and `eci_work/wt-pr14`, a symlink to the repository root. Every script uses paths relative to `eci_work/v11` (for example `runs/W/W3`), so run them from there. The symlink exists because the frozen `lib/freeze.py` locates the plan at `RUNS.parent.parent / "wt-pr14/docs/research/eci-prior-fit-checks"`.

### Inputs

1. `ext/epoch_zip/benchmark_data.zip`, sha256 `9d728f9f8635069812530a157aef7a6cec935fffc93f33d3031bad5c6888b1d5` (2.3 MB, downloaded from `https://epoch.ai/data/benchmark_data.zip` on 2026-11-13). **Now committed** at `inputs/benchmark_data.zip`; `setup_workdir.sh` copies it into place and checks the hash. Do not re-download: the live file may have changed.
2. `runs/W/W2/seed12345.nc` (210,605,531 bytes, sha256 `88ab45bbb8118f5ef7b0efb904e496268d69a22be470be73521416b290604162`). **On GitHub in five parts** on branch `claude/busy-wright-khj0ky` (commit `0829e6e`), under `eci-handoff/W2/`, with `SHA256SUMS`. `setup_workdir.sh` fetches, verifies and reassembles it. By hand: `git fetch origin claude/busy-wright-khj0ky && git archive FETCH_HEAD eci-handoff | tar -x`, then follow `eci-handoff/README.md`. Do not refit W2 with `runs/w2_fit.py`: different draws would invalidate every finished null; see (f). The `seed22345`/`seed32345` and F0 files are not transferred; W3 does not read them (list and hashes in `results/W/EXCLUDED_FILES.tsv`).

The `ext/eee` entries file (58 MB, manifest in `freeze.json`) is not read by the W-stage scripts.

## Stage status

| Stage | Status |
|---|---|
| W1 prior predictive (and W1J Jeffreys checks) | done; `results/W/W1/`, `results/W/W1J/` |
| W2 reproduction of Epoch's fit | done; `results/W/W2/` (three seeds) |
| WA anchor sensitivity | done; `results/W/WA/` |
| W3 calibration | partial: 161 of 199 nulls (155 converged, 2 timeouts, 4 non-converged), 0 of 100 misfit replicates, positive control done |
| W3M interim rank tests | interim only (22 nulls when run); rerun after W3 |
| W4 to W6 | pending |

## Run order

1. **W3**, then **G1** (above): at least 150 converged nulls, 60-minute cap per replicate with a timeout counted as non-converged, stop if more than 10 null timeouts, censoring check.
2. **W4** and the **`w3_modrak.py` rerun** (needs the `.nc` files, which are absent from git and must be copied or regenerated).
3. **W5** (`runs/w5_sensitivity.py`, then `w5j_fit.py --variant J1|J2` and `w5j_score.py`, J1 last). Every prior arm (P0, P0b, P1 to P10, X1, X2, PR, J) saves a thinned `.nc` containing the posterior and `log_likelihood`, written beside its `.npz`. Run the predictive checks (T1 to T7 on the real-data fit, ranked against the W3 null reference, labelled approximate for any non-Epoch prior) right after each arm's fit, then posterior SBC (`runs/w5_posterior_sbc.py`, optional) under that arm's prior. **Before launching any SBC refit, bring the per-arm fit counts and ETAs to the user.**
4. **W6** (`runs/w6_expand.py`, which calls `runs/w6_fit_one.py` per fit with its 60-minute cap).

`results/deviations.md` lists every departure from the plan to date (sampler, positions, 60-minute cap, outage, R26 to R30); read it before changing any script.

## Rules

- Frozen files are never altered: `code/runs/lib/{sbc,ppc_checks,sens_metrics,models,compare,freeze}.py`, plus `strata.json` and the grid digest in `results/freeze.json`. They were copied byte for byte (hashes in `results/freeze.json`). New code goes in new files (as `w3_resume.py` does).
- Path assumptions in frozen files that were left as they are: `lib/freeze.py` uses `RUNS.parent.parent / "wt-pr14/..."` (hence the symlink); `lib/sens_metrics.py` defaults `strata_from` to the cwd-relative `runs/strata.json`. No file in the pack contains an absolute path.
- Do not run PyMC or NUTS fits on a machine concurrently with another fit unless it has the cores and memory (each fit uses 4 chains). Sort fits sequentially.
- Commits are authored as Yanan Long <yanan.long439@gmail.com> and carry no AI attribution lines (no `Co-Authored-By`, no session trailer).
- Never commit `.nc`, `.pkl`, `.npz`, `.venv`, logs over 1 MB, or any file over about 5 MB.

## What is in the pack, and what is excluded

- `code/runs/*.py` (22 drivers and `w3_resume.py`), `code/runs/lib/`, `code/runs/strata.json`, `code/plan_src/gen_json*.py` (plan generators; `gen_json_w.pre-modrak.bak` omitted), `code/tools/truth_npz_json.py`, `code/setup_workdir.sh`, `code/requirements.txt`.
- `results/W/W3/`: `rep/null_<i>.json` and `.log` (161 JSON, 122 logs), `truth/null_<i>.json` (161; the truth draws as JSON, converted from `.npz` and checked to round-trip exactly; `setup_workdir.sh` converts them back), `pc_seed*.json`, `calibration.json` (stale, see above).
- Excluded, with sizes and sha256 in `results/W/EXCLUDED_FILES.tsv` (172 files, about 1.16 GB): 159 `rep/null_*.nc` (1.57 MB each, about 250 MB total), 3 `pc_seed*.npz` (3.55 MB each, regenerable summary of the positive-control ECIs), the W2 files (`seed*.nc` 211 MB each, `f0_seed*.nc` 118 MB each, `loader_input.nc` 26 MB, three `*_evaluation.pkl` of 0.4 MB), `W3M/ranks_null.npz` (94 KB; derived), `.venv` (608 MB), `ext/` (66 MB), `runs/vendor/`. The 161 `truth/*.npz` (5 KB each) were committed as JSON instead.
