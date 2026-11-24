"""W4d step 3: deletion test (no refit). Delete rows of benchmarks in F from the residual table for the observed data and every converged G-null replicate,
recompute T1..T7 with the M5 definitions on the remaining rows (eligibility sets fixed from the full real observation pattern, minus anything touching F),
unadjusted p against the nulls. Null posteriors: W3 rep/null_r.nc if present else the W4d refit runs/W/W4d/null_refit/rep/null_r.nc."""
import sys, json, glob, os, copy, warnings
sys.path.insert(0, "runs"); warnings.filterwarnings("ignore")
import numpy as np, xarray as xr
from lib import data, generators as G, ppc_checks as ppc
df = data.fit_input(); scores = data.read_member(data.SCORES); el = ppc.Elig(df, scores); pat = G.Pattern(df, scores)
st1 = json.load(open("runs/W/W4d/step1.json")); Fnames = list(st1["F"]); bn = el.bench_names
Fb = {bn.index(n) for n in Fnames}
keep = ~np.isin(el.bi, list(Fb)); newidx = -np.ones(el.N, int); newidx[keep] = np.arange(keep.sum())
def remap(rows): r = newidx[rows]; return r
sub = copy.copy(el)
sub.mi = el.mi[keep]; sub.bi = el.bi[keep]; sub.N = int(keep.sum()); sub.gap = el.gap[keep]
sub.t1_bench = np.array([b for b in el.t1_bench if b not in Fb])
sub.rows_of_bench = [np.array([], int) if b in Fb else remap(el.rows_of_bench[b]) for b in range(el.K)]
sub.pairs = [(a, b, remap(ra), remap(rb)) for a, b, ra, rb in el.pairs if a not in Fb and b not in Fb]
sub.cells = [(k, remap(r)) for k, r in el.cells if k[1] not in Fb]
sub.rows_of_model = [remap(r[keep[r]]) for r in el.rows_of_model]
sub.t7_models = np.array([m for m in el.t7_models if len(sub.rows_of_model[m]) >= 6])
sub_info = dict(rows_kept=int(keep.sum()), rows_deleted=int((~keep).sum()), T1_benchmarks=len(sub.t1_bench), T2_pairs=len(sub.pairs), T5_cells=len(sub.cells), T7_models=len(sub.t7_models))
def sub_rq(rq): return dict(mubar=rq["mubar"][keep], v=rq["v"][keep], chat=rq["chat"], p0=rq["p0"][keep], p1=rq["p1"][keep])
def both(y, th):
    rq = ppc.residual_quantities(th, el); full = ppc.stats(y, rq, el, with_components=False)
    dele = ppc.stats(y[keep], sub_rq(rq), sub, with_components=False); return full, dele
# observed
t = xr.open_datatree("runs/W/W2/seed12345.nc"); post = t["posterior"].to_dataset()
P = {v: post[v].stack(s=("chain", "draw")).transpose("s", ...).to_numpy() for v in ["capability", "difficulty", "slope", "sigma"]}
th = {k: ppc.thin(v) for k, v in P.items()}
yobs = np.clip(df["performance"].to_numpy(float), 1e-3, 1 - 1e-3)
Tobs_full, Tobs_del = both(yobs, th)
assert all(abs(Tobs_full[k] - st1["T_obs"][k]) < 1e-9 for k in ppc.TNAMES)
# W2 pooled with hyperparameters for the generator positions
pooled = {v: post[v].stack(s=("chain", "draw")).transpose("s", ...).to_numpy() for v in ["capability", "difficulty", "slope", "sigma"]}
S = pooled["capability"].shape[0]
rows = []
for p in sorted(glob.glob("runs/W/W3/rep/null_*.json"), key=lambda s: int(s.split("_")[-1][:-5])):
    d = json.load(open(p))
    if not d["converged"]: continue
    r = d["r"]; src = "W3"; nc = f"runs/W/W3/rep/null_{r}.nc"
    if not os.path.exists(nc): src = "refit"; nc = f"runs/W/W4d/null_refit/rep/null_{r}.nc"
    if not os.path.exists(nc): rows.append(dict(r=r, missing=True)); continue
    if src == "refit" and not json.load(open(f"runs/W/W4d/null_refit/rep/null_{r}.json"))["converged"]: rows.append(dict(r=r, missing=True, refit_nonconverged=True)); continue
    assert G.position("null", r, S) == d["position"] and G.seed_of("null", r) == d["seed"]
    theta = {k: pooled[k][d["position"]] for k in pooled}
    y, _ = G.simulate("null", r, theta, pat); y = np.clip(y, 1e-3, 1 - 1e-3)
    ds = xr.open_dataset(nc); thr = {k: ds[k].to_numpy() for k in ("capability", "difficulty", "slope", "sigma")}
    full, dele = both(y, thr)
    rows.append(dict(r=r, src=src, full=full, dele=dele, committed=d["T"] if src == "W3" else None))
    if src == "refit":
        rj = f"runs/W/W4d/null_refit/rep/null_{r}.json"
        rows[-1]["refit_json_T"] = json.load(open(rj))["T"]; rows[-1]["refit_converged"] = json.load(open(rj))["converged"]
    rows[-1]["committed"] = d["T"]
miss = [x["r"] for x in rows if x.get("missing")]; rows = [x for x in rows if not x.get("missing")]
# validation: recomputed full T vs the committed (W3) T, per source
def rel(a, b): return abs(a - b) / max(abs(b), 1e-12)
val = {}
for src in ("W3", "refit"):
    xs = [x for x in rows if x["src"] == src]
    if not xs: continue
    per = {k: max(rel(x["full"][k], x["committed"][k]) for x in xs) for k in ppc.TNAMES}
    med = {k: float(np.median([rel(x["full"][k], x["committed"][k]) for x in xs])) for k in ppc.TNAMES}
    val[src] = dict(n=len(xs), max_rel_diff_full_T_vs_committed=per, median_rel_diff=med, max_overall=max(per.values()))
def ptable(sel):
    if not sel: return None
    out = {}
    for k in ("T1", "T2", "T3", "T4", "T5", "T6", "T7"):
        nv = np.array([x["dele"][k] for x in sel]); nf = np.array([x["full"][k] for x in sel])
        out[k] = dict(obs_full=Tobs_full[k], p_full=float((1 + (nf >= Tobs_full[k]).sum()) / (len(sel) + 1)),
                      obs_deleted=Tobs_del[k], p_unadjusted_deleted=float((1 + (nv >= Tobs_del[k]).sum()) / (len(sel) + 1)),
                      null_median_deleted=float(np.median(nv)), null_max_deleted=float(nv.max()))
    return out
res = dict(F=Fnames, n_F=len(Fnames), sub_info=sub_info, n_null_used=len(rows), missing=miss, validation=val,
           primary_all_converged_nulls=ptable(rows), subset_W3_nc_only=ptable([x for x in rows if x["src"] == "W3"]),
           subset_refit_only=ptable([x for x in rows if x["src"] == "refit"]))
if any(x["src"] == "refit" for x in rows):
    res["refit_converged_share"] = float(np.mean([x["refit_converged"] for x in rows if x["src"] == "refit"]))
json.dump(res, open("runs/W/W4d/deletion_test.json", "w"), indent=1, default=float); print(json.dumps(res, indent=1, default=float))
