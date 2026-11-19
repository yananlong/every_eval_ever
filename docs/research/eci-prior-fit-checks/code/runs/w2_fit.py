"""W2: Epoch's fit on the published input (W2a), on the loader output (W2b), and our F0 with the equivalence check EQ (M12)."""
import sys, json, time, warnings
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, arviz as az
from scipy.stats import spearmanr
import eci.bayesian as eb
from eci import prepare_benchmark_data
from lib import data, models, fit, sens_metrics as sm, freeze

OUT = Path("runs/W/W2"); OUT.mkdir(parents=True, exist_ok=True)
SEEDS = (12345, 22345, 32345)
log = lambda *a: print(time.strftime("%H:%M:%S"), *a, flush=True)

df = data.fit_input()
freeze.freeze("strata.json", "prior-grid.json", "sens_metrics.py", "models.py")
strata = json.loads(Path("runs/strata.json").read_text())

# ---------------- W2a
sides = {}
for s in SEEDS:
    log("W2a fit seed", s)
    sides[s], _ = fit.fit(f"seed{s}", OUT, df, spec=None, seed=s, evaluate=True)
    log("  converged", sides[s]["converged"], "stage", sides[s]["started_from"], "last", sides[s]["last_attempt"], "wall", sides[s]["wall_seconds"])
draws = {}; names = None
for s in SEEDS:
    draws[s], nm, _t = fit.load_eci(OUT / f"seed{s}.nc")
    assert names is None or names == nm
    names = nm
names = list(names)
idx = {n: i for i, n in enumerate(names)}
anchor = np.array([n in sm.ANCHORS for n in names])

pub = data.read_member("epoch_capabilities_index/eci_scores.csv").set_index("Model")
pub = pub.loc[names]
pub_w = (pub["eci_ci_high"] - pub["eci_ci_low"]).to_numpy()
d12 = draws[12345]; s12 = sm.summarise(d12)
dm = s12["mean"] - pub["eci"].to_numpy()
tol = np.maximum(0.5, 0.07 * pub_w)
na = ~anchor
g0 = {}
g0["max_abs_d"] = float(np.nanmax(np.abs(dm[na])))
g0["n_exceed_tolerance"] = int((np.abs(dm[na]) > tol[na]).sum())
g0["max_abs_d_over_W"] = float(np.nanmax(np.abs(dm[na]) / pub_w[na]))
g0["spearman"] = float(spearmanr(s12["mean"], pub["eci"].to_numpy()).statistic)
wr = s12["width"][na] / pub_w[na]
g0["median_width_ratio"] = float(np.median(wr)); g0["share_ratio_in_085_115"] = float(np.mean((wr >= .85) & (wr <= 1.15)))
g0["seed12345_pass"] = bool(g0["n_exceed_tolerance"] == 0 and g0["spearman"] >= .999 and .95 <= g0["median_width_ratio"] <= 1.05 and g0["share_ratio_in_085_115"] >= .95)
g0["worst_models"] = [(names[i], float(dm[i]), float(pub_w[i])) for i in np.argsort(-np.abs(dm) * na)[:5]]
g0["per_seed_converged"] = {str(s): bool(sides[s]["converged"]) for s in SEEDS}
g0["per_seed_diag"] = {str(s): {k: sides[s]["last_attempt"][k] for k in ("divergences", "max_rhat", "min_ess")} | {"stage": sides[s]["started_from"], "attempts": len(sides[s]["attempts"]), "min_tail_ess": sides[s].get("min_tail_ess"), "min_bfmi": sides[s].get("min_bfmi")} for s in SEEDS}
g0["all_seeds_converged"] = all(sides[s]["converged"] for s in SEEDS)
g0["seed_to_seed_sd_max"] = float(np.max(np.std([sm.summarise(draws[s])["mean"] for s in SEEDS], axis=0, ddof=1)))
# EDI and slope against published
t12 = fit.load_eci(OUT / "seed12345.nc")[2]
post = t12["posterior"].to_dataset()
a_b = None
try:
    ed = post["difficulty"]; sl = post["slope"]
    cap = post["capability"].stack(s=("chain", "draw")).transpose("s", "model").to_numpy()
    low, high = idx["Claude 3.5 Sonnet"], idx["GPT-5"]
    b = 20.0 / (cap[:, high] - cap[:, low]); a = 130.0 - b * cap[:, low]
    edi = a[:, None] + b[:, None] * ed.stack(s=("chain", "draw")).transpose("s", "benchmark").to_numpy()
    slope_sc = sl.stack(s=("chain", "draw")).transpose("s", "benchmark").to_numpy() / b[:, None]
    bn = [str(x) for x in ed["benchmark"].values]
    pe = data.read_member("epoch_capabilities_index/edi_scores.csv").set_index("benchmark_name").loc[bn]
    g0["max_abs_diff_edi"] = float(np.max(np.abs(edi.mean(0) - pe["edi"].to_numpy())))
    g0["max_abs_diff_slope_scaled"] = float(np.max(np.abs(slope_sc.mean(0) - pe["estimated_slope_scaled"].to_numpy())))
