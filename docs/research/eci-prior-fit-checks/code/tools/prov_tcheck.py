"""PROV validation of the per-refit T1-T7 code path: the same calls on the W2 seed-12345 posteriors of the Epoch-data and EEE-data fits, to compare with the
published W4 observed values (Epoch T5 4.455, EEE T5 3.861, T3 0.081 / 0.090).  Writes runs/EEE/PROV/tcheck.json.  Run from the v11 root."""
import sys, json, warnings; warnings.filterwarnings("ignore")
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np, pandas as pd, xarray as xr
import prov_common as P
from lib import data, ppc_checks as ppc
def nulls(path):
    return [x["T"] for x in (json.loads(f.read_text()) for f in Path(path).glob("rep/null_*.json")) if x.get("converged")]
scores = data.read_member(data.SCORES); out = {}
for lab, nc, csv in (("epoch", "runs/W/W2/seed12345.nc", None), ("eee", "runs/EEE/W2/seed12345.nc", "runs/EEE/input/processed_data_for_eci.csv")):
    df = data.fit_input() if csv is None else pd.read_csv(csv)
    el = ppc.Elig(df, scores); t = xr.open_datatree(nc); post = t["posterior"].to_dataset()
    th = {v: ppc.thin(post[v].stack(s=("chain", "draw")).transpose("s", ...).to_numpy()) for v in ("capability", "difficulty", "slope", "sigma")}
    y = np.clip(df["performance"].to_numpy(dtype=float), ppc.EPS, 1 - ppc.EPS)
    rq = ppc.residual_quantities(th, el); Tobs, comp, mx = ppc.stats(y, rq, el)
    out[lab] = dict(observed=Tobs, p_adj_eee_null=ppc.max_t(Tobs, nulls("runs/EEE/W3")), p_adj_epoch_null=ppc.max_t(Tobs, nulls("runs/W/W3")))
    print(lab, {k: round(v, 3) for k, v in Tobs.items()}, {k: round(out[lab]["p_adj_" + ("eee" if lab == "eee" else "epoch") + "_null"][k]["p_adjusted"], 4) for k in ppc.TNAMES})
Path("runs/EEE/PROV/tcheck.json").write_text(json.dumps(out, indent=1, default=str))
