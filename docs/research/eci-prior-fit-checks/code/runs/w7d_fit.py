"""One fit of a W7 follow-up candidate (runs/w7d_models.py) through Epoch's fit function, in memory, with the same
call as runs/w7_memfit.py (pilot then dense, or cold). Run from stdin of the container Python (no __file__ used).

  fit (default)  fit to Epoch's 2,879 rows; convergence, PSIS-LOO (az.loo, pointwise), LOO-PIT (az.loo_pit), T1-T7 with
                 the frozen lib/ppc_checks.stats. Writes nothing to disk: stdout carries one .npz (redirect it to
                 /dev/shm/w7diag/<name>.npz) with the sidecar json, the pointwise table, thinned draws, the draws used for model-true
                 replicates, pointwise results and residual quantities. All text goes to stderr.
  --fold k       W4 K-fold training fit of fold k; held-out log predictive density over 500 thinned draws, as one json
                 on stdout (rows, logd, boundary flag, convergence).
  --rep r        model-true replicate r: reads the candidate's .npz from stdin (so the script itself must be passed
                 with -c), simulates from replicate draw r, refits, computes T1-T7 of the replicate under its own
                 refit. The replicate's json goes to stdout.
Pointwise elpd on a common measure (elpd_common): interior rows keep their density; rows at a bound use the
log of the LOO predictive mass at that bound. For models without `bnd` that mass is the PSIS-weighted mean of the
Beta mass beyond the clip (az.loo_expectations with the fit's own PSIS weights); with `bnd` it is the likelihood.
Usage: w7d_fit.py --name H1 --features dev,fam,bnd [--clusters 1] [--target-accept 0.99] [--seed 12345] [--fold k | --rep r]"""
import sys, os
OUT = os.fdopen(os.dup(1), "wb"); os.dup2(2, 1)          # stdout carries only the npz
sys.path[:0] = ["runs/vendor/eci-public/src", "runs"]
import argparse, json, hashlib, io, time, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, xarray as xr, arviz as az
import w7d_models as wd, w7_data, w7_memfit
from lib import data, models, expand, ppc_checks as ppc

ap = argparse.ArgumentParser()
ap.add_argument("--name", required=True); ap.add_argument("--features", required=True); ap.add_argument("--clusters", type=int, default=0)
ap.add_argument("--target-accept", type=float, default=0.99); ap.add_argument("--seed", type=int, default=12345)
ap.add_argument("--fold", type=int, default=None); ap.add_argument("--rep", type=int, default=None); ap.add_argument("--R", type=int, default=200)
a = ap.parse_args()
feats = tuple(f for f in a.features.split(",") if f)
wd.install()
import eci.bayesian as eb
_orig = eb.fit_bayesian_eci
eb.fit_bayesian_eci = lambda *x, **k: _orig(*x, **{**k, "target_accept": a.target_accept})
df, ex = w7_data.load("orig"); ex["clusters"] = wd.CLUSTERS if a.clusters else None
spec = models.Spec(feats); VN = wd.var_names(feats)
el = ppc.Elig(df, data.read_member(data.SCORES))


def arrays(tr, n=None, idx=None):
    ds = az.extract(tr, var_names=VN, combined=True)
    P = {k: ds[k].transpose("sample", ...).to_numpy() for k in VN}
    if idx is not None: return {k: v[idx] for k, v in P.items()}
    return {k: ppc.thin(v, n) for k, v in P.items()} if n else P


def tstats(P, frame, y):
    pr = wd.predict(feats, P, frame, ex); rq_ = wd.rq(pr, P)
    T, comp, mx = ppc.stats(np.clip(y, wd.EPS, 1 - wd.EPS), rq_, el)
    return T, comp, mx, rq_, pr


