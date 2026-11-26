"""No-fit check on the augmented input under Epoch's fitted model P0 (runs/W/W2/seed12345.nc), exploratory.
For each cell with an EEE value distinct from Epoch's, compare the source disagreement d = y_EEE - y_Epoch with what
the model's Beta noise implies for two independent draws of the same cell: E[d^2] = 2 mu (1 - mu) / (kappa + 1).
  ratio  = sum d^2 / sum E[d^2]   (1 = sources disagree as much as the model's noise; near 0 = the noise term is
           mostly stable across sources, i.e. cell-level lack of fit rather than measurement noise)
  r_res  = correlation of the standardised residuals of the Epoch value and the EEE value of the same cell
           (0 under the model).
Replicates draw both values fresh from Beta(mu kappa, (1 - mu) kappa) at the same posterior draw.
Posterior draws come from az.extract (500 evenly spaced draws, as before); 90% ranges from az.eti."""
import sys, json
from pathlib import Path
sys.path[:0] = ["runs/vendor/eci-public/src", "runs"]
import numpy as np, pandas as pd, xarray as xr, arviz as az
from lib import models, expand

OUT = Path("runs/AUG"); rng = np.random.default_rng(2026112400)
t = xr.open_datatree("runs/W/W2/seed12345.nc")
st = az.extract(t, var_names=["capability", "difficulty", "slope", "sigma"]); S = st.sizes["sample"]; pick = np.linspace(0, S - 1, 500).astype(int)
P = {k: st[k].transpose("sample", ...).to_numpy()[pick] for k in ("capability", "difficulty", "slope", "sigma")}
q90 = lambda x: [float(v) for v in az.eti(np.asarray(x), prob=0.9)]
res = {}
for name in ("all", "ind"):
    a = pd.read_csv(OUT / f"input_{name}.csv")
    mu, kap = expand.mu_kappa(models.Spec(), P, a, None)
    sd = np.sqrt(mu * (1 - mu) / (kap + 1))
    y = np.clip(a.performance.to_numpy(), 1e-3, 1 - 1e-3)
    ex = np.where(a.obs_class.to_numpy() > 0)[0]; e0 = a.cell.to_numpy()[ex]   # pair each EEE row with its Epoch row
    out = {}
    for lab, sel in (("all pairs", np.ones(len(ex), bool)), ("independent", a.obs_class.to_numpy()[ex] == 1),
                     ("upstream-unknown", a.obs_class.to_numpy()[ex] == 2),
                     ("all pairs, no GPQA diamond", a.benchmark.to_numpy()[ex] != "GPQA diamond"),
                     ("independent, no GPQA diamond", (a.obs_class.to_numpy()[ex] == 1) & (a.benchmark.to_numpy()[ex] != "GPQA diamond"))):
        if sel.sum() == 0: continue
        i1, i0 = ex[sel], e0[sel]
        Ed2 = (2 * sd[:, i0] ** 2).sum(1)
        d2 = ((y[i1] - y[i0]) ** 2).sum()
        ratio = d2 / Ed2
        yr1 = rng.beta(mu[:, i0] * kap[:, i0], (1 - mu[:, i0]) * kap[:, i0]); yr0 = rng.beta(mu[:, i0] * kap[:, i0], (1 - mu[:, i0]) * kap[:, i0])
        ratio_rep = ((yr1 - yr0) ** 2).sum(1) / Ed2
        z1 = (y[i1] - mu[:, i1]) / sd[:, i1]; z0 = (y[i0] - mu[:, i0]) / sd[:, i0]
        r = np.array([np.corrcoef(z1[s], z0[s])[0, 1] for s in range(len(pick))])
        zr1 = (yr1 - mu[:, i0]) / sd[:, i0]; zr0 = (yr0 - mu[:, i0]) / sd[:, i0]
        r_rep = np.array([np.corrcoef(zr1[s], zr0[s])[0, 1] for s in range(len(pick))])
        rms_d = float(np.sqrt(d2 / sel.sum())); 
        out[lab] = dict(n_pairs=int(sel.sum()), n_cells=int(len(np.unique(i0))),
                        ratio_median=float(np.median(ratio)), ratio_90=q90(ratio),
                        ratio_rep_90=q90(ratio_rep), p_ratio_le=float(np.mean(ratio_rep <= ratio)),
                        stable_share_median=float(1 - np.median(ratio)),
                        r_res_median=float(np.median(r)), r_res_90=q90(r),
                        r_rep_90=q90(r_rep), p_r_ge=float(np.mean(r_rep >= r)),
                        rms_source_diff_points=100 * rms_d, rms_diff_expected_points=100 * float(np.sqrt(np.median(Ed2) / sel.sum())),
                        mean_signed_diff_points=100 * float((y[i1] - y[i0]).mean()), share_eee_higher=float(np.mean(y[i1] > y[i0])))
        if lab == "all pairs":   # per benchmark, cells with at least 5 pairs
            b = a.benchmark.to_numpy()[i0]; rows = []
            for bb in np.unique(b):
                m = b == bb
                if m.sum() < 5: continue
                rows.append(dict(benchmark=bb, n=int(m.sum()), rms_diff=100 * float(np.sqrt(((y[i1[m]] - y[i0[m]]) ** 2).mean())),
                                 rms_noise=100 * float(np.sqrt(np.median((2 * sd[:, i0[m]] ** 2).mean(1)) / 2)),
                                 ratio=float(np.median(((y[i1[m]] - y[i0[m]]) ** 2).sum() / (2 * sd[:, i0[m]] ** 2).sum(1)))))
            out["by_benchmark"] = sorted(rows, key=lambda r: r["ratio"])
    res[name] = out
json.dump(res, open(OUT / "diag_p0.json", "w"), indent=1)
for name, o in res.items():
    print("==", name)
    for lab, v in o.items():
        if lab == "by_benchmark":
            print(pd.DataFrame(v).round(3).to_string(index=False)); continue
        print(lab, {k: (round(x, 4) if isinstance(x, float) else x) for k, x in v.items()})
