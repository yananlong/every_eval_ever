"""ECI under the augmented-input fits against P0 (Epoch data, runs/W/W2/seed12345.nc): M3 metrics S1-S4 per
stratum (runs/lib/sens_metrics.py, unchanged), shifts in points, top 10, and the cell model's parameters.
Posterior draws come from az.extract and intervals from az.eti (90%, equal-tailed, as before); convergence from
az.rhat and az.ess. Usage: aug_compare.py [W7 fit names to add from runs/W/W7]"""
import sys, json
from pathlib import Path
sys.path[:0] = ["runs/vendor/eci-public/src", "runs"]
import numpy as np, pandas as pd, xarray as xr, arviz as az
from lib import fit as fitmod, sens_metrics as sm

OUT = Path("runs/AUG")
e0, names, t0 = fitmod.load_eci("runs/W/W2/seed12345.nc")
st = sm.strata_from(); strata = {k: np.array([n in set(st[k]) for n in names]) for k in ("all", "frontier", "sparse", "dense")}
anchor = np.array([n in sm.ANCHORS for n in names]); s0 = sm.summarise(e0)
sig0 = az.extract(t0, var_names="sigma").mean("sample").to_numpy()
eti90 = lambda da: [float(x) for x in az.eti(da, prob=0.9, dim="sample").to_numpy()]
res = {}
FITS = [(OUT, n) for n in ("AUG_base_all", "AUG_base_ind", "AUG_mean_all", "AUG_mean_ind", "AUG_cell_all_ta99", "AUG_cell_ind_ta99")]
FITS += [(Path("runs/W/W7"), n) for n in sys.argv[1:]]
for folder, name in FITS:
    js = folder / f"{name}.json"
    if not js.exists(): continue
    side = json.loads(js.read_text())
    ek, nk, tk = fitmod.load_eci(folder / f"{name}.nc"); assert nk == names
    sc = sm.score(ek, e0, names, strata); sk = sm.summarise(ek)
    d = sk["mean"] - s0["mean"]; d[anchor] = 0
    fr = strata["frontier"] & ~anchor
    order = np.argsort(-np.abs(d))[:8]
    post = tk["posterior"]
    hv = [v for v in ("tau_alpha", "sigma_median", "tau_sigma", "sigma", "capability", "difficulty", "slope", "tau_u", "tau_delta", "tau_fam", "tau_l", "tau_g") if v in post]
    r = dict(converged=side["converged"], last_attempt=side["last_attempt"], wall_seconds=side["wall_seconds"],
             S={k: {kk: v[kk] for kk in ("n", "S1", "S2_count", "S2_limit", "S3_count", "max_rel_shift", "median_width_ratio")} for k, v in sc.items() if k != "S4"},
             S4=dict(top10_same=sc["S4"]["top10_same"], max_pair_change=sc["S4"]["max_pair_change"]),
             frontier_max_abs_shift=float(np.abs(d[fr]).max()), median_abs_shift=float(np.median(np.abs(d[~anchor]))),
             largest_movers=[dict(model=names[i], p0=float(s0["mean"][i]), shift=float(d[i]), p0_width=float(s0["width"][i])) for i in order],
             top10=[names[i] for i in np.argsort(-sk["mean"])[:10]],
             sigma_median_ratio=float(np.median(az.extract(tk, var_names="sigma").mean("sample").to_numpy() / sig0)),
             max_rhat=float(az.rhat(tk, var_names=hv).to_dataset().to_dataarray().max()),
             min_ess_bulk=float(az.ess(tk, var_names=hv).to_dataset().to_dataarray().min()),
             divergences=int(tk["sample_stats"]["diverging"].to_numpy().sum()))
    if "tau_u" in post:
        tu = az.extract(tk, var_names="tau_u"); lo, hi = eti90(tu)
        r["tau_u"] = [lo, float(np.median(tu.to_numpy())), hi]
    if "beta_src" in post:
        b = az.extract(tk, var_names="beta_src"); r["beta_src"] = {}
        for j, c in enumerate(["independent", "upstream-unknown"]):
            bj = b.isel({b.dims[0]: j}); lo, hi = eti90(bj); r["beta_src"][c] = [lo, float(np.median(bj.to_numpy())), hi]
    res[name] = r
json.dump(res, open(OUT / "compare.json" if len(sys.argv) == 1 else Path("runs/W/W7") / "aug_compare.json", "w"), indent=1)
for k, r in res.items():
    print("==", k, r["converged"], r["last_attempt"]["stage"], r["wall_seconds"])
    for s, v in r["S"].items(): print("  ", s, v)
    print("  S4", r["S4"], "frontier max", round(r["frontier_max_abs_shift"], 2), "median", round(r["median_abs_shift"], 2), "sigma ratio", round(r["sigma_median_ratio"], 3))
    print("  ", [(m["model"], round(m["p0"], 1), round(m["shift"], 2)) for m in r["largest_movers"]])
    if "tau_u" in r: print("   tau_u", r["tau_u"], "beta", r["beta_src"])
