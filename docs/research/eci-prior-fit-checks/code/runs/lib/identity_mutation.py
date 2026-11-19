import sys, warnings; sys.path.insert(0,"runs"); warnings.filterwarnings("ignore")
import numpy as np, eci.bayesian as eb
from lib import data, models
df=data.fit_input(); A=eb.build_bayesian_model(df); base=A.initial_point(); rng=np.random.default_rng(1)
pt={k:v+rng.normal(0,.5,np.shape(v)) for k,v in base.items()}; la=float(A.compile_logp()(pt))
for name,kw in [("clip eps 1e-4",dict(eps=1e-4)),("tau_alpha prior sd 0.6",dict(priors={**models.DEFAULT_PRIORS,"tau_alpha":(float(np.log(.5)),.6)})),("reference prior",dict(spec=models.Spec(prior="reference")))]:
    try:
        B=models.build_model(df,**{**dict(spec=models.Spec()),**kw}); 
        pt2={k:pt[k] for k in B.initial_point() if k in pt}
        lb=float(B.compile_logp()({**B.initial_point(),**pt2})); print(name,"abs diff",abs(la-lb))
    except Exception as e: print(name,"error",type(e).__name__)
