import sys, json, pandas as pd, numpy as np
sys.path.insert(0,'../tools'); from eee_xwalk_lib import *; from eee_bmap_rules import INCLUDE
pd.set_option('display.width',250); pd.set_option('display.max_rows',3000); pd.set_option('display.max_colwidth',90)
f=pd.read_parquet(XW+'/flat.parquet',columns=['collection','model_id','model_name','evaluation_name','dataset_name','metric_id','score'])
inc=[]
for (b,c,e,d,m,s,_) in INCLUDE:
    q=(f.collection==c)&(f.evaluation_name==e)
    if d: q&=(f.dataset_name==d)
    if m: q&=(f.metric_id==m)
    x=f[q].copy(); x['eci']=b; inc.append(x)
inc=pd.concat(inc); print(len(inc))
models=pd.read_pickle(XW+'/_auto_models.pkl')
inc=inc.merge(models,on=['model_id','model_name'])
fi=zread('epoch_capabilities_index/processed_data_for_eci.csv'); fit=set(fi.Model)
u=inc.groupby(['model_id','model_name','status','how']).agg(n=('score','size'),ecis=('eci',lambda s:len(set(s))),groups=('groups','first')).reset_index()
print(u.status.value_counts().to_dict())
amb=u[u.status=='ambiguous']; amb=amb[amb.groups.map(lambda g:any(x in fit for x in g))]
print('AMBIGUOUS',len(amb))
for _,r in amb.iterrows(): print(f" {r.model_id} | {r.model_name} | {r.groups}")
un=u[u.status=='unmapped'].copy()
import re
fam=re.compile(r'claude|gpt|gemini|gemma|grok|llama|qwen|qwq|deepseek|kimi|glm|mistral|mixtral|phi|o1|o3|o4|muse|nemotron|minimax|falcon|yi-|baichuan|internlm|vicuna|palm|mpt|starcoder|dolly|xgen|inkling|beam|intellect|chatglm|stable|redpajama|cerebras',re.I)
un=un[un.model_id.str.contains(fam)|un.model_name.astype(str).str.contains(fam)]
print('UNMAPPED family-like',len(un))
un.sort_values('model_id').to_csv(XW+'/_unmapped_review.csv',index=False)
dl=u[(u.status=='mapped')&(u.how=='dateless-unique')]
print('DATELESS-UNIQUE',len(dl)); dl.to_csv(XW+'/_dateless_review.csv',index=False)
