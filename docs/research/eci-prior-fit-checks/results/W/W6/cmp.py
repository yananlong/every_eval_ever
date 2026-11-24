"""Interim W6 comparison: PSIS-LOO and, where complete, K-fold deltas against F0 (same rules as w6_expand)."""
import sys; sys.path[:0] = ["runs/vendor/eci-public/src", "runs"]
import json, numpy as np, pandas as pd, xarray as xr, warnings; warnings.filterwarnings("ignore")
from pathlib import Path
from lib import compare
L0 = compare.loo_stats(xr.open_datatree("runs/W/W2/f0_seed12345.nc"))
fold = pd.read_csv("runs/W/W4/folds.csv")["fold"].to_numpy(); elig = np.where(fold >= 0)[0]
f0kf = pd.read_csv("runs/W/W4/fold_logdens_F0.csv").set_index("row")["logdens_F0"]
res = {}
for n, d in [(a.split("/")[-1], a) for a in sys.argv[1:]]:
    nc = Path(d + ".nc"); side = json.loads(Path(d + ".json").read_text())
    e = dict(converged=side["converged"], wall=side["wall_seconds"])
    if not side["converged"]: res[n] = e; print(n, e); continue
    L = compare.loo_stats(xr.open_datatree(nc)); e.update(elpd=L["elpd"], p=L["p"], k_share=L["k_share"])
    e["loo_delta"], e["loo_se"] = compare.paired(L["elpd_i"], L0["elpd_i"])
    e["kfold_trig"] = bool(compare.kfold_trigger(L0["k_share"], L["k_share"]))
    kd = Path(d).parent / "kfold"; ld = {}; conv = []
    for f in range(5):
        z = kd / f"{n}_fold{f}.npz"
        if z.exists(): z = np.load(z); ld.update(dict(zip(z["rows"].tolist(), z["logd"].tolist()))); conv.append(bool(z["converged"]))
    if len(ld) == len(elig):
        dj = np.array([ld[r] for r in elig]) - f0kf.loc[elig].to_numpy(); e["kfold_delta"], e["kfold_se"] = float(dj.sum()), float(np.sqrt(len(dj)) * dj.std(ddof=1)); e["kfold_conv"] = conv
    est = ("kfold_delta", "kfold_se") if e["kfold_trig"] else ("loo_delta", "loo_se")
    if est[0] in e: e["preferred"] = compare.preferred(e[est[0]], e[est[1]])
    res[n] = e; print(n, {k: (round(v, 2) if isinstance(v, float) else v) for k, v in e.items()})
json.dump(res, open("runs/W/W6/interim_cmp.json", "w"), indent=1, default=float)
