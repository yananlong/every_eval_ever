"""F0 against Epoch's build_bayesian_model on the real fit input (plan M12 EQ item 1, owner's step 1b)."""
import sys, json, warnings
sys.path.insert(0, "runs")
warnings.filterwarnings("ignore")
import numpy as np
import eci.bayesian as eb
from lib import data, models

df = data.fit_input()
A = eb.build_bayesian_model(df)                  # Epoch's
B = models.build_model(df, models.Spec())        # ours
out = {"structure": {}, "points": {}}

def desc(m):
    d = {}
    shp = m.eval_rv_shapes()
    for rv in m.free_RVs:
        tr = m.rvs_to_transforms.get(rv)
        d[rv.name] = dict(shape=[int(x) for x in shp[rv.name]], dist=type(rv.owner.op).__name__,
                          transform=type(tr).__name__ if tr is not None else None,
                          value=m.rvs_to_values[rv].name)
    d["observed"] = [rv.name for rv in m.observed_RVs]
    d["potentials"] = [p.name for p in m.potentials]
    d["deterministics"] = [v.name for v in m.deterministics]
    d["coords"] = {k: len(v) for k, v in m.coords.items()}
    return d
da, db = desc(A), desc(B)
out["structure"]["identical_description"] = (da == db)
out["structure"]["epoch"] = da; out["structure"]["ours"] = db
# data identity of the observed variable
ya = A["obs"].eval() if False else None
obsA = A.rvs_to_values[A["obs"]].get_value() if hasattr(A.rvs_to_values[A["obs"]], "get_value") else None
yA = np.asarray(A.rvs_to_values[A["obs"]].data) if hasattr(A.rvs_to_values[A["obs"]], "data") else None
yB = np.asarray(B.rvs_to_values[B["obs"]].data) if hasattr(B.rvs_to_values[B["obs"]], "data") else None
out["structure"]["observed_equal"] = bool(yA is not None and yB is not None and np.array_equal(yA, yB))
out["structure"]["constants"] = {"MU_EPS": [eb._MU_EPS, models.MU_EPS], "MAX_SIGMA": [eb._MAX_SIGMA, models.MAX_SIGMA],
                                 "CD_BOUND": [eb._CD_BOUND, models.CD_BOUND]}
out["structure"]["free_vars_equal"] = list(eb._FREE_VARS) == models.BASE_FREE and list(eb._DIAGNOSTIC_VARS) == models.BASE_DIAG
names = [v.name for v in A.value_vars]
assert names == [v.name for v in B.value_vars], (names, [v.name for v in B.value_vars])
fa, fb = A.compile_logp(), B.compile_logp()
ga, gb = A.compile_dlogp(), B.compile_dlogp()
base = A.initial_point()
rng = np.random.default_rng(20261118)
N = 300
maxrel_l = maxrel_g = 0.0; maxabs_l = 0.0
terms = {}
# per-term functions
def termfns(m):
    fs = {}
    for rv in list(m.free_RVs) + list(m.observed_RVs):
        fs[rv.name] = m.compile_fn(m.logp(vars=[rv], jacobian=True), inputs=m.value_vars, point_fn=True, on_unused_input='ignore')
    return fs
ta, tb = termfns(A), termfns(B)
tmax = {k: 0.0 for k in ta}; tmax['potential_residual'] = 0.0
def rel(x, y): return float(np.max(np.abs(x - y) / np.maximum(1.0, np.abs(x))))
for i in range(N):
    pt = {k: v + rng.normal(0, 0.7 if i % 2 else 0.1, np.shape(v)) for k, v in base.items()}
    if i % 5 == 0: pt = {k: v + rng.normal(0, 1.5, np.shape(v)) for k, v in base.items()}
    la, lb = float(fa(pt)), float(fb(pt))
    ga_, gb_ = np.asarray(ga(pt)), np.asarray(gb(pt))
    maxrel_l = max(maxrel_l, abs(la - lb) / max(1.0, abs(la))); maxabs_l = max(maxabs_l, abs(la - lb))
    maxrel_g = max(maxrel_g, float(np.max(np.abs(ga_ - gb_) / np.maximum(1.0, np.abs(ga_)))))
    ra = la - sum(float(ta[k](pt)) for k in ta); rb = lb - sum(float(tb[k](pt)) for k in tb)
    tmax['potential_residual'] = max(tmax['potential_residual'], abs(ra - rb))
    for k in ta:
        tmax[k] = max(tmax[k], abs(float(ta[k](pt)) - float(tb[k](pt))) / max(1.0, abs(float(ta[k](pt)))))
out["points"] = dict(n=N, max_rel_logp=maxrel_l, max_abs_logp=maxabs_l, max_rel_dlogp=maxrel_g,
                     per_term_max_rel=tmax, logp_example=la, grad_len=int(ga_.size),
                     requirement=dict(logp=1e-8, grad=1e-6),
                     passed=bool(maxrel_l <= 1e-8 and maxrel_g <= 1e-6 and all(v <= 1e-8 for v in tmax.values())))
# the potential (difficulty bound) is a constant 0 inside the box; test an out-of-box point returns -inf in both
pt = dict(base); pt["difficulty_zerosum__"] = np.full_like(base["difficulty_zerosum__"], 80.0)
out["points"]["potential_outside_box"] = [float(fa(pt)), float(fb(pt))]
# anchoring: Epoch's function is used itself (fit_bayesian_eci with our builder swapped in), so identical by construction
json.dump(out, open(sys.argv[1], "w"), indent=1, default=str)
print(json.dumps(out["points"], indent=1)); print("identical_description", out["structure"]["identical_description"], out["structure"]["observed_equal"], out["structure"]["free_vars_equal"])
if not out["structure"]["identical_description"]:
    for k in da:
        if da[k] != db[k]: print("DIFF", k, da[k], db[k])