except Exception as e:
    g0["edi_error"] = repr(e)
# published bootstraps: adjacent-pair probabilities of the top 10 (published order)
import zipfile
bs = json.loads(zipfile.ZipFile(data.ZIP).read("epoch_capabilities_index/eci_bootstraps.json"))
bnames = bs["model"]["names"]; cs = np.array(bs["model"]["capability_samples"], dtype=float)
if cs.shape[0] != len(bnames): cs = cs.T
order = [n for n in pub.sort_values("eci", ascending=False).index[:10]]
pp = []
for r in range(9):
    i, j = bnames.index(order[r]), bnames.index(order[r + 1])
    pp.append(dict(i=order[r], j=order[r + 1], published=float(np.mean(cs[i] > cs[j])), ours=sm.p_greater(d12, idx[order[r]], idx[order[r + 1]])))
g0["top10_adjacent_pairs"] = pp
g0["published_bootstrap_shape"] = list(cs.shape)

# ---------------- W2b loader input
log("W2b loader input")
dfb = prepare_benchmark_data(Path(data.ZIP))
key = ["model_id", "benchmark_id"]
mg = df.merge(dfb, on=key, how="outer", suffixes=("_pub", "_loader"), indicator=True)
diff = mg[(mg["_merge"] != "both") | ((mg["performance_pub"] - mg["performance_loader"]).abs() > 1e-12)]
w2b = {"n_rows_loader": int(len(dfb)), "n_rows_published": int(len(df)), "keys_equal": bool((mg["_merge"] == "both").all()),
       "differing_rows": diff[["Model_pub", "benchmark_pub", "performance_pub", "performance_loader"]].astype(str).values.tolist()}
sb, _ = fit.fit("loader_input", OUT, dfb, spec=None, seed=12345, evaluate=False)
db, nmb, _ = fit.load_eci(OUT / "loader_input.nc")
assert list(nmb) == names
masks = {k: np.array([n in set(strata[k]) for n in names]) for k in ("all", "frontier", "sparse", "dense")}
w2b["converged"] = sb["converged"]; w2b["S1_S4_vs_W2a"] = sm.score(db, d12, names, masks)
for k in w2b["S1_S4_vs_W2a"]:
    if isinstance(w2b["S1_S4_vs_W2a"][k], dict): w2b["S1_S4_vs_W2a"][k].pop("p_top10_k", None); w2b["S1_S4_vs_W2a"][k].pop("p_top10_0", None)

