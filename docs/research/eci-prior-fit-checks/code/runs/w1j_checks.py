"""Checks (a)-(d) of the Jeffreys prior J builder (lib/jeffreys.py). Writes runs/W/W1J/checks.json. Run from the v11 root."""
import sys, json, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pytensor, pytensor.tensor as pt
from scipy.special import polygamma, expit, betaln
from scipy.stats import beta as sbeta
from lib import data, models, jeffreys as J

OUT = Path("runs/W/W1J"); OUT.mkdir(parents=True, exist_ok=True)
df = data.fit_input()
names, bnames, midx, bidx = models._index(df)
M, K = len(names), len(bnames)
y = np.clip(df["performance"].to_numpy(float), 1e-3, 1 - 1e-3)
rng = np.random.default_rng(20261118)
res = {}


def g_ref(eta, kappa):
    """Independent numpy/scipy g from the definition."""
    mu, om = expit(eta), expit(-eta)
    return (mu * om) ** 2 * kappa ** 2 * (polygamma(1, mu * kappa) + polygamma(1, om * kappa))


def g_alg(eta, kappa):
    """The same g in the form (1 - mu)^2 a^2 psi1(a) + mu^2 b^2 psi1(b), a = mu kappa, b = (1 - mu) kappa (scipy psi1, no recurrence)."""
    mu, om = expit(eta), expit(-eta)
    a, b = mu * kappa, om * kappa
    return om ** 2 * a ** 2 * polygamma(1, a) + mu ** 2 * b ** 2 * polygamma(1, b)


def cf(m, outs):
    """Compile outputs given in terms of the model's random variables as a function of its value variables."""
    return m.compile_fn(m.replace_rvs_by_values(outs), inputs=m.value_vars, on_unused_input="ignore")


def points(model, n, scale):
    base = model.initial_point()
    out = []
    for _ in range(n):
        p = {k: v + rng.normal(0, scale, np.shape(v)) for k, v in base.items()}
        out.append(p)
    return out


mF0 = models.build_model(df, models.Spec())
mJ0 = J.build_j(df, potential=False)
mJ = J.build_j(df)
mP = J.build_j(df, likelihood=False)

# (a) without the potential, J is F0
fl0, fd0, fl1, fd1 = mF0.compile_logp(), mF0.compile_dlogp(), mJ0.compile_logp(), mJ0.compile_dlogp()
pts = points(mF0, 50, 0.5)
eq_l = all(fl0(p) == fl1(p) for p in pts)
eq_d = all(np.array_equal(fd0(p), fd1(p)) for p in pts)
res["a_potential_removed_equals_F0"] = dict(n_points=50, logp_exactly_equal=bool(eq_l), grad_exactly_equal=bool(eq_d),
                                            same_value_vars=[v.name for v in mF0.value_vars] == [v.name for v in mJ0.value_vars])
# prior-only variant: logp equals F0's minus the Beta log-likelihood
cap_f = cf(mF0, [mF0["capability"], mF0["difficulty"], mF0["slope"], mF0["kappa"]])
mPnp = J.build_j(df, potential=False, likelihood=False)
flPnp = mPnp.compile_logp()
errs = []
for p in pts[:10]:
    c, d, a, k = cap_f(p)
    eta = a[bidx] * (c[midx] - d[bidx]); mu = np.clip(expit(eta), 1e-6, 1 - 1e-6); kb = k[bidx]
    ll = ((mu * kb - 1) * np.log(y) + ((1 - mu) * kb - 1) * np.log1p(-y) - betaln(mu * kb, (1 - mu) * kb)).sum()
    errs.append(abs((fl0(p) - ll) - flPnp(p)))
res["a_prior_only_equals_F0_minus_loglik"] = dict(n_points=10, max_abs_err=float(max(errs)), observed_RVs=[v.name for v in mPnp.observed_RVs])

