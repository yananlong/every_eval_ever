import sys, json, pandas as pd, numpy as np, difflib, re
sys.path.insert(0,'../tools'); from eee_xwalk_lib import *; from eee_bmap_rules import INCLUDE
f=pd.read_parquet(XW+'/flat.parquet',columns=['collection','model_id','model_name','evaluation_name','dataset_name','metric_id','score'])
inc=[]
for (b,c,e,d,m,s,_) in INCLUDE:
    q=(f.collection==c)&(f.evaluation_name==e)
    if d: q&=(f.dataset_name==d)
    if m: q&=(f.metric_id==m)
    x=f[q].copy(); x['eci']=b; inc.append(x)
inc=pd.concat(inc)
exact,loose,mm=epoch_keys()
fi=zread('epoch_capabilities_index/processed_data_for_eci.csv'); fit=set(fi.Model)
u=inc.groupby(['model_id','model_name']).agg(n=('score','size'),colls=('collection',lambda s:','.join(sorted(set(x[:6] for x in s))))).reset_index()
res=[auto_map(a,b,exact,loose) for a,b in zip(u.model_id,u.model_name)]
u['status']=[r[0] for r in res]; u['groups']=[r[1] for r in res]; u['how']=[r[2] for r in res]
print(u.status.value_counts().to_dict(), 'mapped to fit:', u[u.status=='mapped'].groups.map(lambda g:g[0] in fit).sum(), 'fit groups hit:', len({g[0] for g in u[u.status=='mapped'].groups if g[0] in fit}))
u.to_pickle(XW+'/_inc_models.pkl')
fitkeys={}
for d in (exact,loose):
    for k,gs in d.items():
        for g in gs:
            if g in fit: fitkeys.setdefault(k,set()).add(g)
keys=list(fitkeys)
un=u[u.status=='unmapped']
out=[]
for _,r in un.iterrows():
    best=(0,None)
    for e in eee_keys(r.model_id,r.model_name):
        for k in set(e):
            for c in difflib.get_close_matches(k,keys,n=1,cutoff=0.86):
                sc=difflib.SequenceMatcher(None,k,c).ratio()
                if sc>best[0]: best=(sc,c)
    if best[1]: out.append((r.model_id,r.model_name,r.n,r.colls,round(best[0],2),best[1],sorted(fitkeys[best[1]])))
o=pd.DataFrame(out,columns=['id','name','n','colls','sim','key','groups']).sort_values(['key','id'])
o.to_csv(XW+'/_fuzzy_review.csv',index=False); print(len(o))
for _,r in o.iterrows(): print(f"{r.id[:46]}|{str(r['name'])[:40]}|{r.n}|{r.colls[:20]}|{r.key}|{'; '.join(r.groups)[:40]}")