if a.rep is not None:                                   # ---------------- model-true replicate
    Z = np.load(io.BytesIO(sys.stdin.buffer.read()))
    Pi = {k: Z["rep_" + k][a.rep:a.rep + 1] for k in VN}
    seed = int.from_bytes(hashlib.sha256(f"w7d:{a.name}:{a.rep}".encode()).digest()[:4], "big")
    y = wd.simulate({k: v[0] for k, v in wd.predict(feats, Pi, df, ex).items()}, np.random.default_rng(seed))
    dr = df.copy(); dr["performance"] = y
    side, tr = w7_memfit.fit_mem(dr, spec, seed % (2 ** 31), ex)
    T, comp, mx, _, _ = tstats(arrays(tr, ppc.N_DRAWS), dr, y)
    res = dict(cand=a.name, r=a.rep, R=a.R, position=int(Z["rep_pos"][a.rep]), seed=seed, converged=side["converged"], last_attempt=side["last_attempt"],
               started_from=side["started_from"], wall_seconds=side["wall_seconds"], T=T, maxima=mx,
               zeros=int((y <= wd.EPS).sum()), ones=int((y >= 1 - wd.EPS).sum()))
    OUT.write(json.dumps(res, indent=1, default=float).encode()); OUT.flush()   # host redirects stdout to /dev/shm
    print("DONE", a.name, a.rep, side["converged"], {k: round(v, 3) for k, v in T.items()}, flush=True); sys.exit(0)

if a.fold is not None:                                  # ---------------- K-fold training fit
    import pymc as pm
    from scipy.special import logsumexp
    def ex_of(sub):
        e = expand.extras_for(sub, ex); e["clusters"] = ex["clusters"]; return e
    fold = pd.read_csv("runs/W/W4/folds.csv")["fold"].to_numpy()
    train = df[fold != a.fold].reset_index(drop=True); held = df[fold == a.fold]; held_rows = np.where(fold == a.fold)[0]
    ev = pd.concat([train, held]).reset_index(drop=True)
    side, t = w7_memfit.fit_mem(train, spec, a.seed, ex_of(train))
    post = t["posterior"].to_dataset(); post = post.isel(draw=np.linspace(0, post.sizes["draw"] - 1, 500).astype(int))
    m = models.build_model(ev, spec, ex=ex_of(ev)); thin = xr.DataTree.from_dict({"posterior": post})
    with m: pm.compute_log_likelihood(thin, extend_inferencedata=True, progressbar=False)
    ll = thin["log_likelihood"].to_dataset()["obs"].stack(s=("chain", "draw")).transpose("s", "obs_dim_0").to_numpy()[:, len(train):]
    logd = logsumexp(ll, axis=0) - np.log(ll.shape[0]); yh = held["performance"].to_numpy(float)
    OUT.write(json.dumps(dict(name=a.name, fold=a.fold, converged=side["converged"], started_from=side["started_from"], last_attempt=side["last_attempt"],
                              attempts=side["attempts"], wall_seconds=side["wall_seconds"], row=held_rows.tolist(), logd=logd.tolist(),
                              at_bound=((yh <= wd.EPS) | (yh >= 1 - wd.EPS)).tolist()), default=float).encode()); OUT.flush()
    print("DONE", a.name, "fold", a.fold, side["converged"], side["started_from"], len(logd), flush=True); sys.exit(0)

# ---------------- full fit
import pymc as pm
t0 = time.time()
side, tr = w7_memfit.fit_mem(df, spec, a.seed, ex)
print("fit done", a.name, side["converged"], side["started_from"], side["attempts"], side["wall_seconds"], flush=True)
m = models.build_model(df, spec, ex=ex)
with m: pm.compute_log_likelihood(tr, extend_inferencedata=True, progressbar=False)
y = np.clip(df["performance"].to_numpy(float), wd.EPS, 1 - wd.EPS); is0, is1 = y <= wd.EPS, y >= 1 - wd.EPS
post = tr["posterior"]; C, Dn = post.sizes["chain"], post.sizes["draw"]; S = C * Dn
Pall = arrays(tr); prall = wd.predict(feats, Pall, df, ex)
# convergence (ArviZ) over Epoch's diagnostic variables plus the new ones
dv = [v for v in spec.diag_vars() if v in post]
rh = az.rhat(tr, var_names=dv); eb_ = az.ess(tr, var_names=dv, method="bulk"); et_ = az.ess(tr, var_names=dv, method="tail")
conv = dict(divergences=int(tr["sample_stats"]["diverging"].to_numpy().sum()), max_rhat=float(max(np.nanmax(rh[v].to_numpy()) for v in dv)),
            min_ess_bulk=float(min(np.nanmin(eb_[v].to_numpy()) for v in dv)), min_ess_tail=float(min(np.nanmin(et_[v].to_numpy()) for v in dv)),
            max_rhat_by_var={v: float(np.nanmax(rh[v].to_numpy())) for v in dv})
