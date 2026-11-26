import sys, json, pandas as pd, numpy as np
sys.path.insert(0,'../tools'); from eee_xwalk_lib import *
pd.set_option('display.width',300); pd.set_option('display.max_rows',3000); pd.set_option('display.max_colwidth',70)
f=pd.read_parquet(XW+'/flat.parquet')
exact,loose,mm=epoch_keys()
fi=zread('epoch_capabilities_index/processed_data_for_eci.csv'); fit=set(fi.Model)
cells={b:set(g.Model) for b,g in fi.groupby('benchmark')}
models=f[['model_id','model_name']].drop_duplicates()
res=[auto_map(a,b,exact,loose) for a,b in zip(models.model_id,models.model_name)]
models['status']=[r[0] for r in res]; models['groups']=[r[1] for r in res]; models['how']=[r[2] for r in res]
models['fitgroups']=models.groups.map(lambda g:[x for x in g if x in fit])
print(models.status.value_counts().to_dict(), 'with fit groups:',(models.fitgroups.str.len()>0).sum())
models.to_pickle(XW+'/_auto_models.pkl')
f=f.merge(models,on=['model_id','model_name'])
f=f[f.fitgroups.str.len()>0]
AL=json.load(open('../tools/eee_aliases.json'))
for c in ('collection','evaluation_name','dataset_name'): f['n_'+c]=f[c].map(norm_text)
out=[]
for b,als in AL.items():
    m=pd.Series(False,index=f.index)
    for a in als:
        a=norm_text(a)
        for c in ('n_collection','n_evaluation_name','n_dataset_name'): m|=f[c].str.contains(a,regex=False)
    s=f[m].copy()
    s['hit']=s.fitgroups.map(lambda g:any(x in cells[b] for x in g))
    g=s.groupby(['collection','evaluation_name','dataset_name','metric_id','max_score','evaluator_relationship'],dropna=False).agg(n=('score','size'),nm=('model_id','nunique'),nhit=('hit','sum'),smin=('score','min'),smax=('score','max')).reset_index()
    g.insert(0,'eci',b); out.append(g[g.nhit>0])
o=pd.concat(out); o.to_csv(XW+'/_cand.csv',index=False)
o['evaluation_name']=o.evaluation_name.str.replace('paperswithcode','pwc').str.replace('artificial_analysis','AA'); o['collection']=o.collection.str.replace('paperswithcode','pwc').str.replace('artificial-analysis-llms','AA')
o['evaluator_relationship']=o.evaluator_relationship.str[:5]
for b,g in o.groupby('eci',sort=False):
    print('=====',b); print(g.drop(columns='eci').sort_values('nhit',ascending=False).head(40).to_string(index=False,header=False))
