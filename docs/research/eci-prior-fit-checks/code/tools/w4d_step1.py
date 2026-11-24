"""W4d step 1-2: null thresholds (99th pct of per-replicate max component) and F from real-data components."""
import sys, json, glob, warnings
sys.path.insert(0, "runs"); warnings.filterwarnings("ignore")
import numpy as np, xarray as xr
from lib import data, ppc_checks as ppc
null = [json.load(open(p)) for p in sorted(glob.glob("runs/W/W3/rep/null_*.json"))]
null = [x for x in null if x["converged"]]
th99 = {k: float(np.quantile([x["maxima"][k] for x in null], 0.99)) for k in ("Qb", "q", "t", "cb")}
df = data.fit_input(); scores = data.read_member(data.SCORES); el = ppc.Elig(df, scores)
t = xr.open_datatree("runs/W/W2/seed12345.nc"); post = t["posterior"].to_dataset()
pooled = {v: post[v].stack(s=("chain", "draw")).transpose("s", ...).to_numpy() for v in ["capability", "difficulty", "slope", "sigma"]}
th = {k: ppc.thin(v) for k, v in pooled.items()}
y = np.clip(df["performance"].to_numpy(float), 1e-3, 1 - 1e-3)
rq = ppc.residual_quantities(th, el); T, comp, mx = ppc.stats(y, rq, el)
bn = el.bench_names; F = {}
def add(b, why): F.setdefault(bn[b], []).append(why)
ext = dict(Qb=[], q=[], t=[], cb=[])
for j, b in enumerate(el.t1_bench):
    if comp["Qb"][j] > th99["Qb"]: ext["Qb"].append((bn[b], float(comp["Qb"][j]))); add(b, f"T1 Qb={comp['Qb'][j]:.2f}>{th99['Qb']:.2f}")
for j, (a, b, ra, rb) in enumerate(el.pairs):
    if comp["q"][j] > th99["q"]: ext["q"].append((bn[a], bn[b], float(comp["q"][j]))); add(a, f"T2 pair with {bn[b]} q={comp['q'][j]:.2f}>{th99['q']:.2f}"); add(b, f"T2 pair with {bn[a]} q={comp['q'][j]:.2f}>{th99['q']:.2f}")
for j, ((o, b), rows) in enumerate(el.cells):
    if abs(comp["t"][j]) > th99["t"]: ext["t"].append((str(o), bn[b], float(comp["t"][j]))); add(b, f"T5 cell ({o}) t={comp['t'][j]:.2f}, |t|>{th99['t']:.2f}")
for b in range(el.K):
    if comp["cb"][b] > th99["cb"]: ext["cb"].append((bn[b], float(comp["cb"][b]))); add(b, f"T6 cb={comp['cb'][b]:.2f}>{th99['cb']:.2f}")
out = dict(n_null=len(null), thresholds_99=th99, T_obs=T, obs_maxima=mx, extreme_components=ext, F=F, n_F=len(F),
           n_components=dict(Qb=len(comp["Qb"]), q=len(comp["q"]), t=len(comp["t"]), cb=len(comp["cb"])),
           top3=dict(Qb=sorted(comp["Qb"])[-3:], q=sorted(comp["q"])[-3:], t=sorted(np.abs(comp["t"]))[-3:], cb=sorted(comp["cb"])[-3:]))
json.dump(out, open("runs/W/W4d/step1.json", "w"), indent=1, default=float); print(json.dumps(out, indent=1, default=float))
