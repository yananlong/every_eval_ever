import sys, json, numpy as np
sys.path.insert(0,'runs')
from lib import sbc_modrak as sm
S='runs/W/W3M_full/'
z=np.load('runs/W/W3M_full/ranks_null.npz'); R=len(z['replicates'])
gt=sm.GammaTest(R); lo,hi=gt.band(); print('G',gt.G,'g05',gt.g05, 'band half-width mid',hi[len(hi)//2])
agg=json.load(open('runs/W/W3M_full/modrak_full.json'))['quantities']
out={}
for c in z.files:
    if c=='replicates': continue
    U=z[c]; P=U.shape[1]
    D=np.stack([gt.diff(U[:,j]) for j in range(P)],1)
    mx=np.abs(D).max(0)
    med=np.median(D,1); q10=np.quantile(D,.1,1); q90=np.quantile(D,.9,1)
    pooled=np.mean(D,1); ip=np.abs(pooled).argmax()
    mu=U.mean(0)
    print(c,P,'band max',round(hi.max(),3),'| median-col maxabs',round(float(np.median(mx)),3),'| mean curve max',round(pooled[ip],3),'at z',round(gt.z[ip],2),'| median curve outside band',int(((med<lo)|(med>hi)).sum()),'/',gt.G,'| mean u range',mu.min().round(2),mu.max().round(2),'| cols mean u<.45',int((mu<.45).sum()),'>.55',int((mu>.55).sum()))
    gp=np.array([gt.test(U[:,j])[1] for j in range(P)]); print('   gamma p<.05 cols',int((gp<.05).sum()),'p<.01/P',int((gp<.01/P).sum()),'median p',np.median(gp).round(3))
    print('   share<.05',(U<.05).mean().round(3),'>.95',(U>.95).mean().round(3),'<.5',(U<.5).mean().round(3))
    out[c]=dict(z=gt.z.tolist(),med=med.tolist(),q10=q10.tolist(),q90=q90.tolist(),mean=pooled.tolist())
np.save(S+'curves.npy',out,allow_pickle=True)
for c in ('loglik_joint','resid_overall','pearson_overall'):
    d=gt.diff(z[c][:,0]); i=np.abs(d).argmax(); print(c,'maxdiff',d[i].round(3),'at',gt.z[i].round(2),'gamma',gt.test(z[c][:,0]),'median u',np.median(z[c][:,0]).round(2),'mean',z[c].mean().round(3),'frac<.5',(z[c]<.5).mean().round(3))
for c in agg: print(c, agg[c]['median_ess'], agg[c]['median_stride'], agg[c]['share_thinned'])
U=z['hyper'];print(U.mean(0),(U>.95).mean(0),[gt.test(U[:,j]) for j in range(3)])
U=z['class_summaries'];print(U.mean(0),[round(gt.test(U[:,j])[1],4) for j in range(6)])
