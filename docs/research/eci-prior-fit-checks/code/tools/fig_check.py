import json,numpy as np
s=json.load(open('runs/W/W4fig/structure.json')); p=json.load(open('runs/W/W4/ppc.json'))['W4b']
s['T_obs']={k:p['T_observed'][k] for k in ('T1','T2','T5')}; json.dump(s,open('runs/W/W4fig/structure.json','w'))
print(s['T_obs'])
P=s['pairs']; d=np.array([(x['r']-x['null_mean'])/x['null_sd'] for x in P]); dt=np.array([(x['r_null_typ']-x['null_mean'])/x['null_sd'] for x in P])
print('obs std dev', d.std(), (np.abs(d)>2).mean(), (d>2).mean(), (d<-2).mean()); print('typ', dt.std(), (np.abs(dt)>2).mean())
for x in s['scatter']['obs']+s['scatter']['null']: print(x['a'][:20],x['b'][:20],len(x['x']),round(x['r'],2))
T=s['T_null']; print({k:(np.mean([t[k] for t in T]),np.std([t[k] for t in T]),np.max([t[k] for t in T])) for k in ('T1','T2','T5')})
print(s['benchmarks'])
