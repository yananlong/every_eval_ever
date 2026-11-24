"""W5 residual checks T1-T7 (R29/R30, exploratory, no verdict) on each prior arm's real-data fit, ranked against the W3 converged G-null reference
(Epoch-prior refits, so approximate for every arm except Epoch's own default priors P0/P0b). Same code path as w4_ppc.py W4b (ppc_checks, 400 thinned draws).
Run from the v11 root.  Writes runs/W/W5/ppc_arms.json."""
import sys, json, warnings
from pathlib import Path
sys.path.insert(0, str(Path("runs").resolve())); warnings.filterwarnings("ignore")
import numpy as np, xarray as xr
from lib import data, ppc_checks as ppc

W3, W5 = Path("runs/W/W3"), Path("runs/W/W5")
df = data.fit_input(); scores = data.read_member(data.SCORES); el = ppc.Elig(df, scores)
y = np.clip(df["performance"].to_numpy(dtype=float), ppc.EPS, 1 - ppc.EPS)
null = [json.loads(p.read_text()) for p in W3.glob("rep/null_*.json")]; null = [x for x in null if x["converged"]]; Tn = [x["T"] for x in null]
arms = {"W2_seed12345": Path("runs/W/W2/seed12345.nc")}
for p in sorted(W5.glob("*.nc")): arms[p.stem] = p
for v in ("J1", "J2"):
    p = Path(f"runs/W/W5J/{v}/{v}.nc")
    if p.exists(): arms[v] = p
only = sys.argv[1:]
out = json.loads((W5 / "ppc_arms.json").read_text()) if (W5 / "ppc_arms.json").exists() else {}
for name, nc in arms.items():
    if only and name not in only: continue
    t = xr.open_datatree(nc); post = t["posterior"].to_dataset()
    pooled = {v: post[v].stack(s=("chain", "draw")).transpose("s", ...).to_numpy() for v in ["capability", "difficulty", "slope", "sigma"]}
    th = {k: ppc.thin(v) for k, v in pooled.items()}
    rq = ppc.residual_quantities(th, el); Tobs, comp, mx = ppc.stats(y, rq, el); mt = ppc.max_t(Tobs, Tn)
    z = (y - rq["mubar"]) / np.sqrt(rq["v"])
    out[name] = dict(n_null=len(Tn), approximate=name not in ("W2_seed12345", "P0", "P0b"), T_observed=Tobs,
                     p_unadjusted={k: mt[k]["p_unadjusted"] for k in ppc.TNAMES}, p_maxT_adjusted={k: mt[k]["p_adjusted"] for k in ppc.TNAMES},
                     rank_share_null_below={k: float(np.mean([n[k] < Tobs[k] for n in Tn])) for k in ppc.TNAMES}, n_draws_used=int(th["capability"].shape[0]))
    print(name, {k: (round(Tobs[k], 3), round(mt[k]["p_adjusted"], 4)) for k in ppc.TNAMES}, flush=True)
(W5 / "ppc_arms.json").write_text(json.dumps(out, indent=1))
