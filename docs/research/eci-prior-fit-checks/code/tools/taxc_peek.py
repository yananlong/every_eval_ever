import pandas as pd
pd.set_option('display.width',300); pd.set_option('display.max_colwidth',140)
f=pd.read_parquet('runs/EEE/crosswalk/flat.parquet',columns=['collection','dataset_name','evaluation_name','metric_id','metric_desc','source_data_extra'])
km=pd.read_csv('/tmp/taxc_keymap.csv',keep_default_na=False)
f=f.fillna({'dataset_name':'','metric_id':''}).merge(km,on=['collection','dataset_name','metric_id'],how='left')
for k in ['mmae','claweval','agentslastexam','skillsbench','preflight','bench','imagenet','safety','oktest','preference','jobbench','parsebench','sgibench','mysterymechanism','frontiercs2','mtaime2024','blendsample','tools','telecom','banking','coarena','vitabench','financefundamentals','helmsafety','mmtebv2','apexshortlist','erqa','lifescidiamond','cyberbench','secbenchpro','riemannbench']:
    s=f[f.key==k].drop_duplicates(['evaluation_name','metric_id']).head(2)
    for r in s.itertuples(): print(k,'|',r.collection,'|',r.evaluation_name[:60],'|',str(r.metric_desc)[:110],'|',str(r.source_data_extra)[:120])
print(sorted(set(km.key[km.key.str.startswith('aa:')])))
