"""Data for the 'structure misfit' figures (descriptive, read-only). Writes runs/W/W4fig/structure.json:
residual correlation per T2 pair for the real data and for every converged G-null replicate (same posteriors as W4d),
a clustered benchmark order, residual scatter data for two example pairs, and the null distributions of T1, T2, T5."""
import sys, json, glob, os, warnings
sys.path.insert(0, "runs"); warnings.filterwarnings("ignore")
import numpy as np, xarray as xr
from scipy.cluster.hierarchy import linkage, leaves_list
from scipy.spatial.distance import squareform
from lib import data, generators as G, ppc_checks as ppc

df = data.fit_input(); scores = data.read_member(data.SCORES); el = ppc.Elig(df, scores); pat = G.Pattern(df, scores)
bn = el.bench_names

def zres(y, th):
    rq = ppc.residual_quantities(th, el); return (y - rq["mubar"]) / np.sqrt(rq["v"])

def pair_r(z):
    out = []
    for a, b, ra, rb in el.pairs:
        r = np.corrcoef(z[ra], z[rb])[0, 1]; out.append(float(r) if np.isfinite(r) else 0.0)
    return np.array(out)

t = xr.open_datatree("runs/W/W2/seed12345.nc"); post = t["posterior"].to_dataset()
P = {v: post[v].stack(s=("chain", "draw")).transpose("s", ...).to_numpy() for v in ["capability", "difficulty", "slope", "sigma"]}
th = {k: ppc.thin(v) for k, v in P.items()}
yobs = np.clip(df["performance"].to_numpy(float), 1e-3, 1 - 1e-3)
zobs = zres(yobs, th); robs = pair_r(zobs)
S = P["capability"].shape[0]

null_r, null_T, null_z = [], [], {}
for p in sorted(glob.glob("runs/W/W3/rep/null_*.json"), key=lambda s: int(s.split("_")[-1][:-5])):
    d = json.load(open(p))
    if not d["converged"]: continue
    null_T.append(dict(r=d["r"], **{k: d["T"][k] for k in ("T1", "T2", "T5")}))
    r = d["r"]; nc = f"runs/W/W3/rep/null_{r}.nc"
    if not os.path.exists(nc):
        nc = f"runs/W/W4d/null_refit/rep/null_{r}.nc"; js = f"runs/W/W4d/null_refit/rep/null_{r}.json"
        if not (os.path.exists(nc) and json.load(open(js))["converged"]): continue
    theta = {k: P[k][d["position"]] for k in P}
    y, _ = G.simulate("null", r, theta, pat); y = np.clip(y, 1e-3, 1 - 1e-3)
    ds = xr.open_dataset(nc); thr = {k: ds[k].to_numpy() for k in ("capability", "difficulty", "slope", "sigma")}
    z = zres(y, thr); rr = pair_r(z); null_r.append(rr); null_z[r] = z
null_r = np.array(null_r)

# benchmarks appearing in at least one pair; clustered order from the real correlation matrix
bset = sorted({a for a, *_ in el.pairs} | {b for _, b, *_ in el.pairs})
ix = {b: i for i, b in enumerate(bset)}; n = len(bset)
C = np.zeros((n, n))
for (a, b, *_), r in zip(el.pairs, robs): C[ix[a], ix[b]] = C[ix[b], ix[a]] = r
D = 1 - C; np.fill_diagonal(D, 0); D = np.clip(D, 0, 2)
order = [bset[i] for i in leaves_list(linkage(squareform(D, checks=False), "average"))]

# a typical null: T2 closest to the null median among those with residuals
q_null = [(len(ra) - 3) * np.arctanh(np.clip(null_r[:, k], -.999, .999)) ** 2 for k, (a, b, ra, rb) in enumerate(el.pairs)]
T2_null = np.mean(np.array(q_null), axis=0)
typ = int(np.argmin(np.abs(T2_null - np.median(T2_null))))

def scatter(na, nb, z):
    a, b = bn.index(na), bn.index(nb)
    for pa, pb, ra, rb in el.pairs:
        if {pa, pb} == {a, b}:
            if pa != a: ra, rb = rb, ra
            return dict(a=na, b=nb, x=z[ra].round(3).tolist(), y=z[rb].round(3).tolist(),
                        models=[el.model_names[m] for m in el.mi[ra]], r=float(np.corrcoef(z[ra], z[rb])[0, 1]))

typ_r_key = list(null_z.keys())[typ]
ex = [("FrontierMath-Tiers-1-3-v2-Private", "FrontierMath-Tier-4-v2-Private"), ("ARC-AGI", "ARC-AGI-2"), ("HellaSwag", "TriviaQA")]
ppcj = json.load(open("runs/W/W4/ppc.json"))
out = dict(
    benchmarks=[bn[b] for b in order],
    pairs=[dict(a=bn[a], b=bn[b], n=len(ra), r=round(float(r), 4), r_null_typ=round(float(null_r[typ, k]), 4),
                null_sd=round(float(null_r[:, k].std()), 4), null_mean=round(float(null_r[:, k].mean()), 4))
           for k, ((a, b, ra, rb), r) in enumerate(zip(el.pairs, robs))],
    n_null=len(null_r), typical_null_rep=int(typ_r_key),
    null_r_pooled_hist=np.histogram(null_r.ravel(), bins=np.linspace(-1, 1, 41))[0].tolist(),
    obs_r_hist=np.histogram(robs, bins=np.linspace(-1, 1, 41))[0].tolist(), hist_edges=np.linspace(-1, 1, 41).round(3).tolist(),
    scatter=dict(obs=[scatter(a, b, zobs) for a, b in ex], null=[scatter(a, b, null_z[typ_r_key]) for a, b in ex]),
    T_null=null_T, T_obs={k: ppcj["W4b"]["T_obs"][k] if "T_obs" in ppcj["W4b"] else None for k in ("T1", "T2", "T5")},
)
os.makedirs("runs/W/W4fig", exist_ok=True)
json.dump(out, open("runs/W/W4fig/structure.json", "w"), default=float)
print("pairs", len(out["pairs"]), "bench", n, "nulls", len(null_r), "typ", typ_r_key, "T_obs", out["T_obs"],
      "share |r|>0.3 obs", float(np.mean(np.abs(robs) > .3)), "null", float(np.mean(np.abs(null_r) > .3)),
      "mean r obs", float(robs.mean()), "null", float(null_r.mean()))
