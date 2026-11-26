"""W4 (M5-M8): Epoch's suite (W4a), T1-T7 with max-T (W4b), five held-out folds (W4c), localisation and refit if needed (W4d)."""
import sys, json, time, pickle, warnings
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, xarray as xr
from scipy.stats import binomtest, beta as betad
from scipy.special import logsumexp
from lib import data, fit as fitmod, fit_any, freeze, ppc_checks as ppc
import eci
from eci import save_evaluation

OUT = Path("runs/W/W4"); OUT.mkdir(parents=True, exist_ok=True)
W2, W3 = Path("runs/W/W2"), Path("runs/W/W3")
EPS = 1e-3
log = lambda *a: print(time.strftime("%H:%M:%S"), *a, flush=True)

df = data.fit_input(); scores = data.read_member(data.SCORES)
freeze.check("ppc_checks.py", "sbc.py")
el = ppc.Elig(df, scores)
t = xr.open_datatree(W2 / "seed12345.nc"); post = t["posterior"].to_dataset()
pooled = {v: post[v].stack(s=("chain", "draw")).transpose("s", ...).to_numpy() for v in ["capability", "difficulty", "slope", "sigma"]}
res = {"eligibility": el.summary()}

# ---- W4a
ev = pickle.load(open(W2 / "seed12345_evaluation.pkl", "rb"))
written = save_evaluation(ev, OUT)
res["W4a"] = dict(files=[str(p.name) for p in written], metrics=ev["metrics"].to_dict() if hasattr(ev["metrics"], "to_dict") else str(ev["metrics"]))
ev["metrics"].to_csv(OUT / "epoch_metrics.csv") if hasattr(ev["metrics"], "to_csv") else None
for k in ("sampler_summary", "calibration", "loo_summary"):
    if hasattr(ev.get(k), "to_csv"): ev[k].to_csv(OUT / f"epoch_{k}.csv")

# ---- W4b
cal = json.loads((W3 / "calibration.json").read_text())
null = [json.loads(p.read_text()) for p in W3.glob("rep/null_*.json")]
null = [x for x in null if x["converged"]]; Tn = [x["T"] for x in null]
th = fit_any.thin_post(t, 400, names=("capability", "difficulty", "slope", "sigma")) if False else {k: ppc.thin(v) for k, v in pooled.items()}
y = np.clip(df["performance"].to_numpy(dtype=float), EPS, 1 - EPS)
rq = ppc.residual_quantities(th, el)
Tobs, comp, mx = ppc.stats(y, rq, el)
mt = ppc.max_t(Tobs, Tn)
rawp = ppc.raw_p(y, th, el, rq, Tobs, np.random.default_rng(20261113))
power = cal.get("power", {})
label = {}
for k, g in (("T1", "shape"), ("T2", "2d"), ("T3", "disp"), ("T4", "drift"), ("T5", "offset")):
    label[k] = "power %.2f" % power[g]["power"] if g in power else "power not assessed"
    if g in power and not power[g]["meets_16_of_20_and_15_converged"]: label[k] += " (below 0.8: no power)"
label["T6"] = label["T7"] = "power not assessed"
res["W4b"] = dict(T_observed=Tobs, maxT=mt, raw_p=rawp, power_label=label, n_null=len(Tn),
                  rejected=[k for k in ppc.TNAMES if mt[k]["p_adjusted"] < 0.01], T2_extras=dict())
q = comp["q"]; res["W4b"]["T2_extras"] = dict(share_pairs_abs_r_gt_0_3=None)
rs = []
for a_, b_, ra, rb in el.pairs:
    z = (y - rq["mubar"]) / np.sqrt(rq["v"]); r_ = np.corrcoef(z[ra], z[rb])[0, 1]; rs.append(r_)
