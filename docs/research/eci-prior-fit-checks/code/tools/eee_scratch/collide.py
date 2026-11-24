import sys, pandas as pd
sys.path.insert(0,'../tools'); from eee_xwalk_lib import *
exact,loose,mm=epoch_keys()
fi=zread('epoch_capabilities_index/processed_data_for_eci.csv'); fit=set(fi.Model)
seen=set()
for k,gs in exact.items():
    allg=gs|loose.get(k,set())
    if len(gs)==1 and len(allg)>1 and (allg & fit):
        t=(k,tuple(sorted(allg)))
        if t not in seen: seen.add(t); print(k,'| exact:',sorted(gs),'| loose adds:',sorted(allg-gs))
m=pd.read_csv(XW+'/model_map.csv'); m=m[m.cls=='mapped']
