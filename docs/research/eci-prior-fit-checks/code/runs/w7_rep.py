"""One model-true replicate of a W7 candidate, as W3 does for F0: take posterior draw floor(r S / R) of the
candidate's fit to Epoch's data, simulate Beta scores from its mean and concentration, refit the same candidate
(same features, same target acceptance) through Epoch's fit, and compute T1-T7 of the replicate under its own refit.
Only the json is kept: the refit runs in memory (runs/w7_memfit.py) and writes no trace. Usage: w7_rep.py --cand G5 --features dev,fam,f1r,skew --r 0 --R 120 [--target-accept 0.95]"""
import sys, argparse, json, hashlib, os, warnings
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); warnings.filterwarnings("ignore")
import numpy as np, xarray as xr
import w7_models as w7, w7_data, w7_ppc, w7_memfit
from lib import data, models, fit as fitmod, ppc_checks as ppc
ap = argparse.ArgumentParser()
ap.add_argument("--cand", required=True); ap.add_argument("--features", required=True); ap.add_argument("--r", type=int, required=True)
ap.add_argument("--R", type=int, default=120); ap.add_argument("--target-accept", type=float, default=0.95)
ap.add_argument("--src", default=None)   # the candidate's fit to Epoch's data; default runs/W/W7/<cand>.nc
a = ap.parse_args()
feats = tuple(f for f in a.features.split(",") if f)
OUT = Path("runs/W/W7/rep") / a.cand; OUT.mkdir(parents=True, exist_ok=True)
js = OUT / f"r{a.r}.json"
if js.exists(): print("exists", js); sys.exit(0)
w7.install()
import eci.bayesian as eb
_orig = eb.fit_bayesian_eci
eb.fit_bayesian_eci = lambda *x, **k: _orig(*x, **{**k, "target_accept": a.target_accept})
df, ex = w7_data.load("orig")
P_all, _ = w7_ppc.post_arrays(Path(a.src or f"runs/W/W7/{a.cand}.nc"), feats, n=10 ** 9)
S = P_all["capability"].shape[0]; pos = int(np.floor(a.r * S / a.R))
seed = int.from_bytes(hashlib.sha256(f"w7:{a.cand}:{a.r}".encode()).digest()[:4], "big")
mu, kap = w7.mu_kappa(feats, {k: v[pos:pos + 1] for k, v in P_all.items()}, df, ex)
y = np.random.default_rng(seed).beta(mu[0] * kap[0], (1 - mu[0]) * kap[0])
dr = df.copy(); dr["performance"] = y
side, tr = w7_memfit.fit_mem(dr, models.Spec(feats), seed % (2 ** 31), ex)
P, _ = w7_ppc.post_arrays(tr, feats)
el = ppc.Elig(df, data.read_member(data.SCORES))
m2, k2 = w7.mu_kappa(feats, P, dr, ex)
T, comp, mx = ppc.stats(np.clip(y, 1e-3, 1 - 1e-3), w7_ppc.rq_from(m2, k2, P), el)
res = dict(cand=a.cand, r=a.r, R=a.R, position=pos, seed=seed, converged=side["converged"], last_attempt=side["last_attempt"],
           started_from=side["started_from"], wall_seconds=side["wall_seconds"], T=T, maxima=mx)
tmp = OUT / f".r{a.r}.json.tmp"; tmp.write_text(json.dumps(res, indent=1, default=float)); os.replace(tmp, js)
print("DONE", a.cand, a.r, side["converged"], {k: round(v, 3) for k, v in T.items()}, flush=True)
