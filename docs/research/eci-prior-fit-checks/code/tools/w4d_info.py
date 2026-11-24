import json,glob,numpy as np,os
w=[json.load(open(p)) for p in glob.glob('runs/W/W3/rep/null_*.json')]
w=[x for x in w if x['converged']]
a=np.array([x['wall_seconds'] for x in w]);print(np.percentile(a,[0,25,50,75,90,100]),a.sum()/3600)
miss=[x for x in w if not os.path.exists(f'runs/W/W3/rep/null_{x["r"]}.nc')]
print(len(miss),sum(x['wall_seconds'] for x in miss)/3600)
from collections import Counter; print(Counter(x['started_from'] for x in miss), Counter(x['last_attempt']['draws'] for x in miss))
