# Build normalized EEE benchmark keys and dump a profile for coding (scratch output to stdout)
import pandas as pd, re
pd.set_option('display.width',300); pd.set_option('display.max_rows',2000); pd.set_option('display.max_colwidth',70)
B='runs/EEE/'
f=pd.read_parquet(B+'crosswalk/flat.parquet',columns=['collection','model_id','model_name','source_name','source_org','dataset_name','evaluation_name','metric_id'])
COSTLAT=re.compile(r'price|tokens_per_second|time_to_first|latency|cost')
def key(r):
    c=r.collection; d=(r.dataset_name or '').strip().lower(); m=(r.metric_id or '')
    if c=='artificial-analysis-llms':
        k=m.replace('artificial_analysis.','')
        return '__costlat' if COSTLAT.search(k) else 'aa:'+k
    if c=='arc-agi': return 'arcagi'
    if c=='bfcl': return 'bfcl'
    if ' - ' in d: d=d.split(' - ')[0]
    if '/' in d: d=d.split('/')[-1]
    d=re.sub(r'\(.*?\)','',d)
    d=re.sub(r'[^a-z0-9]','',d)
    return d or '__blank'
import numpy as np
u=f[['collection','dataset_name','metric_id']].drop_duplicates()
u['key']=[key(r) for r in u.itertuples()]
f=f.merge(u,on=['collection','dataset_name','metric_id'],how='left')
f[['collection','dataset_name','metric_id','key']].drop_duplicates().to_csv('/tmp/taxc_keymap.csv',index=False)
g=f.groupby('key').agg(rows=('model_id','size'),models=('model_id','nunique'),nc=('collection','nunique'),
   cols=('collection',lambda s:'|'.join(sorted(set(s))[:3])),ex=('dataset_name',lambda s:' ; '.join(list(dict.fromkeys(s))[:3])[:90])).sort_values('rows',ascending=False)
tot=g.rows.sum(); cap=g.drop('__costlat',errors='ignore').rows.sum()
print('keys',len(g),'rows',tot,'cap rows',cap)
g['cum']=g.rows.cumsum()/tot
print(g.head(700).to_string())
