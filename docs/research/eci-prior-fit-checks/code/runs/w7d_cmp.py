"""Compare the W7 follow-up candidates (runs/w7d_fit.py outputs in runs/W/W7/diag/) with G3_ta99 and F0.
PSIS-LOO deltas are paired sums with SE (lib/compare.paired). Three scales:
  native    az.loo pointwise elpd as fitted: valid only between models with the same likelihood form (no `bnd`);
  common    interior rows keep their density, rows at a bound use the log LOO predictive mass at that bound (for
            F0 and G3 the PSIS-weighted Beta mass beyond the clip, az.loo_expectations); valid for all pairs;
  interior  the common scale restricted to the 2,798 rows strictly inside (0.001, 0.999).
Also tabulates T1-T7, Pareto k, the largest components, the learned item counts against Epoch's item counts, and
ECI movement against G3_ta99 when the candidate's .npz is supplied on stdin (optional).
Usage: w7d_cmp.py NAME [NAME ...]"""
import sys, json, io, zipfile, warnings
sys.path[:0] = ["runs/vendor/eci-public/src", "runs"]; warnings.filterwarnings("ignore")
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np, pandas as pd, xarray as xr, arviz as az
import w7d_models as wd, w7d_common as c, w7_data
from lib import data, compare, ppc_checks as ppc

DIAG = c.DIAG; names = sys.argv[1:]
df, ex = w7_data.load("orig"); ex["clusters"] = None
y = np.clip(df["performance"].to_numpy(float), wd.EPS, 1 - wd.EPS); is0, is1 = y <= wd.EPS, y >= 1 - wd.EPS; bnd = is0 | is1
el = ppc.Elig(df, data.read_member(data.SCORES)); bn = el.bench_names


def base(nc, feats):
    """Native and common-measure pointwise elpd, Pareto k, for a fit stored as .nc without `bnd`."""
    t = xr.open_datatree(nc); post = t["posterior"]; C, Dn = post.sizes["chain"], post.sizes["draw"]
    loo = az.loo(t, pointwise=True, var_name="obs"); e = np.asarray(loo.elpd_i).ravel(); k = np.asarray(loo.pareto_k).ravel()
    VN = wd.var_names(feats); ds = az.extract(t, var_names=VN, combined=True)
    P = {v: ds[v].transpose("sample", ...).to_numpy() for v in VN}
    rows = np.where(bnd)[0]; sub = df.iloc[rows].reset_index(drop=True)
    # predict needs the full frame's indexing, so compute on all rows in chunks and keep the boundary rows
    m0 = np.empty((C * Dn, len(rows))); m1 = np.empty_like(m0)
    for i in range(0, C * Dn, 500):
        pr = wd.predict(feats, {v: x[i:i + 500] for v, x in P.items()}, df, ex)
        a, b = wd.bound_mass({kk: vv[:, rows] for kk, vv in pr.items()}); m0[i:i + 500], m1[i:i + 500] = a, b
    g = np.where(is0[rows][None], m0, m1).reshape(C, Dn, len(rows))
    dt = xr.DataTree.from_dict({"posterior": post.to_dataset()[["tau_alpha"]], "log_likelihood": t["log_likelihood"].to_dataset().isel(obs_dim_0=rows),
                                "posterior_predictive": xr.Dataset({"obs": (("chain", "draw", "obs_dim_0"), g)},
                                                                   coords={"chain": post["chain"].to_numpy(), "draw": post["draw"].to_numpy(), "obs_dim_0": rows})})
    em, _ = az.loo_expectations(dt, var_name="obs", kind="mean")
    ec = e.copy(); ec[rows] = np.log(np.asarray(em).ravel())
    return dict(elpd=e, common=ec, k=k)


cache = DIAG / "base_pointwise.csv"
if cache.exists():
    bp = pd.read_csv(cache)
else:
    g3 = base("runs/W/W7/G3_ta99.nc", ("dev", "fam")); f0 = base("runs/W/W2/f0_seed12345.nc", ())
    bp = pd.DataFrame(dict(G3_elpd=g3["elpd"], G3_common=g3["common"], G3_k=g3["k"], F0_elpd=f0["elpd"], F0_common=f0["common"], F0_k=f0["k"]))
    bp.to_csv(cache, index=False, float_format="%.5f")
pair = lambda a_, b_, m=None: dict(zip(("delta", "se"), compare.paired(np.asarray(a_)[m] if m is not None else a_, np.asarray(b_)[m] if m is not None else b_)))
res = dict(rows=len(y), interior_rows=int((~bnd).sum()), bound_rows=int(bnd.sum()),
           G3_vs_F0=dict(native=pair(bp.G3_elpd, bp.F0_elpd), common=pair(bp.G3_common, bp.F0_common), interior=pair(bp.G3_common, bp.F0_common, ~bnd),
                         bound_rows_sum=[float(bp.G3_common[bnd].sum()), float(bp.F0_common[bnd].sum())], k_share=float((bp.G3_k > .7).mean())),
           candidates={})