rs = np.array(rs); res["W4b"]["T2_extras"] = dict(max_abs_r=float(np.nanmax(np.abs(rs))), share_abs_r_gt_0_3=float(np.mean(np.abs(rs) > 0.3)))
zz = (y - rq["mubar"]) / np.sqrt(rq["v"])
from scipy.stats import spearmanr
res["W4b"]["T4_within_benchmark_spearman"] = {el.bench_names[b]: float(spearmanr(zz[el.rows_of_bench[b]], el.gap[el.rows_of_bench[b]]).statistic) for b in el.t1_bench}
(OUT / "w4b_partial.json").write_text(json.dumps(res, indent=1, default=str))
log("W4b rejected:", res["W4b"]["rejected"], {k: round(mt[k]["p_adjusted"], 4) for k in ppc.TNAMES})

# ---- W4c folds
cnt = df.groupby("model_id").size(); order = df["model_id"].unique()
elig = [m for m in order if cnt[m] >= 6]
def assign(seed):
    rng = np.random.default_rng(seed); fold = -np.ones(len(df), int)
    for m in elig:
        rows = np.where(df["model_id"].to_numpy() == m)[0]; perm = rng.permutation(rows)
        for p, r in enumerate(perm): fold[r] = p % 5
    return fold
def ok(fold):
    for f in range(5):
        tr = fold != f
        if (np.bincount(el.bi[tr], minlength=el.K) < 3).any(): return False
    return True
seed_used = 20261113; fold = assign(seed_used)
if not ok(fold): seed_used = 20261114; fold = assign(seed_used)
fdf = pd.DataFrame({"row": np.arange(len(df)), "model_id": df["model_id"], "benchmark_id": df["benchmark_id"], "fold": fold})
fdf.to_csv(OUT / "folds.csv", index=False)
freeze.freeze(extra={"folds_csv_sha256": fitmod.sha_file(OUT / "folds.csv")})
res["W4c_folds"] = dict(seed=seed_used, n_heldout=int((fold >= 0).sum()), n_eligible_models=len(elig), fold_sizes=np.bincount(fold[fold >= 0], minlength=5).tolist())
heldout_rows, pits, covered, logd = [], [], [], {}
fold_info = {}
for f in range(5):
    train = df[fold != f].reset_index(drop=True)
    side, rr = fitmod.fit(f"fold{f}", OUT, train, spec=None, seed=12345 + f, evaluate=False)
    fold_info[f] = dict(converged=side["converged"], last_attempt=side["last_attempt"], started_from=side["started_from"], wall=side["wall_seconds"])
    tf = xr.open_datatree(OUT / f"fold{f}.nc"); pf = tf["posterior"].to_dataset()
    mnames = [str(x) for x in pf["model"].values]; bnames = [str(x) for x in pf["benchmark"].values]
    mpos = {n: i for i, n in enumerate(mnames)}; bpos = {n: i for i, n in enumerate(bnames)}
    P = {v: pf[v].stack(s=("chain", "draw")).transpose("s", ...).to_numpy() for v in ("capability", "difficulty", "slope", "sigma")}
    rows = np.where(fold == f)[0]
    mi_ = np.array([mpos[df["Model"].iloc[r]] for r in rows]); bi_ = np.array([bpos[df["benchmark"].iloc[r]] for r in rows])
    def mukap(idx):
        Q = {k: v[idx] for k, v in P.items()}
        eta = Q["slope"][:, bi_] * (Q["capability"][:, mi_] - Q["difficulty"][:, bi_])
        return np.clip(1 / (1 + np.exp(-np.clip(eta, -700, 700))), 1e-6, 1 - 1e-6), (1 / (4 * Q["sigma"] ** 2) - 1)[:, bi_]
    S = P["capability"].shape[0]; ev2000 = np.linspace(0, S - 1, 2000).astype(int)
    mu, kap = mukap(ev2000); rng = np.random.default_rng(20261113 + f)
    yrep = rng.beta(mu * kap, (1 - mu) * kap); tgt = y[rows]
    pit = (yrep <= tgt[None, :]).mean(0); cov = (pit >= .05) & (pit <= .95)
    pits.append(pit); covered.append(cov); heldout_rows.append(rows)
    # F0 held-out log predictive density (all draws) for W6
    muA, kapA = mukap(np.arange(S)); lp = betad.logpdf(tgt[None, :], muA * kapA, (1 - muA) * kapA)
    logd[f] = (rows, logsumexp(lp, axis=0) - np.log(S))
    log("fold", f, fold_info[f]["converged"], "coverage", cov.mean())
