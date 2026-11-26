"""Verification of the normalised capability-only Jeffreys priors J1 and J2 (lib/jeffreys_norm.py). Writes runs/W/W1J/checks_normalised.json.
Run from the v11 root, single thread."""
import sys, json, time, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pytensor, pytensor.tensor as pt
from scipy.special import expit, polygamma
from scipy.integrate import quad
from lib import data, models, jeffreys_norm as N

OUT = Path("runs/W/W1J"); OUT.mkdir(parents=True, exist_ok=True)
df = data.fit_input()
names, bnames, midx, bidx = models._index(df); M, K = len(names), len(bnames)
rng = np.random.default_rng(20261118)
obs_b = [bidx[midx == m] for m in range(M)]


def g_ref(eta, kappa, variant):
    """Independent g from the definition with scipy's trigamma (J1) or mu(1-mu) (J2)."""
    mu, om = expit(eta), expit(-eta)
    if variant == "J2":
        return mu * om
    return (mu * om) ** 2 * kappa ** 2 * (polygamma(1, mu * kappa) + polygamma(1, om * kappa))


def I_ref(c, m, a, d, k, variant):
    b = obs_b[m]; return float((a[b] ** 2 * g_ref(a[b] * (c - d[b]), k[b], variant)).sum())


def Z_quad(m, a, d, k, variant):
    b = obs_b[m]
    f = lambda c: np.sqrt((a[b] ** 2 * g_ref(a[b] * (c - d[b]), k[b], variant)).sum())
    return quad(f, -50, 50, points=sorted(set(np.clip(d[b], -49.9, 49.9))), limit=1000, epsabs=0, epsrel=1e-11)[0]


def pot_ref(c, a, d, k, variant, models_subset=None):
    tot = 0.0
    for m in range(M):
        tot += 0.5 * np.log(I_ref(c[m], m, a, d, k, variant)) - np.log(Z_quad(m, a, d, k, variant))
    return tot


def cf(m, outs):
    return m.compile_fn(m.replace_rvs_by_values(outs), inputs=m.value_vars, on_unused_input="ignore")


def points(model, n, sd_c, sd_d, sd_ls):
    base = model.initial_point(); out = []
    for _ in range(n):
        p = {}
        for k_, v in base.items():
            sd = sd_c if k_.startswith("capability") else sd_d if k_.startswith("difficulty") else sd_ls if k_.startswith("log_slope") else 0.3
            p[k_] = v + rng.normal(0, sd, np.shape(v))
        out.append(p)
    return out


res = {"quadrature": {"nodes": int(len(N.nodes()[0])), "rule": "composite Gauss-Legendre: unit panels with 8 nodes on [-16, 16], 4 panels of width 8.5 with 6 nodes on each side",
                      "valid_for": "difficulties within about +-16 (the W2 posterior means span -9.5 to 3.9, the largest draw 20.5) and slopes up to about 6"}}
