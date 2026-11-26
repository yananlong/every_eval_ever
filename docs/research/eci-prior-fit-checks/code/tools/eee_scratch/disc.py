import sys, pandas as pd
sys.path.insert(0,'../tools'); from eee_xwalk_lib import *
p=pd.read_csv(XW+'/pairs.csv'); p['d']=p.norm-p.epoch_norm
q=p.reindex(p.d.abs().sort_values(ascending=False).index).head(45)
for r in q.itertuples(): print(f"{r.eci_benchmark[:18]:18}|{r.model_group[:26]:26}|{r.src[:12]:12}|{r.source_class[:5]}|{r.norm:.3f} vs {r.epoch_norm:.3f}|{r.model_id[:40]}|{str(r.model_name)[:30]}|{r.evaluation_name.split('.')[-1][:24]}|ep:{str(r.epoch_version)[:30]}")
