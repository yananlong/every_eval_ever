# Audit of the X-post claim "base log-perplexity strongly predicts Epoch ECI" against our posterior and refits.
import sys, json, glob, os; sys.path.insert(0,'runs')
import numpy as np, xarray as xr, pandas as pd
OUT='runs/XPOST'; os.makedirs(OUT,exist_ok=True)
t=xr.open_datatree('runs/W/W2/seed12345.nc'); names=[str(x) for x in t['posterior'].to_dataset()['model'].values]
d0=np.load('runs/W/W5/P0.npz')['eci'].astype(float)
# OpenAI "Perplexity and Intelligence" (2026-11-22) base log-perplexity, read from the chart via secondary write-ups;
# GPT-5/5.1 and 5.2 values read off the X-post chart (approximate).
L={'GPT-5.1':0.893,'GPT-5.2':0.888,'GPT-5.4':0.871,'GPT-5.5':0.848,'GPT-5.6 Sol':0.828,'GPT-6 Astra':0.783}
L_src={'GPT-5.1':'X-post chart (approx)','GPT-5.2':'X-post chart (approx)'}
ms=list(L); x=np.array([L[m] for m in ms]); idx=[names.index(m) for m in ms]
X=np.c_[np.ones_like(x),x]; xi=np.array([1,0.732])
def ols(y):
    b,res,*_=np.linalg.lstsq(X,y,rcond=None); r=y-X@b; s=np.sqrt((r@r)/(len(y)-2)); return b,s
R={'models':{m:dict(L=L[m],L_source=L_src.get(m,'OpenAI chart via dev.to/mlq.ai'),eci_mean=float(d0[:,i].mean()),q05=float(np.quantile(d0[:,i],.05)),q95=float(np.quantile(d0[:,i],.95))) for m,i in zip(ms,idx)}}
y=d0[:,idx].mean(0); b,s=ols(y); r=np.corrcoef(x,y)[0,1]
from scipy import stats
tq=stats.t.ppf(.95,len(x)-2); se_pred=s*np.sqrt(1+xi@np.linalg.inv(X.T@X)@xi)
R['ols_on_means']=dict(n=len(x),intercept=b[0],slope=b[1],r=r,r2=r*r,resid_sd=s,pred_0732=float(xi@b),pi90=[float(xi@b-tq*se_pred),float(xi@b+tq*se_pred)])
# propagate posterior uncertainty: per-draw OLS
B=np.array([ols(d0[k,idx])[0] for k in range(0,d0.shape[0],4)])
p=B@xi
R['ols_per_draw']=dict(slope_q=list(np.quantile(B[:,1],[.05,.5,.95])),pred_q=list(np.quantile(p,[.05,.5,.95])))
# leave-one-model-out
R['lomo_pred']={m:float(np.r_[1,0.732]@np.linalg.lstsq(np.delete(X,j,0),np.delete(y,j),rcond=None)[0]) for j,m in enumerate(ms)}
# time-only and L-only
dt={'GPT-5.1':'2025-11-13','GPT-5.2':'2025-12-11','GPT-5.4':'2026-03-05','GPT-5.5':'2026-04-23','GPT-5.6 Sol':'2026-07-09','GPT-6 Astra':'2026-09-03'}
tt=np.array([(pd.Timestamp(dt[m])-pd.Timestamp('2025-01-01')).days/365.25 for m in ms])
R['corr_L_time']=float(np.corrcoef(x,tt)[0,1]); R['corr_eci_time']=float(np.corrcoef(y,tt)[0,1])
bt=np.linalg.lstsq(np.c_[np.ones_like(tt),tt],y,rcond=None)[0]; rt=y-np.c_[np.ones_like(tt),tt]@bt
R['time_only']=dict(slope_per_yr=float(bt[1]),resid_sd=float(np.sqrt(rt@rt/(len(y)-2))))
# same-base spread (post-training / inference variants)
grp={'GPT-5.4 base (L 0.871)':['GPT-5.4','GPT-5.4 Pro','GPT-5.4 Mini','GPT-5.4 Nano'],'GPT-5.5 base (L 0.848)':['GPT-5.5','GPT-5.5 Pro'],
     'GPT-5.6 family (L 0.828 for Sol)':['GPT-5.6 Sol','GPT-5.6 Terra','GPT-5.6 Luna'],'GPT-6 family (L 0.783 for Astra)':['GPT-6 Astra','GPT-6.1 Sol','GPT-6.1 Terra','GPT-6 Sol','GPT-6 Luna'],
     'GPT-4o vs o1 (same-base pair in the X chart)':['GPT-4o (Nov 2024)','o1']}