mF0 = models.build_model(df, models.Spec())
fl0, fd0 = mF0.compile_logp(), mF0.compile_dlogp()
cap_f = cf(mF0, [mF0["capability"], mF0["difficulty"], mF0["slope"], mF0["kappa"]])
for variant in ("J1", "J2"):
    R = {}
    m0 = N.build_jn(df, variant, potential=False); mJ = N.build_jn(df, variant)
    fl1, fd1 = m0.compile_logp(), m0.compile_dlogp()
    pts = points(mF0, 50, 0.5, 0.5, 0.5)
    R["a_potential_removed_equals_F0"] = dict(n_points=50, logp_exactly_equal=bool(all(fl0(p) == fl1(p) for p in pts)),
                                              grad_exactly_equal=bool(all(np.array_equal(fd0(p), fd1(p)) for p in pts)))
    potfn = cf(mJ, [mJ["jeffreys_norm"]]); cap_j = cf(mJ, [mJ["capability"], mJ["difficulty"], mJ["slope"], mJ["kappa"]])
    # (b) potential against independent numpy/scipy with Z_m by quad, at 20 points with difficulties spread over about +-8
    rel, zerr = [], []
    for p in points(mJ, 20, 0.5, 2.5, 0.4):
        c, d, a, k = cap_j(p)
        ref = pot_ref(c, a, d, k, variant); val = float(potfn(p)[0]); rel.append(abs(val - ref) / abs(ref))
        for m in rng.choice(M, 6, replace=False):
            x, w = N.nodes(); b = obs_b[m]
            G = (a[b][:, None] ** 2 * N.g_np(a[b][:, None] * (x[None, :] - d[b][:, None]), k[b][:, None], variant)).sum(0)
            zq = Z_quad(m, a, d, k, variant); zerr.append(abs((w * np.sqrt(G)).sum() - zq) / zq)
    R["b_potential_vs_numpy_quad"] = dict(n_points=20, max_rel_err=float(max(rel)), tol=1e-6, passed=bool(max(rel) < 1e-6),
                                          Z_m_vs_scipy_quad=dict(n=len(zerr), max_rel_err=float(max(zerr)), tol=1e-6, passed=bool(max(zerr) < 1e-6)))
    # (c) gradient against central finite differences
    pot_expr = mJ.replace_rvs_by_values([mJ["jeffreys_norm"]])[0]; vv = mJ.value_vars
    gfn = mJ.compile_fn(pytensor.grad(pot_expr, vv, disconnected_inputs="ignore"), inputs=vv, on_unused_input="ignore")
    pfn = mJ.compile_fn(pot_expr, inputs=vv, on_unused_input="ignore"); order = [v.name for v in vv]; errs = []
    for p in points(mJ, 3, 0.5, 2.0, 0.4):
        gr = dict(zip(order, gfn(p)))
        for _ in range(6):
            dirs = {k_: rng.normal(0, 1, np.shape(v)) for k_, v in p.items()}; nrm = np.sqrt(sum((v ** 2).sum() for v in dirs.values())); dirs = {k_: v / nrm for k_, v in dirs.items()}
            an = sum((gr[k_] * dirs[k_]).sum() for k_ in p); h = 1e-3
            f_ = lambda t: float(pfn({k_: p[k_] + t * dirs[k_] for k_ in p}))
            fd = (-f_(2 * h) + 8 * f_(h) - 8 * f_(-h) + f_(-2 * h)) / (12 * h)
            errs.append(abs(an - fd) / max(abs(an), 1e-12))
    R["c_gradient_finite_difference"] = dict(n_directional=len(errs), step=1e-3, stencil='4-point central', max_rel_err=float(max(errs)), tol=1e-6, passed=bool(max(errs) < 1e-6))
    # (d) normalisation: the density sqrt(I_m)/Z_m, with Z_m from the quadrature rule, integrates to 1 on [-50, 50]
    p = points(mJ, 1, 0.5, 2.5, 0.4)[0]; c, d, a, k = cap_j(p); x, w = N.nodes(); ints = []
    for m in rng.choice(M, 8, replace=False):
        b = obs_b[m]; G = (a[b][:, None] ** 2 * N.g_np(a[b][:, None] * (x[None, :] - d[b][:, None]), k[b][:, None], variant)).sum(0); Zn = (w * np.sqrt(G)).sum()
        ints.append(quad(lambda cc: np.sqrt(I_ref(cc, m, a, d, k, variant)) / Zn, -50, 50, points=sorted(set(np.clip(d[b], -49.9, 49.9))), limit=1000, epsabs=0, epsrel=1e-11)[0])
    R["d_normalisation"] = dict(n_models=8, integrals=[float(v) for v in ints], max_abs_dev_from_1=float(max(abs(np.array(ints) - 1))), tol=1e-6, passed=bool(max(abs(np.array(ints) - 1)) < 1e-6))
    # (e) slope pressure: at fixed w, (c, d, kappa), the potential over tau_alpha (log a = tau w). Analogue of propriety.json.
    w_ = rng.normal(0, 1, K); w_ -= w_.mean(); w_ *= np.sqrt(K / (K - 1)); cc = rng.uniform(-12, 12, M); dd = rng.uniform(-12, 12, K); dd -= dd.mean()
    kk = 1 / (4 * 0.1 ** 2) - 1; kap = np.full(K, kk)
    _c, _d, _a, _k = (pt.dvector(n) for n in "cdak")
    pf = pytensor.function([_c, _d, _a, _k], N.norm_potential(_a * 0 + 0, _a, _a, _k, midx, bidx, M, K, variant) if False else N.norm_potential(_c, _d, _a, _k, midx, bidx, M, K, variant), on_unused_input="ignore")
    rows = []
    for tau in (0.1, 0.25, 0.5, 1, 2, 4, 8, 16, 32):
        a_ = np.exp(tau * w_); v = float(pf(cc, dd, a_, kap))
        sub = rng.choice(M, 12, replace=False); x_, w_n = N.nodes()
        I_np = lambda c_, m: float((a_[obs_b[m]] ** 2 * N.g_np(a_[obs_b[m]] * (c_ - dd[obs_b[m]]), kap[obs_b[m]], variant)).sum())
        Zn = lambda m: float((w_n * np.sqrt((a_[obs_b[m]][:, None] ** 2 * N.g_np(a_[obs_b[m]][:, None] * (x_[None, :] - dd[obs_b[m]][:, None]), kap[obs_b[m]][:, None], variant)).sum(0))).sum())
        mine = sum(0.5 * np.log(I_np(cc[m], m)) - np.log(Zn(m)) for m in sub)
        ind = sum(0.5 * np.log(I_np(cc[m], m)) - np.log(Z_quad(m, a_, dd, kap, variant)) for m in sub) if tau <= 2 else None
        rows.append(dict(tau_alpha=tau, potential=v, per_model=v / M, quadrature_vs_quad_on_12_models_abs_diff=(None if ind is None else float(abs(ind - mine)))))
    pv = np.array([r["potential"] for r in rows])
    R["e_slope_pressure"] = dict(profile=rows, range_over_tau=float(pv.max() - pv.min()), per_model_range=float((pv.max() - pv.min()) / M),
                                 reading="no upward trend in tau_alpha (the original J rose by about 15,000): the potential is the log of a normalised density in c_m, so it is bounded above in the slope scale; at fixed (c, d) it flattens (J1) or falls (J2). Beyond tau_alpha of about 2 the slopes exceed the quadrature rule's range (about 6), so those values are indicative")
    # (f) cost per log density plus gradient
    def cost(m):
        f1, f2 = m.compile_logp(), m.compile_dlogp(); p = m.initial_point(); f1(p); f2(p); t = time.perf_counter()
        for _ in range(40): f1(p); f2(p)
        return (time.perf_counter() - t) / 40
    R["f_cost_seconds_per_logp_plus_grad"] = dict(F0=cost(mF0), variant=cost(mJ)); R["f_cost_seconds_per_logp_plus_grad"]["ratio"] = R["f_cost_seconds_per_logp_plus_grad"]["variant"] / R["f_cost_seconds_per_logp_plus_grad"]["F0"]
    res[variant] = R
(OUT / "checks_normalised.json").write_text(json.dumps(res, indent=1))
for v in ("J1", "J2"):
    r = res[v]; print(v, {k: r[k].get("passed", r[k].get("logp_exactly_equal")) for k in r if isinstance(r[k], dict) and k != "e_slope_pressure" and k != "f_cost_seconds_per_logp_plus_grad"},
                    r["b_potential_vs_numpy_quad"]["max_rel_err"], r["c_gradient_finite_difference"]["max_rel_err"], r["d_normalisation"]["max_abs_dev_from_1"], r["e_slope_pressure"]["per_model_range"], r["f_cost_seconds_per_logp_plus_grad"])