hv = [v for v in ["tau_alpha", "sigma_median", "tau_sigma", "tau_delta", "tau_fam"] if v in post]
hyper = json.loads(az.summary(tr, var_names=hv, kind="all", ci_prob=0.9, ci_kind="eti", round_to="none").to_json(orient="index"))
# PSIS-LOO, pointwise
loo = az.loo(tr, pointwise=True, var_name="obs"); elpd_i = np.asarray(loo.elpd_i).ravel(); kk = np.asarray(loo.pareto_k).ravel()
# common-measure elpd for rows at a bound
elpd_c = elpd_i.copy(); bnd_rows = np.where(is0 | is1)[0]
if not wd.has_bnd(feats):
    m0, m1 = wd.bound_mass({k: v[:, bnd_rows] for k, v in prall.items()})
    g = np.where(is0[bnd_rows][None], m0, m1).reshape(C, Dn, len(bnd_rows))
    sub = xr.DataTree.from_dict({"posterior": post.to_dataset()[["tau_alpha"]],
                                 "log_likelihood": tr["log_likelihood"].to_dataset().isel(obs_dim_0=bnd_rows),
                                 "posterior_predictive": xr.Dataset({"obs": (("chain", "draw", "obs_dim_0"), g)},
                                                                    coords={"chain": post["chain"].to_numpy(), "draw": post["draw"].to_numpy(), "obs_dim_0": bnd_rows})})
    e_, _k = az.loo_expectations(sub, var_name="obs", kind="mean")
    elpd_c[bnd_rows] = np.log(np.asarray(e_).ravel())
# LOO-PIT from simulated posterior predictive draws
rng = np.random.default_rng(20261125)
yrep = np.clip(wd.simulate(prall, rng), wd.EPS, 1 - wd.EPS).reshape(C, Dn, -1)
od = tr["observed_data"]["obs"].dims[0]
pt_ = xr.DataTree.from_dict({"posterior": post.to_dataset()[["tau_alpha"]], "log_likelihood": tr["log_likelihood"].to_dataset(),
                             "observed_data": tr["observed_data"].to_dataset(),
                             "posterior_predictive": xr.Dataset({"obs": (("chain", "draw", od), yrep)}, coords={"chain": post["chain"].to_numpy(), "draw": post["draw"].to_numpy()})})