rows_all = np.concatenate(heldout_rows); pit_all = np.concatenate(pits); cov_all = np.concatenate(covered)
pd.DataFrame({"row": rows_all, "model_id": df["model_id"].to_numpy()[rows_all], "benchmark_id": df["benchmark_id"].to_numpy()[rows_all], "pit": pit_all, "covered": cov_all}).to_csv(OUT / "heldout_pit.csv", index=False)
pd.DataFrame({"row": np.concatenate([logd[f][0] for f in range(5)]), "fold": np.concatenate([[f] * len(logd[f][0]) for f in range(5)]),
              "logdens_F0": np.concatenate([logd[f][1] for f in range(5)])}).to_csv(OUT / "fold_logdens_F0.csv", index=False)
mid_ = df["model_id"].to_numpy()[rows_all]; um = np.unique(mid_); rngb = np.random.default_rng(20261113)
per_model = {m: cov_all[mid_ == m] for m in um}
boots = []
for _ in range(2000):
    pick = rngb.choice(um, len(um)); c = np.concatenate([per_model[m] for m in pick]); boots.append(c.mean())
overall = float(cov_all.mean()); ci = [float(np.quantile(boots, .05)), float(np.quantile(boots, .95))]
bench_rows = df["benchmark_id"].to_numpy()[rows_all]; flags = []; tab = {}
ub = [b for b in np.unique(bench_rows) if (bench_rows == b).sum() >= 20]
for b in ub:
    k, n = int(cov_all[bench_rows == b].sum()), int((bench_rows == b).sum()); p = binomtest(k, n, 0.9).pvalue
    tab[str(b)] = dict(k=k, n=n, p=float(p)); 
    if p < 0.01 / 44: flags.append(str(b))
res["W4c"] = dict(folds=fold_info, overall_coverage=overall, bootstrap90=ci, in_rule_0_85_0_95=bool(.85 <= overall <= .95), n_benchmarks_tested=len(ub),
                  bonferroni_level=0.01 / 44, flagged_benchmarks=flags, per_benchmark=tab, all_folds_converged=all(v["converged"] for v in fold_info.values()),
                  epoch_loo_coverage_0_9=float(ev["calibration"].iloc[0].get("coverage_0.9_loo", np.nan)) if hasattr(ev.get("calibration"), "iloc") else None)
# ---- verdict inputs
rej = res["W4b"]["rejected"]
res["C2_inputs"] = dict(rejected_checks=rej, coverage_ok=res["W4c"]["in_rule_0_85_0_95"], flagged_benchmarks=flags,
                        T2_or_T5_power_ok=bool(power.get("2d", {}).get("meets_16_of_20_and_15_converged") or power.get("offset", {}).get("meets_16_of_20_and_15_converged")))
res["C2_clean"] = bool(not rej and res["W4c"]["in_rule_0_85_0_95"] and not flags)
(OUT / "ppc.json").write_text(json.dumps(res, indent=1, default=str))
log("W4 done: clean", res["C2_clean"], "rejected", rej, "coverage", overall, "flagged", flags)
if res["C2_clean"]:
    pw = res["C2_inputs"]["T2_or_T5_power_ok"]
    v = dict(verdict="Adequate" if pw else "Inconclusive (nothing rejected, but neither T2 nor T5 reached power 0.8)", power_labels=label,
             misfit_types_with_power=[k for k, g in (("T1", "shape"), ("T2", "2d"), ("T3", "disp"), ("T4", "drift"), ("T5", "offset")) if power.get(g, {}).get("meets_16_of_20_and_15_converged")],
             not_assessed=["T6", "T7"] + [k for k, g in (("T1", "shape"), ("T2", "2d"), ("T3", "disp"), ("T4", "drift"), ("T5", "offset")) if not power.get(g, {}).get("meets_16_of_20_and_15_converged")])
    (OUT / "verdict_C2.json").write_text(json.dumps(v, indent=1)); log("C2 verdict:", v["verdict"])
else:
    log("LOCALISATION NEEDED (W4d): not writing verdict_C2.json")