R['variants']={g:{m:round(float(d0[:,names.index(m)].mean()),2) for m in v if m in names} for g,v in grp.items()}
# benchmark-set dependence: same OLS on every BSEL refit (posterior means)
rows=[]
for f in sorted(glob.glob('runs/W/BSEL/fits/*.npz')):
    z=np.load(f,allow_pickle=True); nm=list(z['names'])
    if not all(m in nm for m in ms): rows.append(dict(fit=os.path.basename(f)[:-4],missing=[m for m in ms if m not in nm])); continue
    yy=np.array([z['mean'][nm.index(m)] for m in ms]); bb,ss=ols(yy)
    rows.append(dict(fit=os.path.basename(f)[:-4],slope=bb[1],pred_0732=float(xi@bb),stretch_51_to_6A=float(yy[-1]-yy[0]),resid_sd=ss))
Bs=pd.DataFrame(rows); Bs.to_csv(f'{OUT}/bsel_slopes.csv',index=False)
ok=Bs.dropna(subset=['slope']); ok=ok.assign(kind=ok.fit.str.extract(r'^(LOBO|R\d+|C|A4)')[0].str.replace(r'R\d+','R',regex=True))
R['bsel']={k:dict(n=len(g),slope_min=g.slope.min(),slope_max=g.slope.max(),pred_min=g.pred_0732.min(),pred_max=g.pred_0732.max(),stretch_min=g.stretch_51_to_6A.min(),stretch_max=g.stretch_51_to_6A.max()) for k,g in ok.groupby('kind')}
R['bsel_missing']=int(Bs.slope.isna().sum())
R['bsel_extremes']=ok.sort_values('slope').iloc[[0,-1]][['fit','slope','pred_0732','stretch_51_to_6A']].to_dict('records')
# priors at the frontier
R['priors']={}
for a in ['P8','P9','P10','PR']:
    fpath=f'runs/W/W5/{a}.npz'
    if os.path.exists(fpath):
        dd=np.load(fpath)['eci'].astype(float); yy=dd[:,idx].mean(0); bb,_=ols(yy); R['priors'][a]=dict(slope=bb[1],pred_0732=float(xi@bb))
# saturation: expected normalized score of a model at ECI E on each benchmark (posterior-mean EDI and slope, Epoch data)
E=pd.read_csv('runs/EEE/edi_compare.csv')
sat={}
for e in [169.0,172.5,177,190,210,237]:
    mu=1/(1+np.exp(-E.slope_epoch*(e-E.edi_epoch)))
    sat[str(e)]=dict(below_0_5=int((mu<.5).sum()),below_0_9=int((mu<.9).sum()),below_0_9_names=E.benchmark[mu<.9].tolist())
R['saturation']=sat; R['edi_top']=E.sort_values('edi_epoch',ascending=False).head(8)[['benchmark','edi_epoch','slope_epoch']].to_dict('records')
json.dump(R,open(f'{OUT}/lppl_audit.json','w'),indent=1,default=float)
print(json.dumps({k:v for k,v in R.items() if k not in('saturation',)},indent=1,default=lambda o: round(float(o),3)))
print(json.dumps({k:{kk:vv for kk,vv in v.items() if kk!='below_0_9_names'} for k,v in sat.items()}))
for k in ['210','237','177']: print(k, sat[k if k!='177' else '177']['below_0_9_names'])
