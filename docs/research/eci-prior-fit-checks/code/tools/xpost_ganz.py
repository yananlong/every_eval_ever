# Audit of the "log-perplexity vs Epoch ECI" chart (Ganzhorn, 2026-11-22): point selection, data version, projection.
import json, os, glob
import numpy as np, xarray as xr
OUT='runs/XPOST'; os.makedirs(OUT,exist_ok=True)
t=xr.open_datatree('runs/W/W2/seed12345.nc'); names=[str(x) for x in t['posterior'].to_dataset()['model'].values]
d0=np.load('runs/W/W5/P0.npz')['eci'].astype(float)
def m(n): return float(d0[:,names.index(n)].mean())
# Base log-perplexity read off OpenAI's "Perplexity and Intelligence" chart (pixel reads, +-0.002).
LB={'GPT-3.5':0.986,'GPT-4':0.913,'GPT-4 Turbo':0.909,'GPT-4o/o1':0.904,'GPT-4.5':0.876,'GPT-4.1/o3':0.902,
    'GPT-5/5.1':0.893,'GPT-5.2':0.889,'GPT-5.4':0.871,'GPT-5.5':0.849,'GPT-5.6 Sol':0.828,'GPT-6 Astra':0.783,'GPT-6.2 Astra':0.761}
FAM={'GPT-3.5':['GPT-3.5 Turbo (Jun 2023)','GPT-3.5 Turbo (Nov 2023)','GPT-3.5 Turbo (Jan 2024)'],
     'GPT-4':['GPT-4 (Mar 2023)','GPT-4 (Jun 2023)'],'GPT-4 Turbo':['GPT-4 Turbo (Nov 2023)','GPT-4 Turbo (Apr 2024)'],
     'GPT-4o/o1':['GPT-4o (May 2024)','GPT-4o (Aug 2024)','GPT-4o (Nov 2024)','o1','o1-preview'],'GPT-4.5':['GPT-4.5'],
     'GPT-4.1/o3':['GPT-4.1','o3','o3-pro'],'GPT-5/5.1':['GPT-5','GPT-5.1','GPT-5 Pro'],'GPT-5.2':['GPT-5.2','GPT-5.2 Pro'],
     'GPT-5.4':['GPT-5.4','GPT-5.4 Pro'],'GPT-5.5':['GPT-5.5','GPT-5.5 Pro'],'GPT-5.6 Sol':['GPT-5.6 Sol'],'GPT-6 Astra':['GPT-6 Astra']}
# Ganzhorn's chart, pixel reads (x +-0.002, y +-0.3): Epoch's published ECI values.
G={'o3':(0.902,147.3),'GPT-5':(0.894,150.0),'GPT-5.2':(0.889,153.5),'GPT-5.4':(0.872,156.7),'GPT-5.5':(0.849,158.8),
   'GPT-5.6 Sol':(0.829,161.3),'GPT-6 Astra':(0.783,169.2),'GPT-6.2 Astra':(0.761,174.2)}
def fit(x,y,x0=0.732):
    x,y=np.asarray(x),np.asarray(y); X=np.c_[np.ones_like(x),x]; b=np.linalg.lstsq(X,y,rcond=None)[0]; r=y-X@b
    s=np.sqrt(r@r/(len(y)-2)); return dict(n=len(x),intercept=b[0],slope=b[1],r=float(np.corrcoef(x,y)[0,1]),resid_sd=s,pred_0732=b[0]+b[1]*x0,
        resid={})
R={}
gx=[v[0] for v in G.values()]; gy=[v[1] for v in G.values()]
R['ganz_chart_refit']=fit(gx,gy)
R['ganz_chart_no_6.2']=fit(gx[:-1],gy[:-1])
# same 7 models, our posterior means, OpenAI L
sel={'o3':'GPT-4.1/o3','GPT-5':'GPT-5/5.1','GPT-5.2':'GPT-5.2','GPT-5.4':'GPT-5.4','GPT-5.5':'GPT-5.5','GPT-5.6 Sol':'GPT-5.6 Sol','GPT-6 Astra':'GPT-6 Astra'}
R['ours_vs_epoch_published']={k:dict(epoch_chart=G[k][1],ours=round(m(k),2),diff=round(m(k)-G[k][1],2)) for k in sel}
R['ours_same7']=fit([LB[v] for v in sel.values()],[m(k) for k in sel])
# per-draw on same 7
idx=[names.index(k) for k in sel]; x=np.array([LB[v] for v in sel.values()]); X=np.c_[np.ones_like(x),x]
B=np.linalg.lstsq(X,d0[::4][:,idx].T,rcond=None)[0]; p=B[0]+B[1]*0.732
R['ours_same7_per_draw']=dict(slope_q=np.quantile(B[1],[.05,.5,.95]).tolist(),pred_q=np.quantile(p,[.05,.5,.95]).tolist())
# point-selection: every base on OpenAI's chart that we have, using (a) the max-ECI model per base, (b) the min-ECI listed model per base
def bases(pick, keys):
    xs,ys,who=[],[],[]
    for k in keys:
        c=[(m(n),n) for n in FAM[k] if n in names]
        if not c: continue
        v,n=pick(c); xs.append(LB[k]); ys.append(v); who.append(n)
    f=fit(xs,ys); f['models']=who; f['eci']=[round(y,2) for y in ys]; return f
allk=[k for k in FAM]; since4=[k for k in FAM if k!='GPT-3.5']; since45=['GPT-4.5','GPT-4.1/o3','GPT-5/5.1','GPT-5.2','GPT-5.4','GPT-5.5','GPT-5.6 Sol','GPT-6 Astra']
R['select']={'all_bases_max':bases(max,allk),'all_bases_min':bases(min,allk),'GPT4on_max':bases(max,since4),
             'GPT4.5on_max':bases(max,since45),'GPT4.5on_min':bases(min,since45)}
# alternative within-base picks in Ganz's 7-model window
alt={'GPT-4.1 for o3':{'o3':'GPT-4.1'},'GPT-5.1 for GPT-5':{'GPT-5':'GPT-5.1'},'Pro variants':{'GPT-5':'GPT-5 Pro','GPT-5.2':'GPT-5.2 Pro','GPT-5.4':'GPT-5.4 Pro','GPT-5.5':'GPT-5.5 Pro','o3':'o3-pro'}}
R['within_base_swaps']={}
for a,sw in alt.items():
    ks=[sw.get(k,k) for k in sel]; R['within_base_swaps'][a]=fit([LB[v] for v in sel.values()],[m(k) for k in ks])
# benchmark-set refits on Ganz's 7-model set
rows=[]
for f in sorted(glob.glob('runs/W/BSEL/fits/*.npz')):
    z=np.load(f,allow_pickle=True); nm=list(z['names'])
    if all(k in nm for k in sel): rows.append(fit(x,[z['mean'][nm.index(k)] for k in sel])['pred_0732'])
R['bsel_same7_pred']=dict(n=len(rows),min=min(rows),max=max(rows),q05=float(np.quantile(rows,.05)),q95=float(np.quantile(rows,.95)))
def clean(o):
    if isinstance(o,dict): return {k:clean(v) for k,v in o.items()}
    if isinstance(o,(list,tuple)): return [clean(v) for v in o]
    if isinstance(o,(np.floating,float)): return round(float(o),3)
    return o
R=clean(R); json.dump(R,open(f'{OUT}/ganz_audit.json','w'),indent=1); print(json.dumps(R,indent=1))
