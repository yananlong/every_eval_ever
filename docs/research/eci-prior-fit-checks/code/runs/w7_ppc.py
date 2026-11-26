"""Score a W7 fit: convergence (az.summary, az.rhat, az.ess), PSIS-LOO against F0 (Epoch's data only; the frozen
compare.loo_stats, which calls az.loo, plus az.compare as a cross-check), LOO-PIT (az.loo_pit on a posterior
predictive group simulated from the fit's own mean and concentration), T1-T7 with the W4 code
(lib/ppc_checks.stats, registered definitions unchanged) on residual quantities from the fit's own mean and
concentration, raw in-sample predictive p, an approximate max-T p against F0's model-true replicates
(runs/W/W3/rep/null_*.json; the calibrated p comes from runs/w7_rep.py), and the T1, T2, T5 localisation.
Posterior draws come from az.extract; the registered draw thinning (ppc_checks.thin) is kept so that the T values
equal W4's for F0. On augmented inputs the checks use Epoch's 2,879 rows (the first rows of every W7 input; for the
cell-mean inputs those rows hold the cell means that were fitted). Usage: w7_ppc.py NAME FEATURES DATA"""
import sys, json, warnings
from pathlib import Path
sys.path[:0] = ["runs/vendor/eci-public/src", "runs"]; warnings.filterwarnings("ignore")
import numpy as np, xarray as xr, arviz as az
from scipy.special import betainc
import w7_models as w7, w7_data
from lib import data, models, ppc_checks as ppc, compare

EPS = 1e-3
HYPER = ["tau_alpha", "sigma_median", "tau_sigma", "tau_delta", "tau_omega", "tau_fam", "tau_l", "tau_g", "tau_u"]
F0_NC = Path("runs/W/W2/f0_seed12345.nc")


def open_tree(nc_or_tree):
    return nc_or_tree if isinstance(nc_or_tree, xr.DataTree) else xr.open_datatree(nc_or_tree)


def post_arrays(nc, feats, n=ppc.N_DRAWS):
    """Posterior draws as arrays with a leading sample axis (chain-major), via az.extract, thinned as W4 does."""
    t = open_tree(nc)
    names = ["capability", "difficulty", "slope", "sigma"] + sum((w7.POST_VARS[f] for f in feats), [])
    ds = az.extract(t, var_names=names, combined=True)
    return {k: ppc.thin(ds[k].transpose("sample", ...).to_numpy(), n) for k in names}, t


def rq_from(mu, kap, P):
    a, b = mu * kap, (1 - mu) * kap
    return dict(mubar=mu.mean(0), v=(mu * (1 - mu) / (kap + 1)).mean(0) + mu.var(0), chat=P["capability"].mean(0),
                p0=betainc(a, b, EPS).mean(0), p1=(1 - betainc(a, b, 1 - EPS)).mean(0))


def diag_vars(feats):
    w7.install(); return [v for v in models.Spec(tuple(feats)).diag_vars()]


def convergence(t, feats):
    """ArviZ diagnostics over Epoch's diagnostic variables plus each feature's (sign-free ones for f1r)."""
    post = t["posterior"]
    dv = [v for v in diag_vars(feats) if v in post]
    rh = az.rhat(t, var_names=dv); es = az.ess(t, var_names=dv, method="bulk"); et = az.ess(t, var_names=dv, method="tail")
    worst = lambda ds, f: {v: float(f(ds[v].to_numpy())) for v in dv}
    hv = [v for v in HYPER if v in post]
    sm = az.summary(t, var_names=hv, kind="all", ci_prob=0.9, ci_kind="eti", round_to="none")
    ss = t["sample_stats"]
    return dict(chains=int(post.sizes["chain"]), draws=int(post.sizes["draw"]),
                divergences=int(ss["diverging"].to_numpy().sum()),
                max_rhat=float(max(worst(rh, np.nanmax).values())), min_ess_bulk=float(min(worst(es, np.nanmin).values())),
                min_ess_tail=float(min(worst(et, np.nanmin).values())),
                max_rhat_by_var=worst(rh, np.nanmax), min_ess_bulk_by_var=worst(es, np.nanmin),
                hyper_summary=json.loads(sm.to_json(orient="index")))


