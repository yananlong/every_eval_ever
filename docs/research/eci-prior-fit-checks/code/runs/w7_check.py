"""Checks for runs/w7_models.py: (a) log density equals the frozen builder (F0, F2, F5) and the W6X family builder
at random points; (b) the numpy mu_kappa reproduces the model's observation log density for every feature."""
import sys; sys.path[:0] = ["runs/vendor/eci-public/src", "runs"]
import numpy as np, pandas as pd, warnings; warnings.filterwarnings("ignore")
from scipy.stats import beta as B
import w7_models as w7, w6x_family as fx
from lib import data, models, expand
df = data.fit_input(); ex = expand.extras_info(df); ex["fam_variant"] = "lin"
frozen = w7._frozen; rng = np.random.default_rng(1)
def rand_point(m):
    ip = m.initial_point(); return {k: v + rng.normal(0, .3, np.shape(v)) for k, v in ip.items()}
for feats, ref in (((), frozen), (("dev",), frozen), (("hetero",), frozen), (("fam",), fx.build_model_x)):
    sp = models.Spec(feats); a = w7.build(df, sp, ex=ex); b = ref(df, sp, ex=ex)
    p = rand_point(a); la, lb = a.compile_logp()(p), b.compile_logp()(p)
    print("logp", feats, float(la), float(lb), "equal" if np.isclose(la, lb, rtol=1e-9) else "DIFF")
a_ = pd.read_csv("runs/AUG/input_all.csv"); n = a_.groupby("cell").size(); multi = n[n > 1].index
mi = -np.ones(len(a_), int); pos = {c: i for i, c in enumerate(multi)}; mi = np.array([pos.get(c, -1) for c in a_.cell])
exa = expand.extras_for(a_, ex); exa.update(fam_variant="lin", multi_idx=mi, n_multi=len(multi))
for feats, d, e in ((("dev", "fam", "f1r", "skew", "hetero"), df, ex), (("dev", "fam", "f1r", "skew", "cell"), a_, exa)):
    m = w7.build(d, models.Spec(feats), ex=e); p = rand_point(m)
    outs = m.unobserved_value_vars
    vals = m.compile_fn(outs, inputs=m.value_vars, on_unused_input="ignore", point_fn=False)(*[p[v.name] for v in m.value_vars])
    P = {o.name: np.asarray(v)[None] for o, v in zip(outs, vals)}
    mu, kap = w7.mu_kappa(feats, P, d, e)
    y = np.clip(d.performance.to_numpy(), 1e-3, 1 - 1e-3)
    ln = B.logpdf(y, mu[0] * kap[0], (1 - mu[0]) * kap[0]).sum(); lm = float(m.compile_logp(vars=[m["obs"]])(p))
    print("mirror", feats, ln, lm, "equal" if np.isclose(ln, lm, rtol=1e-7) else "DIFF")
