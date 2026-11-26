import pandas as pd, json, collections
pd.set_option('display.width',250); pd.set_option('display.max_rows',400); pd.set_option('display.max_colwidth',60)
B='runs/EEE/'
a=pd.read_csv(B+'input/eee_fit_input_annotated.csv')
print(a.shape, a.benchmark.nunique(), a.Model.nunique())
g=a.groupby('benchmark').agg(cells=('Model','size'),rel=('benchmark_release_date','first')).sort_values('cells',ascending=False)
print(g.to_string())
f=pd.read_parquet(B+'crosswalk/flat.parquet')
print(f.shape); print(f.dtypes)
print(f.head(3).T)
for c in ['collection','source_type','source_org','source_name']:
    print(c, f[c].nunique()); print(f[c].value_counts().head(40).to_string())
print('evaluation_name',f.evaluation_name.nunique(),'dataset_name',f.dataset_name.nunique())
mm=pd.read_csv(B+'crosswalk/model_map.csv'); print(mm.cls.value_counts()); print(mm.how.value_counts())
print(mm[mm.cls.str.contains('fit',na=False)].head())
e=collections.Counter()
for l in open('ext/eee/entries.jsonl'):
    e[json.loads(l).get('benchmark')]+=1
print(len(e)); print(e.most_common(60))