# (b) potential value vs independent numpy/scipy
potfn = cf(mJ, [mJ["jeffreys"]])
cap_j = cf(mJ, [mJ["capability"], mJ["difficulty"], mJ["slope"], mJ["kappa"]])
def pot_ref(c, d, a, k, g):
    eta = a[bidx] * (c[midx] - d[bidx]); e = a[bidx] ** 2 * g(eta, k[bidx])
    return 0.5 * np.log(np.bincount(midx, e, M)).sum() + 0.5 * np.log(np.bincount(bidx, e, K)).sum(), float(np.abs(eta).max())


rel, extremes, rel_tail, ext_tail = [], [], [], []
while len(rel) < 20:
    p = points(mJ, 1, 0.7)[0]; c, d, a, k = cap_j(p)
    ref, mx = pot_ref(c, d, a, k, g_ref)
    if mx < 100 and np.isfinite(ref):
        val = float(potfn(p)[0]); rel.append(abs(val - ref) / abs(ref)); extremes.append(mx)
while len(rel_tail) < 20:
    p = points(mJ, 1, 1.0)[0]; c, d, a, k = cap_j(p)
    ref, mx = pot_ref(c, d, a, k, g_alg)
    if 30 < mx < 300 and np.isfinite(ref):
        val = float(potfn(p)[0]); rel_tail.append(abs(val - ref) / abs(ref)); ext_tail.append(mx)
res["b_potential_tail_points"] = dict(n_points=20, reference="algebraic form with scipy psi1", max_rel_err=float(max(rel_tail)), max_abs_eta=float(max(ext_tail)), passed=bool(max(rel_tail) < 1e-8))
res["b_potential_vs_numpy"] = dict(n_points=20, max_rel_err=float(max(rel)), max_abs_eta_over_points=float(max(extremes)), tol=1e-8, passed=bool(max(rel) < 1e-8))
# g itself: the pytensor expression against the definition, and against Monte Carlo Var(score)
etas, kap = pt.dvector("eta"), pt.dvector("kap")
glog = pytensor.function([etas, kap], J.log_info_g(etas, kap))
mc = []
for mu, kappa in [(0.5, 4.0), (0.2, 10.0), (0.05, 25.0), (0.9, 10.0), (0.5, 100.0), (0.3, 5.0)]:
    a_, b_ = mu * kappa, (1 - mu) * kappa
    draws = sbeta.rvs(a_, b_, size=1_000_000, random_state=rng)
    assert draws.min() > 0 and draws.max() < 1
    from scipy.special import digamma
    score = kappa * (np.log(draws) - np.log1p(-draws) - digamma(a_) + digamma(b_)) * mu * (1 - mu)
    eta0 = float(np.log(mu / (1 - mu)))
    gm = float(score.var()); gt = float(np.exp(glog(np.array([eta0]), np.array([kappa]))[0])); gr = float(g_ref(eta0, kappa))
    mc.append(dict(mu=mu, kappa=kappa, g_formula=gr, g_pytensor=gt, g_monte_carlo=gm, mc_mean_score=float(score.mean()),
                   rel_err_pytensor_vs_formula=abs(gt - gr) / gr, rel_err_mc=abs(gm - gr) / gr))
res["b_g_monte_carlo"] = dict(draws=1_000_000, rows=mc, max_rel_err_mc=max(r["rel_err_mc"] for r in mc))
# trigamma implementation against scipy
x = pt.dvector("x"); tg = pytensor.function([x], J.trigamma1p(x))
xs = np.concatenate([[0.0, 1e-8, 1e-3, .1, .5, 1, 2.5, 5, 6, 7, 50, 1e3, 1e6, 1e12], rng.uniform(0, 30, 2000), 10 ** rng.uniform(-6, 8, 2000)])
r_ = np.abs(tg(xs) - polygamma(1, xs + 1)) / polygamma(1, xs + 1)
res["b_trigamma_vs_scipy"] = dict(n=len(xs), max_rel_err=float(r_.max()), tol=1e-10, passed=bool(r_.max() < 1e-10))
# extreme eta: finite and equal to the limit g -> 1
ee = np.array([-700., -300., -50., -20., 20., 50., 300., 700.])
ge = np.exp(glog(ee, np.full(8, 20.0)))
res["b_extreme_eta"] = dict(eta=ee.tolist(), g_at_kappa20=ge.tolist(), all_finite=bool(np.isfinite(ge).all()))