pit = np.asarray(az.loo_pit(pt_, var_names="obs")["obs"]).ravel()
# T1-T7 (registered thinning to 400 draws)
P4 = {k: ppc.thin(v, ppc.N_DRAWS) for k, v in Pall.items()}
T, comp, mx, rq_, pr4 = tstats(P4, df, y)
z = (y - rq_["mubar"]) / np.sqrt(rq_["v"])
rs = np.array([np.corrcoef(z[ra], z[rb])[0, 1] for _, _, ra, rb in el.pairs])
top = lambda vals, labs, k=8: [dict(item=labs[i], value=float(vals[i])) for i in np.argsort(-np.abs(vals))[:k]]
bn = el.bench_names
out = dict(name=a.name, features=list(feats), clusters=wd.CLUSTERS if a.clusters else None, target_accept=a.target_accept, seed=a.seed,
           converged=side["converged"], started_from=side["started_from"], attempts=side["attempts"], last_attempt=side["last_attempt"],
           wall_seconds=side["wall_seconds"], total_seconds=round(time.time() - t0, 1), convergence=conv, hyper_summary=hyper, T=T, maxima=mx,
           T2_extras=dict(max_abs_r=float(np.nanmax(np.abs(rs))), share_abs_r_gt_0_3=float(np.mean(np.abs(rs) > .3))),
           T1_top=top(comp["Qb"], [bn[b] for b in el.t1_bench]),
           T2_top=top(comp["q"], [f"{bn[i]} | {bn[j]}" for i, j, _, _ in el.pairs]),
           T5_top=top(comp["t"], [f"{o} | {bn[b]}" for (o, b), _ in el.cells]),
           T6_top=top(comp["cb"], bn),
           bounds=dict(zeros=int(is0.sum()), exp_zeros=float(rq_["p0"].sum()), ones=int(is1.sum()), exp_ones=float(rq_["p1"].sum())),
           loo=dict(elpd=float(loo.elpd), se=float(loo.se), p=float(loo.p), k_share=float((kk > .7).mean()), n_k_gt_0_7=int((kk > .7).sum()), n_k_gt_1=int((kk > 1).sum()),
                    elpd_interior=float(elpd_i[~(is0 | is1)].sum()), elpd_common=float(elpd_c.sum()), elpd_common_bound_rows=float(elpd_c[is0 | is1].sum())),
           pit=dict(ks_distance=float(np.max(np.abs(np.sort(pit) - (np.arange(1, len(pit) + 1) - .5) / len(pit)))), var_ratio=float(pit.var() * 12),
                    share_lt_0_05=float((pit < .05).mean()), share_gt_0_95=float((pit > .95).mean())))
if wd.has_bnd(feats):
    ln = Pall["log_n"]; out["n_items"] = {bn[b]: [float(np.exp(np.quantile(ln[:, b], q))) for q in (.05, .5, .95)] for b in range(el.K)}
PW = pd.DataFrame(dict(model=df["Model"], benchmark=df["benchmark"], y=y, mubar=rq_["mubar"], v=rq_["v"], p0=rq_["p0"], p1=rq_["p1"], z=z, elpd=elpd_i,
                       elpd_common=elpd_c, k=kk, pit=pit)).to_csv(index=False, float_format="%.5f")
print("scored", a.name, "T", {k: round(v, 3) for k, v in T.items()}, "loo", out["loo"], flush=True)
# npz to stdout
pos = np.floor(np.arange(a.R) * S / a.R).astype(int)
sm = lambda v: v.astype(np.float32)
blob = dict(sidecar_json=np.array(json.dumps(out, indent=1, default=float)), pointwise_csv=np.array(PW), rep_pos=pos, elpd_i=elpd_i, pareto_k=kk, elpd_common=elpd_c, pit=pit, z=z, y=y, mubar=rq_["mubar"], v=rq_["v"], p0=rq_["p0"], p1=rq_["p1"],
            chat=rq_["chat"], Qb=comp["Qb"], q=comp["q"], cb=comp["cb"], t=comp["t"], U=comp["U"],
            eci=sm(post["eci"].stack(s=("chain", "draw")).transpose("s", "model").to_numpy()),
            model_names=np.array(el.model_names), bench_names=np.array(bn), family=np.array(list(post["family"].to_numpy()) if "family" in post.coords else []))
for k in VN:
    blob["rep_" + k] = Pall[k][pos]; blob["thin_" + k] = sm(P4[k])
    if Pall[k].ndim <= 2: blob["full_" + k] = sm(Pall[k])
blob["mu400"] = sm(pr4["mu"]); blob["kap400"] = sm(pr4["kap"]); blob["p0_400"] = sm(pr4["p0"]); blob["p1_400"] = sm(pr4["p1"]); blob["mui400"] = sm(pr4["mu_i"])
buf = io.BytesIO(); np.savez_compressed(buf, **blob); OUT.write(buf.getvalue()); OUT.flush()
print("DONE", a.name, side["converged"], round(time.time() - t0), "s; npz", len(buf.getvalue()) // 1024, "KB", flush=True)
