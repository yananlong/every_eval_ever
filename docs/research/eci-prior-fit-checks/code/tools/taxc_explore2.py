import pandas as pd
pd.set_option('display.width',250); pd.set_option('display.max_rows',600); pd.set_option('display.max_colwidth',50)
B='runs/EEE/'
f=pd.read_parquet(B+'crosswalk/flat.parquet',columns=['collection','model_id','model_name','source_name','source_org','dataset_name','evaluation_name','metric_id'])
mm=pd.read_csv(B+'crosswalk/model_map.csv')
print(mm[mm.cls=='mapped'].model_group.nunique())
print(mm.groupby(['model_id']).size().max())
# map on model_id+model_name
m=mm[mm.cls=='mapped'][['model_id','model_name','model_group']].drop_duplicates()
f=f.merge(m,on=['model_id','model_name'],how='left')
print('rows with eci model', f.model_group.notna().sum(), f.model_group.nunique())
aa=f[f.collection=='artificial-analysis-llms']
print(aa.dataset_name.value_counts().head(40).to_string()); print(aa.metric_id.value_counts().head(40).to_string())
f['dn']=f.dataset_name.fillna('').str.strip().str.lower()
g=f.groupby('dn').agg(rows=('model_id','size'),models=('model_id','nunique'),eci=('model_group','nunique'),cols=('collection',lambda s:'|'.join(sorted(set(s))[:4])),nc=('collection','nunique')).sort_values('rows',ascending=False)
g['cumrow']=g.rows.cumsum()/g.rows.sum()
print(len(g)); print(g.head(250).to_string())
print('by eci models'); print(g.sort_values('eci',ascending=False).head(150).to_string())
for k in [100,200,300,400,600]:
    print(k, g.rows.head(k).sum()/g.rows.sum())
