"""K-fold delta of a W7 candidate against F0 on the W4 folds, as runs/W/W6/cmp.py computes it (paired sum and SE over
eligible rows; compare.preferred on the K-fold estimate). Folds that are missing or did not converge are reported.
Usage: w7_kfold_cmp.py CAND"""
import sys, json
from pathlib import Path
sys.path[:0] = ["runs/vendor/eci-public/src", "runs"]
import numpy as np, pandas as pd
from lib import compare

cand = sys.argv[1]
fold = pd.read_csv("runs/W/W4/folds.csv")["fold"].to_numpy(); elig = np.where(fold >= 0)[0]
f0kf = pd.read_csv("runs/W/W4/fold_logdens_F0.csv").set_index("row")["logdens_F0"]
ld, conv, have = {}, {}, []
for k in range(5):
    z = Path("runs/W/W7/kfold") / f"{cand}_fold{k}.npz"
    if z.exists():
        z = np.load(z); ld.update(dict(zip(z["rows"].tolist(), z["logd"].tolist()))); conv[k] = bool(z["converged"]); have.append(k)
out = dict(cand=cand, folds_present=have, folds_converged=conv)
rows = np.array([r for r in elig if r in ld])
if len(rows):
    dj = np.array([ld[r] for r in rows]) - f0kf.loc[rows].to_numpy()
    out.update(n_rows=int(len(rows)), n_eligible=int(len(elig)), kfold_delta=float(dj.sum()), kfold_se=float(np.sqrt(len(dj)) * dj.std(ddof=1)),
               complete=bool(len(rows) == len(elig)))
    out["preferred"] = bool(compare.preferred(out["kfold_delta"], out["kfold_se"]))
Path(f"runs/W/W7/{cand}_kfold.json").write_text(json.dumps(out, indent=1)); print(out)
