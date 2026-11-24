import sys, json; sys.path.insert(0,'runs')
import numpy as np, xarray as xr
from lib import data, sens_metrics as sm
df=data.fit_input(); cnt=df.groupby('Model').size()
t=xr.open_datatree('runs/W/W2/seed12345.nc'); names=[str(x) for x in t['posterior'].to_dataset()['model'].values]
n=np.array([cnt[x] for x in names]); anchor=np.array([x in sm.ANCHORS for x in names])
d0=np.load('runs/W/W5/P0.npz')['eci'].astype(float); s0=sm.summarise(d0)
from lib import fit as fm
arms={k:np.load(f'runs/W/W5/{k}.npz')['eci'].astype(float) for k in ('P8','P9','P10')}
arms['PR']=np.load('runs/W/W5/PR.npz')['eci'].astype(float) if False else fm.load_eci('runs/W/W5/PR.nc')[0]
arms['J2']=fm.load_eci('runs/W/W5J/J2/J2.nc')[0]
for k,d in arms.items():
    s=sm.summarise(d); sh=(s['mean']-s0['mean'])/s0['width']; wr=s['width']/s0['width']; na=~anchor
    low=s0['mean']<np.median(s0['mean'])
    print(k,'n>.25:',int((np.abs(sh[na])>.25).sum()),'of which sparse',int(((np.abs(sh)>.25)&na&(n<=6)).sum()),'low-half',int(((np.abs(sh)>.25)&na&low).sum()),
      'mean signed shift (ECI) low-half %.2f high-half %.2f'%((s['mean']-s0['mean'])[low&na].mean(),(s['mean']-s0['mean'])[~low&na].mean()),
      'median width ratio sparse %.3f dense %.3f'%(np.median(wr[na&(n<=6)]),np.median(wr[na&(n>6)])),
      'S3 outside: narrower',int((wr[na]<.8).sum()),'wider',int((wr[na]>1.25).sum()),'corr(|shift|,1/n) %.2f'%np.corrcoef(np.abs(sh[na]),1/n[na])[0,1])
    top=np.argsort(-np.abs(sh*na))[:3]; print('   largest shifts (W units):',[(names[i],int(n[i]),round(float(sh[i]),2),round(float((s['mean']-s0['mean'])[i]),1)) for i in top])