g3ppc = json.loads(Path("runs/W/W7/G3_ta99_ppc.json").read_text())
tab = [dict(fit="G3_ta99", converged=True, **{k: round(v, 3) for k, v in g3ppc["T"].items()}, k_share=round(float((bp.G3_k > .7).mean()), 3))]
perb = {}
for n in names:
    js = DIAG / f"{n}.json"
    if not js.exists(): res["candidates"][n] = dict(status="no result file (cap, crash or still running)"); continue
    o = json.loads(js.read_text()); pw = pd.read_csv(DIAG / f"{n}_pointwise.csv"); has_bnd = wd.has_bnd(o["features"])
    d = dict(features=o["features"], clusters=bool(o["clusters"]), target_accept=o["target_accept"], converged=o["converged"], started_from=o["started_from"],
             attempts=o["attempts"], wall_seconds=o["wall_seconds"], convergence={k: o["convergence"][k] for k in ("divergences", "max_rhat", "min_ess_bulk", "min_ess_tail")},
             T=o["T"], bounds=o["bounds"], loo=o["loo"], pit=o["pit"],
             vs_G3=dict(native=pair(pw.elpd, bp.G3_elpd) if not has_bnd else "not comparable (mass against density on rows at a bound)",
                        common=pair(pw.elpd_common, bp.G3_common), interior=pair(pw.elpd_common, bp.G3_common, ~bnd),
                        bound_rows_sum=[float(pw.elpd_common[bnd].sum()), float(bp.G3_common[bnd].sum())]),
             vs_F0=dict(common=pair(pw.elpd_common, bp.F0_common), interior=pair(pw.elpd_common, bp.F0_common, ~bnd)),
             k=dict(share_gt_0_7=float((pw.k > .7).mean()), n_gt_0_7=int((pw.k > .7).sum()), n_gt_1=int((pw.k > 1).sum()), share_gt_0_7_interior=float((pw.k[~bnd] > .7).mean())),
             T1_top=o["T1_top"][:5], T2_top=o["T2_top"][:6], T6_top=o["T6_top"][:5], T5_top=o["T5_top"][:3], T2_extras=o["T2_extras"], hyper={k: [round(v["mean"], 4), round(v["sd"], 4)] for k, v in o["hyper_summary"].items()})
    d["preferred_over_G3_common"] = bool(compare.preferred(d["vs_G3"]["common"]["delta"], d["vs_G3"]["common"]["se"]))
    if has_bnd:
        zf = zipfile.ZipFile(data.ZIP); it = []
        for b_, mem in c.INTERNAL.items():
            if b_ not in o["n_items"]: continue
            raw = pd.read_csv(io.BytesIO(zf.read(mem)))
            ni = (raw["mean_score"] * (1 - raw["mean_score"]) / raw["stderr"] ** 2).replace([np.inf, -np.inf], np.nan).median()
            it.append(dict(benchmark=b_, epoch_items_median=float(ni), learned_n=o["n_items"][b_], zeros=int(is0[df.benchmark.to_numpy() == b_].sum()), ones=int(is1[df.benchmark.to_numpy() == b_].sum())))
        d["item_counts"] = it
        allq = np.array([v for v in o["n_items"].values()]); d["learned_n_all_median_range"] = [float(allq[:, 1].min()), float(np.median(allq[:, 1])), float(allq[:, 1].max())]
    res["candidates"][n] = d
    tab.append(dict(fit=n, converged=o["converged"], **{k: round(v, 3) for k, v in o["T"].items()}, k_share=round(d["k"]["share_gt_0_7"], 3)))
    perb[n] = pd.Series(pw.elpd_common.to_numpy() - bp.G3_common.to_numpy()).groupby(df["benchmark"].to_numpy()).sum()
(DIAG / "compare_candidates.json").write_text(json.dumps(res, indent=1, default=float))
pd.DataFrame(tab).to_csv(DIAG / "compare_T.csv", index=False)
print(pd.DataFrame(tab).to_string())
for n, d in res["candidates"].items():
    if "vs_G3" in d: print(n, "conv", d["converged"], d["convergence"], "| vs G3 common", d["vs_G3"]["common"], "interior", d["vs_G3"]["interior"], "native", d["vs_G3"]["native"], "| k", d["k"], "| wall", d["wall_seconds"])
    else: print(n, d)
if perb:
    P = pd.DataFrame(perb).fillna(0.0); P = P.loc[P.abs().max(1).sort_values(ascending=False).index]; P.to_csv(DIAG / "compare_elpd_by_benchmark.csv", float_format="%.3f")
    top = P.head(24); fig, ax = plt.subplots(figsize=(12, 5)); x = np.arange(len(top)); wdt = .8 / len(top.columns)
    for j, n in enumerate(top.columns): ax.bar(x + j * wdt, top[n], wdt, label=n)
    ax.axhline(0, color="k", lw=.5); ax.set_xticks(x + .4); ax.set_xticklabels([c.short(b_) for b_ in top.index], rotation=90, fontsize=7); ax.legend(fontsize=8)
    ax.set_ylabel("PSIS-LOO gain over G3_ta99 (common measure), summed over rows"); ax.set_title("Candidates against G3_ta99 by benchmark (24 largest absolute changes)", fontsize=10)
    fig.savefig(DIAG / "compare_elpd_by_benchmark.png", dpi=95, bbox_inches="tight"); print("wrote compare_elpd_by_benchmark.png")