# ---------------- EQ
log("EQ")
eq = {}
# item 1: density at 20 evenly spaced posterior draws of the seed-12345 trace
import pytensor.tensor as pt
A = eb.build_bayesian_model(df); B = models.build_model(df, models.Spec())
tr = t12["posterior"].to_dataset()
tot = tr.sizes["chain"] * tr.sizes["draw"]; keep = np.linspace(0, tot - 1, 20).astype(int)
stk = {v: tr[v].stack(s=("chain", "draw")).transpose("s", ...).to_numpy()[keep] for v in models.BASE_FREE}
cols = {}
for vv in A.value_vars:
    rv = A.values_to_rvs[vv]; trf = A.rvs_to_transforms[rv]; x = stk[rv.name]
    cols[vv.name] = np.asarray(trf.forward(pt.as_tensor(x), *rv.owner.inputs).eval()) if trf is not None else x
fa, fb = A.compile_logp(), B.compile_logp()
ga, gb = A.compile_dlogp(), B.compile_dlogp()
la = np.array([float(fa({k: v[i] for k, v in cols.items()})) for i in range(20)])
lb = np.array([float(fb({k: v[i] for k, v in cols.items()})) for i in range(20)])
eq["density"] = dict(max_abs_diff=float(np.max(np.abs(la - lb))), max_rel_diff=float(np.max(np.abs(la - lb) / np.abs(la))), logp_range=[float(la.min()), float(la.max())], requirement_abs=1e-6, passed=bool(np.max(np.abs(la - lb)) <= 1e-6))
# items 2 and 3
loo_epoch = {}
for s in (12345, 22345):
    loo_epoch[s] = fit.loo(fit.load_eci(OUT / f"seed{s}.nc")[2])
eq["fits"] = {}
for s in (12345, 22345):
    log("EQ fit F0 seed", s)
    sf, _ = fit.fit(f"f0_seed{s}", OUT, df, spec=models.Spec(), seed=s, loglik=True)
    d0, nm0, t0 = fit.load_eci(OUT / f"f0_seed{s}.nc")
    assert list(nm0) == names
    se, so = sm.summarise(draws[s]), sm.summarise(d0)
    dd = so["mean"] - se["mean"]; We = se["width"]
    wr0 = so["width"][na] / We[na]
    l0 = fit.loo(t0)
    r = dict(converged=sf["converged"], last_attempt=sf["last_attempt"], started_from=sf["started_from"], wall_seconds=sf["wall_seconds"],
             max_abs_dECI=float(np.max(np.abs(dd[na]))), max_dECI_over_tolerance=float(np.max(np.abs(dd[na]) / np.maximum(0.5, 0.07 * We[na]))),
             n_exceed=int((np.abs(dd[na]) > np.maximum(0.5, 0.07 * We[na])).sum()),
             spearman=float(spearmanr(so["mean"], se["mean"]).statistic), median_width_ratio=float(np.median(wr0)),
             share_ratio_in_085_115=float(np.mean((wr0 >= .85) & (wr0 <= 1.15))),
             elpd_loo_epoch=float(loo_epoch[s].elpd), elpd_loo_F0=float(l0.elpd), elpd_diff=float(l0.elpd - loo_epoch[s].elpd),
             se_epoch=float(loo_epoch[s].se), se_F0=float(l0.se), p_loo_epoch=float(loo_epoch[s].p), p_loo_F0=float(l0.p),
             identical_draws=bool(np.array_equal(draws[s], d0)))
    r["pass"] = bool(r["converged"] and r["n_exceed"] == 0 and r["spearman"] >= .999 and .95 <= r["median_width_ratio"] <= 1.05
                     and r["share_ratio_in_085_115"] >= .95 and abs(r["elpd_diff"]) <= 2)
    eq["fits"][str(s)] = r
eq["passed"] = bool(eq["density"]["passed"] and all(v["pass"] for v in eq["fits"].values()))

res = dict(G0=g0, G0_pass_reproduction=g0["seed12345_pass"] and g0["all_seeds_converged"], W2b=w2b, EQ=eq, settings="see settings_provenance.md")
(OUT / "reproduction.json").write_text(json.dumps(res, indent=1, default=str))
log("G0 reproduction", res["G0_pass_reproduction"], "EQ", eq["passed"])
