"""Benchmark parameters (EDI, scaled slope, sigma) under Epoch's model: Epoch-data fit against EEE-data fit (seed 12345).
Run from eci_work/v11. Adds 'benchmarks' to runs/EEE/eci_compare.json and writes runs/EEE/edi_compare.csv."""
import sys, json, warnings; sys.path.insert(0, "runs"); warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, xarray as xr
from scipy.stats import spearmanr
def load(nc):
    p = xr.open_datatree(nc)["posterior"].to_dataset()
    names = [str(x) for x in p["model"].values]; bn = [str(x) for x in p["benchmark"].values]
    st = lambda v, dim: p[v].stack(s=("chain", "draw")).transpose("s", dim).to_numpy()
    cap, dif, sl, sg = st("capability", "model"), st("difficulty", "benchmark"), st("slope", "benchmark"), st("sigma", "benchmark")
    lo, hi = names.index("Claude 3.5 Sonnet"), names.index("GPT-5")
    b = 20.0 / (cap[:, hi] - cap[:, lo]); a = 130.0 - b * cap[:, lo]
    return names, bn, a[:, None] + b[:, None] * dif, sl / b[:, None], sg, a[:, None] + b[:, None] * cap
nE, bE, ediE, slE, sgE, eciE = load("runs/W/W2/seed12345.nc"); nX, bX, ediX, slX, sgX, eciX = load("runs/EEE/W2/seed12345.nc")
assert bE == bX and nE == nX
ann = pd.read_csv("runs/EEE/input/eee_fit_input_annotated.csv")
key = "benchmark" if bE[0] in set(ann.benchmark) else "benchmark_id"
bid = ann.drop_duplicates(key).set_index(key, drop=False).benchmark
g = ann.groupby(key)
t = pd.DataFrame(dict(benchmark=[bid.get(b, b) for b in bE], edi_epoch=ediE.mean(0), edi_eee=ediX.mean(0), slope_epoch=slE.mean(0), slope_eee=slX.mean(0), sigma_epoch=sgE.mean(0), sigma_eee=sgX.mean(0)), index=bE)
t["edi_shift"] = t.edi_eee - t.edi_epoch; t["edi_w_epoch"] = np.quantile(ediE, .95, 0) - np.quantile(ediE, .05, 0)
t["slope_ratio"] = t.slope_eee / t.slope_epoch; t["sigma_ratio"] = t.sigma_eee / t.sigma_epoch
t["cells"] = g.size().reindex(bE).to_numpy(); t["changed"] = g.absdiff.apply(lambda s: int((s > 0.0015).sum())).reindex(bE).to_numpy()
t["mean_signed_diff"] = (ann.performance - ann.epoch_performance).groupby(ann[key]).mean().reindex(bE).to_numpy()
t.round(4).to_csv("runs/EEE/edi_compare.csv")
out = json.load(open("runs/EEE/eci_compare.json"))
out["benchmarks"] = dict(spearman_edi=float(spearmanr(t.edi_epoch, t.edi_eee).statistic), max_abs_edi_shift=float(t.edi_shift.abs().max()), argmax=str(t.benchmark[t.edi_shift.abs().idxmax()]),
                         median_abs_edi_shift=float(t.edi_shift.abs().median()), n_edi_shift_gt_2=int((t.edi_shift.abs() > 2).sum()),
                         sigma_ratio_median=float(t.sigma_ratio.median()), sigma_ratio_max=float(t.sigma_ratio.max()), sigma_argmax=str(t.benchmark[t.sigma_ratio.idxmax()]),
                         slope_ratio_min=float(t.slope_ratio.min()), slope_ratio_max=float(t.slope_ratio.max()),
                         top=t.reindex(t.edi_shift.abs().sort_values(ascending=False).index).head(10)[["benchmark", "edi_epoch", "edi_eee", "edi_shift", "slope_ratio", "sigma_ratio", "cells", "changed", "mean_signed_diff"]].round(3).to_dict("records"),
                         top_sigma=t.sort_values("sigma_ratio", ascending=False).head(6)[["benchmark", "sigma_epoch", "sigma_eee", "sigma_ratio", "cells", "changed"]].round(3).to_dict("records"))
# where on the scale do the shifts sit: mean shift by Epoch-ECI band
m = eciE.mean(0); d = eciX.mean(0) - m; anc = np.isin(nE, ["Claude 3.5 Sonnet", "GPT-5"])
bands = [(-1e9, 80), (80, 100), (100, 120), (120, 140), (140, 160), (160, 1e9)]
out["shift_by_band"] = [dict(band=f"{lo if lo > -1e8 else 'below'}-{hi if hi < 1e8 else 'above'}", n=int(((m >= lo) & (m < hi) & ~anc).sum()), mean_shift=float(d[(m >= lo) & (m < hi) & ~anc].mean()), max_abs=float(np.abs(d[(m >= lo) & (m < hi) & ~anc]).max())) for lo, hi in bands]
json.dump(out, open("runs/EEE/eci_compare.json", "w"), indent=1, default=str)
print(json.dumps(out["shift_by_band"])); print(pd.DataFrame(out["benchmarks"]["top"]).to_string()); print(pd.DataFrame(out["benchmarks"]["top_sigma"]).to_string()); print({k: v for k, v in out["benchmarks"].items() if not isinstance(v, list)})
