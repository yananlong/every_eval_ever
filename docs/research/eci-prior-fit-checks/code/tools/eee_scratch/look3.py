import pandas as pd, re, json
pd.set_option('display.width',300); pd.set_option('display.max_columns',40); pd.set_option('display.max_rows',2000); pd.set_option('display.max_colwidth',38)
f=pd.read_parquet('runs/EEE/crosswalk/flat.parquet')
print(f.shape, f.collection.nunique())
norm=lambda s: re.sub(r'[^a-z0-9]','',str(s).lower())
AL=json.load(open('../tools/eee_aliases.json'))
for c in ('collection','evaluation_name','dataset_name'): f['n_'+c]=f[c].map(norm)
key=['collection','evaluation_name','dataset_name','metric_id','max_score','source_org','evaluator_relationship']
for b,als in AL.items():
    m=pd.Series(False,index=f.index)
    for a in als:
        a=norm(a)
        for c in ('n_collection','n_evaluation_name','n_dataset_name'): m|=f[c].str.contains(a,regex=False)
    g=f[m].groupby(key,dropna=False).agg(n=('score','size'),nm=('model_id','nunique'),smin=('score','min'),smax=('score','max')).reset_index()
    print('\n=====',b,als,int(m.sum()))
    if len(g): print(g.sort_values('n',ascending=False).head(22).to_string())
