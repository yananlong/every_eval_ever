"""Read-only: how often Epoch's mu clip [1e-6, 1-1e-6] binds on the W2 posterior."""
import sys; sys.path.insert(0,'runs')
import numpy as np, arviz as az
from lib import data, ppc_checks as pc
t=az.from_netcdf('runs/W/W2/seed12345.nc'); df=data.fit_input()
el=pc.Elig(df, data.scores()) if hasattr(data,'scores') else None
post=t.posterior
P={v: post[v].stack(s=("chain","draw")).transpose("s",...).to_numpy() for v in ["capability","difficulty","slope"]}
mids,bids=df["model_id"].unique(),df["benchmark_id"].unique()
mi=df["model_id"].map({m:i for i,m in enumerate(mids)}).to_numpy(); bi=df["benchmark_id"].map({b:i for i,b in enumerate(bids)}).to_numpy()
L=np.log(1e6-1)
y=np.clip(df["performance"].to_numpy(),1e-3,1-1e-3) if "performance" in df else None
S=P["capability"].shape[0]; N=len(df); hit=np.zeros(N); lo=np.zeros(N); etamax=0
for a in range(0,S,1000):
    eta=P["slope"][a:a+1000][:,bi]*(P["capability"][a:a+1000][:,mi]-P["difficulty"][a:a+1000][:,bi])
    hit+=(np.abs(eta)>L).sum(0); lo+=(eta<-L).sum(0); etamax=max(etamax,np.abs(eta).max())
f=hit/S
print("draws",S,"rows",N,"max|eta|",round(float(etamax),2),"clip threshold |eta|>",round(L,2))
print("share of all (draw,row) cells clipped",f.mean())
print("rows with any clipped draw",int((f>0).sum()),"rows clipped in >5% / >50% of draws",int((f>.05).sum()),int((f>.5).sum()))
idx=np.argsort(-f)[:12]
for i in idx:
    if f[i]==0: break
    print(round(f[i],4),"low" if lo[i]>hit[i]/2 else "high", df.iloc[i]["Model"] if "Model" in df else mi[i], "|", df.iloc[i]["benchmark"] if "benchmark" in df else bi[i], "| y=", None if y is None else round(float(y[i]),4))
# compare with the score clip: logit(1e-3)
print("score-clip logit", round(float(np.log(999)),2))
