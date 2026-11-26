import sys, json, pandas as pd, numpy as np
sys.path.insert(0,'../tools'); from eee_xwalk_lib import *
f=pd.read_parquet(XW+'/flat.parquet',columns=['collection','model_id','model_name','evaluation_name','dataset_name','metric_id','max_score','evaluator_relationship','score'])
models=pd.read_pickle(XW+'/_auto_models.pkl'); models=models[models.status=='mapped']; models['g']=models.groups.str[0]
f=f.merge(models[['model_id','model_name','g']],on=['model_id','model_name'])
fi=zread('epoch_capabilities_index/processed_data_for_eci.csv'); bm=zread('benchmark_metadata.csv').set_index('benchmark')
cand=pd.read_csv(XW+'/_cand.csv')
bad=('swissai','helm_air','aixamine','hlab','biomystery','medqa','medcode','medscribe','mmlu_pro','mmlu-pro','mgsm','supergpqa','polyglotox','tau','kitti','nyuv2','sage.','zebra','livebench/','frontier-cs','matharena','helm_mmlu','mmlu-winogrande','airbench','global-piqa','social','vggsound','something','so10','instantmesh','browsecomp','deepsearchqa','truthfulqa','time_horizon','healthbench','wild.bbh.','wild.mmlu.','wild.math','wild.bbeh','cost','helm_capabilities')
seen=set()
for (b,c,e,d,m),_ in cand.groupby(['eci','collection','evaluation_name','dataset_name','metric_id'],dropna=False,sort=False):
    if any(x in (c+e+str(m)).lower() for x in bad): continue
    s=f[(f.collection==c)&(f.evaluation_name==e)&(f.dataset_name==d)&((f.metric_id==m) if isinstance(m,str) else f.metric_id.isna())]
    if not len(s): continue
    mx=s.max_score.max(); sc=1.0
    if s.score.max()>1.5: sc=0.01
    r=bm.loc[b]
    s=s.assign(p=((s.score*sc-r.random_baseline)/(r.score_ceiling-r.random_baseline)).clip(0,1))
    best=s.groupby('g').p.max(); last=s.groupby('g').p.last()
    ep=fi[fi.benchmark==b].set_index('Model').performance
    j=pd.concat([best,ep],axis=1,join='inner'); j.columns=['e','p']
    if len(j)<2: continue
    dd=(j.e-j.p)
    print(f"{b[:22]:22}|{c[:10]:10}|{e.replace('paperswithcode.','pwc.').replace('artificial_analysis.','AA.').replace('benchpress.','bp.').replace('llm_stats.','ls.').replace('vals_ai.','va.')[:36]:36}|{str(d)[:18]:18}|{str(m).split('.')[-1][:10]:10}|n={len(j):3}|med|d|={dd.abs().median():.3f}|bias={dd.mean():+.3f}|eq3={(dd.abs()<0.0015).mean():.2f}|r={np.corrcoef(j.e,j.p)[0,1]:.2f}")