# (c) gradient of the potential against central finite differences, along random directions and on single coordinates
potg = mJ.compile_fn(mJ.potentials[0]) if False else None
vv = mJ.value_vars
pot_expr = mJ.replace_rvs_by_values([mJ["jeffreys"]])[0]
gfn = mJ.compile_fn(pytensor.grad(pot_expr, vv, disconnected_inputs="ignore"), inputs=vv, on_unused_input="ignore")
pfn = mJ.compile_fn(pot_expr, inputs=vv, on_unused_input="ignore")
order = [v.name for v in vv]
c_res = []
for p in points(mJ, 3, 0.5):
    grads = dict(zip(order, gfn(p)))
    for _ in range(6):
        dirs = {k: rng.normal(0, 1, np.shape(v)) for k, v in p.items()}
        nrm = np.sqrt(sum((v ** 2).sum() for v in dirs.values())); dirs = {k: v / nrm for k, v in dirs.items()}
        an = sum((grads[k] * dirs[k]).sum() for k in p)
        h = 1e-5
        fp = pfn({k: p[k] + h * dirs[k] for k in p}); fm = pfn({k: p[k] - h * dirs[k] for k in p})
        fd = (float(fp) - float(fm)) / (2 * h)
        c_res.append(abs(an - fd) / max(abs(an), 1e-12))
res["c_gradient_finite_difference"] = dict(n_directional=len(c_res), step=1e-5, max_rel_err=float(max(c_res)), tol=1e-6, passed=bool(max(c_res) < 1e-6))

# (d) tails: one model, others fixed; 1/2 log I_m(c) over c in [-50, 50], and the same for one benchmark's difficulty
p0 = points(mJ, 1, 0.5)[0]; c0, d0, a0, k0 = cap_j(p0)
m_i = int(np.bincount(midx).argmax()); sel = midx == m_i
grid = np.array([-50, -40, -30, -20, -15, -10, -7, -5, -3, -2, -1, 0, 1, 2, 3, 5, 7, 10, 15, 20, 30, 40, 50.0])
half_log_Im = []
for cc in grid:
    eta = a0[bidx[sel]] * (cc - d0[bidx[sel]])
    half_log_Im.append(0.5 * np.log((a0[bidx[sel]] ** 2 * g_alg(eta, k0[bidx[sel]])).sum()))
plateau = 0.5 * np.log((a0[bidx[sel]] ** 2).sum())
hl = np.array(half_log_Im)
res["d_tail_behaviour"] = dict(model=names[m_i], n_cells=int(sel.sum()), c_grid=grid.tolist(), half_log_I_m=hl.tolist(),
                               limit_half_log_sum_a2=float(plateau), slope_over_c_20_to_50=float((hl[-1] - hl[-5]) / (grid[-1] - grid[-5])),
                               slope_over_c_minus50_to_minus20=float((hl[3] - hl[0]) / (grid[3] - grid[0])),
                               max_abs_gap_to_plateau_at_abs_c_ge_30=float(np.abs(hl[np.abs(grid) >= 30] - plateau).max()),
                               reading="half log I_m does not decay: g tends to 1 as |eta| grows (Beta shape below 1), so I_m tends to the sum of squared slopes and "
                                       "the density sqrt(I_m) is bounded below in the tails; it is proper only because the c box [-50, 50] is kept")
(OUT / "checks.json").write_text(json.dumps(res, indent=1))
print(json.dumps({k: (v if k not in ("b_g_monte_carlo", "d_tail_behaviour") else "...") for k, v in res.items()}, indent=1)[:3500])
print(json.dumps(res["b_g_monte_carlo"]["rows"], indent=0)[:1500]); print(res["d_tail_behaviour"])
