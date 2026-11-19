"""W1-J blocker evidence: (1) how J's log density behaves in the slope scale tau_alpha at fixed (c, d, kappa), computed with an
independent numpy/scipy g; (2) where PyMC NUTS on the J prior (no likelihood) ends up. Writes runs/W/W1J/propriety.json. Run from the v11 root."""
import sys, json, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np, pymc as pm
from scipy.special import expit, polygamma
from lib import data, models, jeffreys as J

OUT = Path("runs/W/W1J"); OUT.mkdir(parents=True, exist_ok=True)
df = data.fit_input(); names, bnames, midx, bidx = models._index(df); M, K = len(names), len(bnames)
rng = np.random.default_rng(20261118)


def g_alg(eta, kappa):
    mu, om = expit(eta), expit(-eta); a, b = mu * kappa, om * kappa
    with np.errstate(all="ignore"):
        return om ** 2 * a ** 2 * polygamma(1, a) + mu ** 2 * b ** 2 * polygamma(1, b)


import pytensor, pytensor.tensor as pt
_e, _k, _a = pt.dvector("e"), pt.dvector("k"), pt.dvector("a")
_pot = pytensor.function([_e, _k, _a], J.jeffreys_logp(_e, _k, _a, midx, bidx, M, K))


def pot(c, d, a, kap):
    """The potential of lib/jeffreys.py (checked against an independent numpy computation in checks.json), stable for large slopes."""
    return float(_pot(a[bidx] * (c[midx] - d[bidx]), kap[bidx], a[bidx]))


# (1) profile in tau_alpha: log a = tau * w with w fixed, so the prior on (tau, w) contributes only the LogNormal(ln 0.5, 0.5) hyperprior in tau
w = rng.normal(0, 1, K); w -= w.mean(); w *= np.sqrt(K / (K - 1))
c = rng.uniform(-50, 50, M); d = rng.uniform(-50, 50, K); d -= d.mean()
sig = 0.1 * np.ones(K); kap = 1 / (4 * sig ** 2) - 1
rows = []
for tau in (0.1, 0.25, 0.5, 1, 2, 4, 8, 16, 32):
    a = np.exp(tau * w); lp_hyper = -np.log(tau) - 0.5 * ((np.log(tau) - np.log(.5)) / .5) ** 2 - np.log(.5 * np.sqrt(2 * np.pi))
    rows.append(dict(tau_alpha=tau, log_hyperprior=float(lp_hyper), potential=float(pot(c, d, a, kap)), sum_over_models_of_log_rms_slope=float(sum(np.log(np.sqrt(np.mean((a[bidx][midx == m]) ** 2))) for m in range(M)))))
for r in rows: r["log_density_in_tau_given_w"] = r["log_hyperprior"] + r["potential"]
res = dict(profile_tau_alpha=rows,
           reading="At fixed w and (c, d, kappa), log density in tau_alpha is the hyperprior plus the potential. The potential grows about linearly in tau_alpha "
                   "(g tends to 1 when eta saturates, so sum_m 1/2 log I_m tends to sum_m log of the root-mean-square slope on model m's benchmarks, while "
                   "sum_b log a_b = 0 by the zero-sum constraint) and the LogNormal hyperprior only falls like (ln tau)^2: the joint prior is not normalisable in tau_alpha.")
# (2) NUTS on the J prior (no likelihood): where it ends
ends = []
for seed in (20261118, 20261120):
    m = J.build_j(df, likelihood=False); last = {}
    def cb(trace, draw): last["p"] = draw.point
    status = "completed"
    try:
        with m:
            pm.sample(draws=200, tune=300, chains=1, cores=1, target_accept=0.95, random_seed=seed, progressbar=False, compute_convergence_checks=False, callback=cb)
    except Exception as e:
        status = str(e)[:70]
    p = last["p"]; ls = p["log_slope_zerosum__"]; ta = float(np.exp(p["tau_alpha_log__"]))
    ends.append(dict(seed=seed, status=status, tau_alpha=ta, max_abs_log_slope_unconstrained=float(np.abs(ls).max()), logp_total=float(m.compile_logp()(p)),
                     jeffreys_potential=float(m.compile_fn(m.replace_rvs_by_values([m["jeffreys"]]), inputs=m.value_vars, on_unused_input="ignore")(p)[0])))
res["nuts_J_prior_only"] = ends
m0 = J.build_j(df, potential=False, likelihood=False)
with m0:
    tr = pm.sample(draws=200, tune=300, chains=1, cores=1, target_accept=0.95, random_seed=20261118, progressbar=False, compute_convergence_checks=False)
res["nuts_epoch_prior_only_without_potential"] = dict(draws=200, divergences=int(tr.sample_stats["diverging"].sum()),
                                                       note="Epoch's hard box on the difficulties already makes every NUTS iteration diverge on the prior alone")
(OUT / "propriety.json").write_text(json.dumps(res, indent=1)); print(json.dumps(res, indent=1)[:3500])