def mu_kappa_all(feats, nc, df, ex, n_rows, chunk=500):
    """mu and kappa over every posterior draw, shaped (chain, draw, row) for Epoch's rows, computed in chunks."""
    t = open_tree(nc)
    names = ["capability", "difficulty", "slope", "sigma"] + sum((w7.POST_VARS[f] for f in feats), [])
    ds = az.extract(t, var_names=names, combined=True); S = ds.sizes["sample"]
    C, D = t["posterior"].sizes["chain"], t["posterior"].sizes["draw"]
    mu = np.empty((S, n_rows)); kap = np.empty((S, n_rows))
    for i in range(0, S, chunk):
        P = {k: ds[k].isel(sample=slice(i, i + chunk)).transpose("sample", ...).to_numpy() for k in names}
        m, k = w7.mu_kappa(feats, P, df, ex); mu[i:i + chunk], kap[i:i + chunk] = m[:, :n_rows], k[:, :n_rows]
    return mu.reshape(C, D, n_rows), kap.reshape(C, D, n_rows)


def pit_tree(nc, feats, kind="orig", seed=20261125):
    """DataTree with posterior, log_likelihood, observed_data and a posterior_predictive group of Beta draws from
    the fit's own mean and concentration (one per posterior draw), ready for az.loo_pit and az.plot_loo_pit."""
    t = open_tree(nc); df, ex = w7_data.load(kind, "lin"); n0 = len(data.fit_input())
    mu, kap = mu_kappa_all(feats, t, df, ex, n0)
    yrep = np.random.default_rng(seed).beta(mu * kap, (1 - mu) * kap)
    obs_dim = t["observed_data"]["obs"].dims[0]
    pp = xr.Dataset({"obs": (("chain", "draw", obs_dim), yrep)},
                    coords={"chain": t["posterior"]["chain"].to_numpy(), "draw": t["posterior"]["draw"].to_numpy()})
    groups = {"posterior": t["posterior"].to_dataset()[["capability"]], "posterior_predictive": pp,
              "observed_data": t["observed_data"].to_dataset()}
    if "log_likelihood" in t: groups["log_likelihood"] = t["log_likelihood"].to_dataset()
    return xr.DataTree.from_dict(groups)


def pit_summary(dt):
    pit = np.asarray(az.loo_pit(dt, var_names="obs")["obs"]).ravel()
    return dict(n=len(pit), share_lt_0_05=float(np.mean(pit < .05)), share_gt_0_95=float(np.mean(pit > .95)),
                share_central_50=float(np.mean(np.abs(pit - .5) < .25)),
                ks_distance=float(np.max(np.abs(np.sort(pit) - (np.arange(1, len(pit) + 1) - .5) / len(pit)))))


