"""Data for curve-shape (T1) and lab-by-benchmark (T5) misfit figures (descriptive, read-only). Writes runs/W/W4fig/misspec.json."""
import sys, json, os, warnings
sys.path.insert(0, "runs"); warnings.filterwarnings("ignore")
import numpy as np, xarray as xr
from lib import data, generators as G, ppc_checks as ppc

df = data.fit_input(); scores = data.read_member(data.SCORES); el = ppc.Elig(df, scores); pat = G.Pattern(df, scores)
bn = el.bench_names
t = xr.open_datatree("runs/W/W2/seed12345.nc"); post = t["posterior"].to_dataset()
P = {v: post[v].stack(s=("chain", "draw")).transpose("s", ...).to_numpy() for v in ["capability", "difficulty", "slope", "sigma"]}
th = {k: ppc.thin(v) for k, v in P.items()}
y = np.clip(df["performance"].to_numpy(float), 1e-3, 1 - 1e-3)
rq = ppc.residual_quantities(th, el); z = (y - rq["mubar"]) / np.sqrt(rq["v"])
chat = rq["chat"]; _, comp, _ = ppc.stats(y, rq, el)

# T1: three benchmarks with the largest Q_b, plus one typical benchmark; points and fitted curve band
Qb = dict(zip([bn[b] for b in el.t1_bench], comp["Qb"]))
top = sorted(Qb, key=Qb.get, reverse=True)[:3]
med = sorted(Qb, key=Qb.get)[len(Qb) // 2]
cgrid = np.linspace(chat.min() - .5, chat.max() + .5, 120)
curves = []
for name in top + [med]:
    b = bn.index(name); rows = el.rows_of_bench[b]
    mu = 1 / (1 + np.exp(-th["slope"][:, b, None] * (cgrid[None, :] - th["difficulty"][:, b, None])))
    q = np.quantile(mu, [.05, .5, .95], axis=0)
    order = rows[np.argsort(chat[el.mi[rows]], kind="stable")]
    quart = [dict(c=float(chat[el.mi[g]].mean()), zbar=float(z[g].mean()), n=len(g)) for g in np.array_split(order, 4)]
    lo, hi = chat[el.mi[rows]].min() - .3, chat[el.mi[rows]].max() + .3; keep = (cgrid >= lo) & (cgrid <= hi)
    curves.append(dict(name=name, Qb=float(Qb[name]), rank_note="median benchmark" if name == med else "",
                       pts=[[round(float(chat[el.mi[r]]), 3), round(float(y[r]), 4), el.model_names[el.mi[r]]] for r in rows],
                       grid=cgrid[keep].round(3).tolist(), q05=q[0][keep].round(4).tolist(), q50=q[1][keep].round(4).tolist(), q95=q[2][keep].round(4).tolist(),
                       quart=quart))

# T5: all cells, real t and a typical null's t (same null replicate as structure.json)
st = json.load(open("runs/W/W4fig/structure.json")); r = st["typical_null_rep"]
d = json.load(open(f"runs/W/W3/rep/null_{r}.json")); S = P["capability"].shape[0]
theta = {k: P[k][d["position"]] for k in P}
yn, _ = G.simulate("null", r, theta, pat); yn = np.clip(yn, 1e-3, 1 - 1e-3)
nc = f"runs/W/W3/rep/null_{r}.nc"
if not os.path.exists(nc): nc = f"runs/W/W4d/null_refit/rep/null_{r}.nc"
ds = xr.open_dataset(nc); thr = {k: ds[k].to_numpy() for k in ("capability", "difficulty", "slope", "sigma")}
_, compn, _ = ppc.stats(yn, ppc.residual_quantities(thr, el), el)
cells = [dict(org=o, b=bn[b], n=len(rr), t=round(float(tt), 3), tn=round(float(tn), 3))
         for ((o, b), rr), tt, tn in zip(el.cells, comp["t"], compn["t"])]
out = dict(curves=curves, cells=cells, t_thresh=3.593381842259049, typical_null_rep=r)
json.dump(out, open("runs/W/W4fig/misspec.json", "w"), default=float)
print("top Qb", [(c["name"], round(c["Qb"], 1)) for c in curves], "cells", len(cells), "orgs", sorted({c["org"] for c in cells}))
