import pandas as pd
pd.set_option('display.width',250); pd.set_option('display.max_colwidth',400)
f=pd.read_parquet('runs/EEE/crosswalk/flat.parquet')
def show(q,n=3,seed=0):
    s=f.query(q); print('\n###',q,len(s))
    for _,r in s.sample(min(n,len(s)),random_state=seed).iterrows():
        print({k:r[k] for k in ['model_id','model_name','model_extra','source_name','source_org','source_type','evaluator_relationship','source_extra','evaluation_name','dataset_name','source_data_extra','metric_id','metric_unit','metric_desc','metric_extra','max_score','score','score_extra','gen_cfg','eval_ts','legacy_path']})
show("collection=='paperswithcode' and evaluation_name=='paperswithcode.world_knowledge.gpqa_diamond'",3)
show("collection=='paperswithcode' and evaluation_name=='paperswithcode.reasoning.hellaswag'",2)
show("collection=='llm-stats' and evaluation_name=='llm_stats.frontiermath'",2)
show("collection=='llm-stats' and evaluation_name=='llm_stats.frontiercode-1.1' and evaluator_relationship=='third_party'",1)
show("collection=='benchpress' and evaluation_name=='benchpress.gpqa-diamond'",3)
show("collection=='artificial-analysis-llms' and evaluation_name=='artificial_analysis.gpqa'",1)
show("collection=='vals-ai' and evaluation_name=='vals_ai.proof_bench.overall'",2)
show("collection=='arc-agi' and evaluation_name=='v1_Semi_Private' and metric_id=='score'",1)
show("collection=='terminal-bench-2.0'",1)
