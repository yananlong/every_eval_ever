import sys, json; sys.path.insert(0,'runs')
import numpy as np
from lib import fit as fm, sens_metrics as sm
d0=np.load('runs/W/W5/P0.npz')['eci'].astype(float); dk=np.load('runs/W/W5/P3.npz')['eci'].astype(float)
names=fm.load_eci('runs/W/W5/P0.nc')[1] if False else fm.load_eci('runs/W/W2/seed12345.nc')[1]
st=json.load(open('runs/strata.json')); masks={k:np.array([n in set(st[k]) for n in names]) for k in ('all','frontier','sparse','dense')}
s=sm.score(dk,d0,names,masks,0.25)
print({k:(round(v['S1'],4),v['S2_count'],v['S3_count'],v['S2_limit']) for k,v in s.items() if k!='S4'}, s['S4']['top10_same'], s['S4']['max_pair_change'])
