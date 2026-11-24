"""Read-only localisation of T1/T2/T5 from the W2 posterior (same calls as w4_ppc.py). Writes runs/W/W4/localisation.json."""
import sys, json, warnings
from pathlib import Path
sys.path.insert(0, "runs"); warnings.filterwarnings("ignore")
import numpy as np, xarray as xr
from lib import data, ppc_checks as ppc
df = data.fit_input(); scores = data.read_member(data.SCORES); el = ppc.Elig(df, scores)
t = xr.open_datatree("runs/W/W2/seed12345.nc"); post = t["posterior"].to_dataset()
pooled = {v: post[v].stack(s=("chain", "draw")).transpose("s", ...).to_numpy() for v in ["capability", "difficulty", "slope", "sigma"]}
th = {k: ppc.thin(v) for k, v in pooled.items()}
y = np.clip(df["performance"].to_numpy(float), 1e-3, 1 - 1e-3)
rq = ppc.residual_quantities(th, el); T, comp, mx = ppc.stats(y, rq, el)
bn = el.bench_names; out = {}
Qb = comp["Qb"]; o = np.argsort(-Qb)[:8]
out["T1_top_benchmarks"] = [dict(benchmark=bn[el.t1_bench[j]], n=int(len(el.rows_of_bench[el.t1_bench[j]])), Qb=float(Qb[j])) for j in o]
out["T1_Qb_mean"] = float(Qb.mean()); out["T1_Qb_median"] = float(np.median(Qb)); out["T1_share_Qb_gt_9.49"] = float((Qb > 9.49).mean())
q = comp["q"]; o = np.argsort(-q)[:10]
out["T2_top_pairs"] = [dict(a=bn[el.pairs[j][0]], b=bn[el.pairs[j][1]], n_shared=int(len(el.pairs[j][2])), q=float(q[j])) for j in o]
out["T2_median_q"] = float(np.median(q)); out["T2_share_q_gt_3.84"] = float((q > 3.84).mean())
# benchmark involvement: mean q over pairs containing each benchmark
inv = {}
for j, (a, b, _, _) in enumerate(el.pairs):
    for k in (a, b): inv.setdefault(k, []).append(q[j])
rk = sorted(inv, key=lambda k: -np.mean(inv[k]))[:8]
out["T2_benchmarks_by_mean_q"] = [dict(benchmark=bn[k], n_pairs=len(inv[k]), mean_q=float(np.mean(inv[k]))) for k in rk]
tt = comp["t"]; o = np.argsort(-np.abs(tt))[:10]
out["T5_top_cells"] = [dict(org=str(el.cells[j][0][0]), benchmark=bn[el.cells[j][0][1]], n=int(len(el.cells[j][1])), t=float(tt[j])) for j in o]
out["T5_share_abs_t_gt_2"] = float((np.abs(tt) > 2).mean())
Path("runs/W/W4/localisation.json").write_text(json.dumps(out, indent=1)); print(json.dumps(out, indent=1))
