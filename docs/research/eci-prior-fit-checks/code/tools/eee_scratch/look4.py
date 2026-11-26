import zipfile, io, pandas as pd, re
pd.set_option('display.width',300); pd.set_option('display.max_columns',40); pd.set_option('display.max_rows',2000); pd.set_option('display.max_colwidth',60)
z=zipfile.ZipFile('ext/epoch_zip/benchmark_data.zip')
rd=lambda n: pd.read_csv(io.BytesIO(z.read(n)))
mm=rd('model_metadata.csv').dropna(subset=['model_version']); fi=rd('epoch_capabilities_index/processed_data_for_eci.csv')
print(len(mm), mm.model_group.nunique(), mm.model_group.isna().sum())
fit=set(fi.Model); mf=mm[mm.model_group.isin(fit)]
print(len(mf), mf.model_group.nunique())
print(mf.sample(40,random_state=1)[['model_version','model_group','date','display_name','organization']].to_string())
g=mf.groupby('model_group').model_version.agg(list)
for k in ['Claude 3.5 Sonnet','GPT-5','GPT-4o','Gemini 2.5 Pro','Claude Fable 5.2']:
    print(k, [x for x in g.index if k.lower() in x.lower()][:8]); 
for k in [x for x in g.index if x.startswith('Claude 3.5 Sonnet') or x.startswith('GPT-5')][:8]: print(k, g[k])
print(sorted(fit)[:260])
f=pd.read_parquet('runs/EEE/crosswalk/flat.parquet',columns=['collection','model_id','model_name','developer'])
for c in ['artificial-analysis-llms','vals-ai','paperswithcode','llm-stats','benchpress','arc-agi','terminal-bench-2.0','hfopenllm_v2','wild','openeval']:
    s=f[f.collection==c].drop_duplicates('model_id'); print(c,len(s)); print(s.sample(min(8,len(s)),random_state=2)[['model_id','model_name']].to_string(header=False))
