import sys, json, pandas as pd
sys.path.insert(0,'../tools'); from eee_xwalk_lib import *
p=pd.read_csv(XW+'/pairs.csv')
for q in ["collection=='apex-agents'","evaluation_name=='benchpress.apex-agents'","evaluation_name=='llm_stats.cybench'","evaluation_name=='benchpress.cybench'","evaluation_name=='llm_stats.arc-agi'","evaluation_name=='paperswithcode.reasoning.arc_agi'","evaluation_name=='llm_stats.frontiercode-1.1'"]:
    s=p.query(q)
    if not len(s): print(q,'none'); continue
    r=s.iloc[0]; d=json.load(open('ext/eee/repo/'+r.object_path)); e=d['evaluation_results'][int(r.res_idx)]
    print('##',q,len(s),'| mc:',json.dumps(e.get('metric_config'))[:420],'| sd:',json.dumps(e.get('source_data'))[:500],'| det:',json.dumps(e['score_details'].get('details'))[:500])
m=pd.read_csv(XW+'/model_map.csv'); m=m[(m.cls=='mapped')&(m.how!='exact')]
print(len(m))
for r in m.itertuples(): print(f"{r.model_id[:44]}|{str(r.model_name)[:38]}|{r.how[:8]}|{r.model_group}")
