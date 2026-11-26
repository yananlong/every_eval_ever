"""Chart data for the page: ECDF-difference curves (every 4th of 180 grid points) and the exact R=R_ 95% band, from W3M_full/ranks_null.npz."""
import sys, json, numpy as np
sys.path.insert(0, 'runs')
from lib import sbc_modrak as sm
z = np.load('runs/W/W3M_full/ranks_null.npz'); R_ = len(z['replicates']); gt = sm.GammaTest(R_); lo, hi = gt.band(); ix = np.r_[np.arange(3, R_, 4)]
r3 = lambda a: [round(float(v), 3) for v in np.asarray(a)[ix]]
d = dict(z=r3(gt.z), lo=r3(lo), hi=r3(hi), R=R_, scalar={}, med={})
for c in ("loglik_joint", "resid_overall", "pearson_overall"): d["scalar"][c] = r3(gt.diff(z[c][:, 0]))
for c in ("loglik_bench", "resid_bench", "eci", "edi", "slope", "sigma"):
    U = z[c]; d["med"][c] = r3(np.median(np.stack([gt.diff(U[:, j]) for j in range(U.shape[1])], 1), 1))
json.dump(d, open('runs/W/W3M_full/chart_data.json', 'w'))
print(len(ix), d['lo'][:3], d['hi'][:3])
