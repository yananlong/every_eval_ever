"""Calibrated max-T p for a W7 candidate against its own model-true replicates (runs/W/W7/rep/<cand>/r*.json, from
runs/w7_rep.py), with the frozen lib/ppc_checks.max_t. Non-converged replicates are counted and excluded, as W3 does.
Replicate distributions are summarised with az.eti (90%) on a DataTree of the replicate T values.
Usage: w7_calib.py CAND [R]"""
import sys, json
from pathlib import Path
sys.path[:0] = ["runs/vendor/eci-public/src", "runs"]
import numpy as np, xarray as xr, arviz as az
from lib import ppc_checks as ppc

cand = sys.argv[1]; R = int(sys.argv[2]) if len(sys.argv) > 2 else 120
reps = [json.loads(p.read_text()) for p in sorted((Path("runs/W/W7/rep") / cand).glob("r*.json"))]
conv = [r for r in reps if r["converged"]]
obs = json.loads(Path(f"runs/W/W7/{cand}_ppc.json").read_text())["T"]
res = ppc.max_t(obs, [r["T"] for r in conv])
ds = xr.Dataset({k: (("chain", "draw"), [[r["T"][k] for r in conv]]) for k in ppc.TNAMES})
eti = az.eti(xr.DataTree.from_dict({"posterior": ds}), prob=0.9)
eti = eti.to_dataset() if isinstance(eti, xr.DataTree) else eti
out = dict(cand=cand, R_planned=R, finished=len(reps), converged=len(conv),
           timeouts_or_failed=R - len(reps), not_converged=len(reps) - len(conv),
           wall_median_s=float(np.median([r["wall_seconds"] for r in reps])) if reps else None,
           max_t=res, rep_eti90={k: [float(x) for x in eti[k].to_numpy()] for k in ppc.TNAMES},
           rejected_at_0_01=[k for k in ppc.TNAMES if res[k]["p_adjusted"] < 0.01])
Path(f"runs/W/W7/{cand}_calib.json").write_text(json.dumps(out, indent=1))
print(cand, f"{len(conv)}/{R} converged ({len(reps)} finished)")
for k in ppc.TNAMES:
    print(f"  {k} obs {obs[k]:.3f} rep90 {out['rep_eti90'][k][0]:.3f}-{out['rep_eti90'][k][1]:.3f} p_unadj {res[k]['p_unadjusted']:.4f} p_adj {res[k]['p_adjusted']:.4f}")
print("  rejected at 0.01:", out["rejected_at_0_01"] or "none")
