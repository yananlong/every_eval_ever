"""Chart data for the W5 section of the report: per-model ECI shift and width ratio against P0 for the arms that move
(P8, P9, PR, J2) and one null-effect arm (P7). Reads runs/W/W5 and runs/W/W5J; writes runs/W/W5/chart_data.json. Run from eci_work/v11."""
import sys, json; sys.path.insert(0, 'runs')
import numpy as np, xarray as xr
from lib import data, sens_metrics as sm, fit as fm
df = data.fit_input(); cnt = df.groupby('Model').size()
t = xr.open_datatree('runs/W/W2/seed12345.nc'); names = [str(x) for x in t['posterior'].to_dataset()['model'].values]
n = np.array([cnt[x] for x in names]); anchor = np.array([x in sm.ANCHORS for x in names])
s0 = sm.summarise(np.load('runs/W/W5/P0.npz')['eci'].astype(float))
arms = {k: np.load(f'runs/W/W5/{k}.npz')['eci'].astype(float) for k in ('P7', 'P8')}
arms['P9'] = np.load('runs/W/W5/P9_retry3.npz')['eci'].astype(float)
arms['PR'] = fm.load_eci('runs/W/W5/PR.nc')[0]
arms['J2'] = fm.load_eci('runs/W/W5J/J2/J2.nc')[0]
top20 = set(np.argsort(-np.where(anchor, -np.inf, s0['mean']))[:20].tolist())
out = dict(models=[dict(name=names[i], n=int(n[i]), eci0=round(float(s0['mean'][i]), 2), w0=round(float(s0['width'][i]), 2),
                        frontier=i in top20) for i in range(len(names)) if not anchor[i]], arms={})
keep = [i for i in range(len(names)) if not anchor[i]]
for k, d in arms.items():
    s = sm.summarise(d)
    sh = s['mean'] - s0['mean']; wr = s['width'] / s0['width']
    out['arms'][k] = dict(shift=[round(float(sh[i]), 2) for i in keep], shift_w=[round(float(sh[i] / s0['width'][i]), 3) for i in keep],
                          wr=[round(float(wr[i]), 3) for i in keep],
                          max_abs_shift=float(np.abs(sh[keep]).max()), argmax=names[keep[int(np.argmax(np.abs(sh[keep])))]],
                          frontier_max_abs_shift=float(max(abs(sh[i]) for i in top20)))
    print(k, 'max |shift| %.2f (%s)' % (out['arms'][k]['max_abs_shift'], out['arms'][k]['argmax']), 'frontier max %.2f' % out['arms'][k]['frontier_max_abs_shift'],
          'n |shift|>0.25W', int((np.abs(sh[keep] / s0['width'][keep]) > .25).sum()))
json.dump(out, open('runs/W/W5/chart_data.json', 'w'))
