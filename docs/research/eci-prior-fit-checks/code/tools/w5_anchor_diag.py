"""Diagnostic for the W5A summary: frontier shifts of P8/P9 under orig and X-lowGPT5, and the GPT-4o mini..GPT-5 raw-gap ratio. Run from eci_work/v11."""
import sys,json; sys.path.insert(0,'runs')
import numpy as np, xarray as xr
from lib import anchors as A, sens_metrics as sm
names=[str(x) for x in xr.open_datatree("runs/W/W2/seed12345.nc")["posterior"].to_dataset()["model"].values]
st=json.load(open('runs/strata.json')); fr=[names.index(n) for n in st['frontier']]
P0=np.load('runs/W/W5/P0.npz')['eci'].astype(float); m0=P0.mean(0)
D={'P8':np.load('runs/W/W5/P8.npz')['eci'].astype(float),'P9':np.load('runs/W/W5/P9_retry3.npz')['eci'].astype(float)}
lo=names.index('GPT-4o mini'); g5=names.index('GPT-5'); c35=names.index('Claude 3.5 Sonnet')
print('GPT-4o mini P0 mean', m0[lo], 'P8', D['P8'].mean(0)[lo], 'P9', D['P9'].mean(0)[lo], 'n obs?')
fr=sorted(fr,key=lambda i:-m0[i])
for tag,(il,ih,tl,th) in {'orig':(c35,g5,130,150),'X-lowGPT5':(lo,g5,m0[lo],150.0)}.items():
    b0,_,_=A.reanchor(P0,il,ih,tl,th); s0=sm.summarise(b0)
    for k in ('P9','P8'):
        bk,_,_=A.reanchor(D[k],il,ih,tl,th); sk=sm.summarise(bk)
        sh=(sk['mean']-s0['mean'])
        print(tag,k,'frontier P0 mean ECI %.1f-%.1f'%(s0['mean'][fr].min(),s0['mean'][fr].max()),'median W0 %.2f'%np.median(s0['width'][fr]),
              'shift', np.round(sh[fr],2).tolist(), 'shift/W', np.round(sh[fr]/s0['width'][fr],2).tolist())
# scale ratio: raw capability gap ratio GPT-4o mini..GPT-5 vs Claude3.5..GPT-5 : arm/P0
for k in D:
    r=lambda d,a,b: (d[:,b]-d[:,a]).mean()
    print(k,'gap(4o-mini->GPT-5)/gap(C3.5->GPT-5) arm %.4f P0 %.4f'%(r(D[k],lo,g5)/r(D[k],c35,g5), r(P0,lo,g5)/r(P0,c35,g5)))