def score(name, feats, kind, folder=Path("runs/W/W7"), raw_n=200, out_folder=None, with_pit=True):
    df0 = data.fit_input().reset_index(drop=True); el = ppc.Elig(df0, data.read_member(data.SCORES))
    df, ex = w7_data.load(kind, "lin")
    P, t = post_arrays(folder / f"{name}.nc", feats)
    mu, kap = w7.mu_kappa(feats, P, df, ex); mu, kap = mu[:, :len(df0)], kap[:, :len(df0)]   # Epoch's rows come first
    y = np.clip(df["performance"].to_numpy(dtype=float)[:len(df0)], EPS, 1 - EPS)
    rq = rq_from(mu, kap, P)
    T, comp, mx = ppc.stats(y, rq, el)
    Tn = [x["T"] for x in (json.loads(p.read_text()) for p in Path("runs/W/W3/rep").glob("null_*.json")) if x["converged"]]
    approx = ppc.max_t(T, Tn)
    rng = np.random.default_rng(20261124); cnt = {k: 0 for k in ppc.TNAMES}; S = mu.shape[0]; pick = np.linspace(0, S - 1, raw_n).astype(int)
    for s in pick:
        yr = np.clip(rng.beta(mu[s] * kap[s], (1 - mu[s]) * kap[s]), EPS, 1 - EPS); tr = ppc.stats(yr, rq, el, with_components=False)
        for k in ppc.TNAMES: cnt[k] += tr[k] >= T[k]
    z = (y - rq["mubar"]) / np.sqrt(rq["v"])
    rs = np.array([np.corrcoef(z[ra], z[rb])[0, 1] for _, _, ra, rb in el.pairs])
    top = lambda vals, labs, k=6: [dict(item=labs[i], value=float(vals[i])) for i in np.argsort(-np.abs(vals))[:k]]
    out = dict(name=name, features=list(feats), data=kind, convergence=convergence(t, feats), T=T,
               approx_vs_F0_replicates=approx, raw_p={k: cnt[k] / len(pick) for k in ppc.TNAMES},
               T2_extras=dict(max_abs_r=float(np.nanmax(np.abs(rs))), share_abs_r_gt_0_3=float(np.mean(np.abs(rs) > 0.3))),
               T1_top=top(comp["Qb"], [el.bench_names[b] for b in el.t1_bench]),
               T2_top=top(comp["q"], [f"{el.bench_names[a]} | {el.bench_names[b]}" for a, b, _, _ in el.pairs]),
               T2_top_r=top(rs, [f"{el.bench_names[a]} | {el.bench_names[b]}" for a, b, _, _ in el.pairs]),
               T5_top=top(comp["t"], [f"{o} | {el.bench_names[b]}" for (o, b), _ in el.cells]))
    if kind == "orig" and "log_likelihood" in t:
        t0 = xr.open_datatree(F0_NC)
        L0 = compare.loo_stats(t0); L = compare.loo_stats(t)
        d, se = compare.paired(L["elpd_i"], L0["elpd_i"])
        cmp = az.compare({"F0": az.loo(t0, pointwise=True, var_name="obs"), name: az.loo(t, pointwise=True, var_name="obs")}, round_to="none")
        out["loo"] = dict(elpd=L["elpd"], se_elpd=L["se"], p=L["p"], k_share=L["k_share"], n_k_gt_0_7=L["n_k_gt_0_7"],
                          delta_vs_F0=d, se=se, kfold_trigger=bool(compare.kfold_trigger(L0["k_share"], L["k_share"])),
                          az_compare={str(i): dict(rank=int(r["rank"]), elpd=float(r["elpd"]), elpd_diff=float(r["elpd_diff"]),
                                                    dse=float(r["dse"]), weight=float(r["weight"])) for i, r in cmp.iterrows()})
    if with_pit and "log_likelihood" in t:
        out["loo_pit"] = pit_summary(pit_tree(t, feats, kind))
    (Path(out_folder or folder) / f"{name}_ppc.json").write_text(json.dumps(out, indent=1, default=float))
    return out


if __name__ == "__main__":
    name, feats, kind = sys.argv[1], tuple(f for f in sys.argv[2].split(",") if f), sys.argv[3] if len(sys.argv) > 3 else "orig"
    o = score(name, feats, kind)
    print(name, "conv", {k: o["convergence"][k] for k in ("divergences", "max_rhat", "min_ess_bulk", "min_ess_tail")})
    print("  T", {k: round(v, 3) for k, v in o["T"].items()})
    print("  approx adj p vs F0 reps", {k: round(o["approx_vs_F0_replicates"][k]["p_adjusted"], 4) for k in ppc.TNAMES})
    print("  raw p", o["raw_p"], "T2 extras", o["T2_extras"])
    if "loo" in o: print("  loo", {k: (round(v, 2) if isinstance(v, float) else v) for k, v in o["loo"].items() if k != "az_compare"}, o["loo"]["az_compare"])
    if "loo_pit" in o: print("  loo_pit", o["loo_pit"])
