import pandas as pd, re
pd.set_option('display.width',300); pd.set_option('display.max_rows',3000); pd.set_option('display.max_colwidth',60)
B='runs/EEE/'
f=pd.read_parquet(B+'crosswalk/flat.parquet',columns=['collection','model_id','model_name','dataset_name','evaluation_name','metric_id'])
km=pd.read_csv('/tmp/taxc_keymap.csv',keep_default_na=False)
f=f.fillna({'dataset_name':'','metric_id':''}).merge(km,on=['collection','dataset_name','metric_id'],how='left')
mm=pd.read_csv(B+'crosswalk/model_map.csv'); print(mm.duplicated(['model_id','model_name']).sum())
m=mm[mm.cls=='mapped'][['model_id','model_name','model_group']]
f=f.merge(m,on=['model_id','model_name'],how='left')
eci=set(pd.read_csv(B+'eci_compare.csv').model); print('groups not in eci', len(set(m.model_group)-eci))
g=f.groupby('key').agg(rows=('model_id','size'),eci=('model_group','nunique'),ex=('evaluation_name',lambda s:' ; '.join(list(dict.fromkeys(s))[:2])[:80])).sort_values('rows',ascending=False)
g=g.drop('__costlat'); cap=g.rows.sum(); g['cum']=g.rows.cumsum()/cap
top=g.head(300)
print('top300 cap cover',top.rows.sum()/cap)
for t in [10,15,20,30]:
    u=g[(g.index.isin(top.index))|(g.eci>=t)]; print(t,len(u),u.rows.sum()/cap)
extra=g[(~g.index.isin(top.index))&(g.eci>=10)]
print(extra.to_string())
print(g.head(300)[['eci']].T.to_string())
u=g[(g.index.isin(top.index))|(g.eci>=10)]
u.to_csv('/tmp/taxc_codeset.csv')
print('CODESET')
for k,r in u.iterrows(): print(k, r.eci, '|', r.ex[:60])
