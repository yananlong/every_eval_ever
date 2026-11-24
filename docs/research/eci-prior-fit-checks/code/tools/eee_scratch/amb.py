import sys, pandas as pd
sys.path.insert(0,'../tools'); from eee_xwalk_lib import *
m=pd.read_csv(XW+'/model_map.csv'); a=m[(m.cls=='ambiguous-model')&(m.how=='undated-collision')]
print(len(a))
for r in a.itertuples(): print(f"{r.model_id[:50]}|{str(r.model_name)[:44]}|{r.n_rows}|{r.candidates[:80]}")
