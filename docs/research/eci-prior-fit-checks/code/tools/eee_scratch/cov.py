import sys, pandas as pd
sys.path.insert(0,'../tools'); from eee_xwalk_lib import *
p=pd.read_csv(XW+'/pairs.csv')
print(p[p.eci_benchmark.str.startswith('FrontierMath')].groupby(['eci_benchmark','src','source_class','evaluator_relationship']).agg(n=('norm','size'),d=('absdiff','median')).to_string())
t=p.groupby(['eci_benchmark','source_class']).size().unstack(fill_value=0); t['cells']=p.groupby('eci_benchmark').apply(lambda g:g.model_group.nunique()); print(t.to_string())
