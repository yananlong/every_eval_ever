"""W7 diagnostics follow-up (exploratory, outside every registered verdict): targeted changes to W7 candidate G3
(developer-by-benchmark offsets plus lineage-family offsets). New code only; runs/w7_models.py is imported, not edited.

Features (any subset; ("dev", "fam") alone is G3 exactly):
  dev   developer-by-benchmark offsets on the logit, as G3.
  fam   per-model family offsets on capability, as G3. The families are the five lineage families of
        runs/w6x_family.py plus, when ex["clusters"] is given, the residual clusters named there (CLUSTERS below).
        The clusters were read off G3_ta99's residual correlation matrix (runs/w7d_diag.py), so they are post hoc:
        any gain they show on the same data is optimistic.
  bnd   boundary mass from item-count discreteness (aims at T6, and at the ceiling of OTIS Mock AIME in T1).
        A benchmark with n items scores 0 with probability E[(1 - p)^n] and 1 with probability E[p^n] when the
        per-run success rate p is Beta(mu kappa, (1 - mu) kappa); both have closed forms (beta-binomial):
            P0 = B(a, b + n) / B(a, b),  P1 = B(a + n, b) / B(a, b),  a = mu kappa, b = (1 - mu) kappa.
        The likelihood is a hurdle: mass P0 at scores <= eps, mass P1 at scores >= 1 - eps, and otherwise
        (1 - P0 - P1) times a Beta density with the same kappa and mean (mu - P1) / (1 - P0 - P1), so that the
        overall mean stays mu, as it is for a beta-binomial. n[b] = exp(log_n[b]), log_n ~ Normal(log 100, 1.5):
        the effective item count is learned per benchmark, because item counts are unknown for most sources.
  bndc  as bnd, but a score at a bound is given the whole mass the model puts there: P0 plus the interior Beta's
        mass below eps (and P1 plus its mass above 1 - eps). Under bnd the interior Beta keeps mass below eps
        that the likelihood of a zero ignores, so the fit over-predicts zeros (H1_ta99: 79.7 expected, 59 seen);
        bndc removes that inconsistency. Use one of bnd and bndc, not both.
`predict` mirrors the builder in numpy; `rq` gives the residual quantities the frozen lib/ppc_checks.stats needs;
`simulate` draws model-true scores. `install()` swaps the builder and registers the variable lists in memory."""
import numpy as np
import pymc as pm
import pytensor.tensor as pt
from pymc.distributions.transforms import ZeroSumTransform
from scipy.special import betainc, gammaln
from lib import models
import w6x_family as fx
from lib.models import MU_EPS, MAX_SIGMA, CD_BOUND, DEFAULT_PRIORS, _index

EPS = 1e-3
FREE = {"dev": ["zeta", "tau_delta"], "fam": ["w_fam", "tau_fam"], "bnd": ["log_n"], "bndc": ["log_n"]}
DIAG = {"dev": ["zeta", "tau_delta"], "fam": ["w_fam", "tau_fam"], "bnd": ["log_n"], "bndc": ["log_n"]}
BND = {"bnd", "bndc"}
LOG_N_PRIOR = (float(np.log(100.0)), 1.5)

# Residual clusters of G3_ta99 whose mean within-cluster residual correlation lies beyond the 99% posterior
# predictive envelope (runs/W/W7/diag/diag_G3_ta99_all.json, "clusters"); the two adjacent knowledge/reasoning QA
# clusters are merged because their cross pairs are also beyond the envelope.
CLUSTERS = {
    "clu:oldLM": ["HellaSwag", "LAMBADA", "PIQA", "Winogrande", "TriviaQA"],
    "clu:knowQA": ["DTBench", "LMCA", "Balrog", "SimpleQA Verified", "SimpleBench", "Mystery Game Puzzles", "DeepResearch Bench"],
    "clu:math": ["MATH level 5", "OTIS Mock AIME 2024-2025", "FrontierMath-Tiers-1-3-v2-Private"],
}


def _tail_mass(a, b, x, terms=30):
    """Regularised incomplete beta I_x(a, b) for small x by its hypergeometric series,
    x^a (1 - x)^b / (a B(a, b)) * sum_k (a + b)_k / (a + 1)_k x^k. pt.betainc has a gradient about 100 times
    slower; with x = 0.001 and a + b below about 400 the 30-term series is accurate to better than 1e-9 relative."""
    term = pt.ones_like(a); tot = pt.ones_like(a)
    for k in range(terms):
        term = term * (a + b + k) / (a + 1.0 + k) * x; tot = tot + term
    return pt.exp(a * np.log(x) + b * np.log1p(-x) - pt.log(a) - (pt.gammaln(a) + pt.gammaln(b) - pt.gammaln(a + b))) * tot


def fam_matrix(bench_names, clusters=None):
    A, names = fx.families(bench_names, "lin")
    for g, mem in (clusters or {}).items():
        col = np.array([[float(b in mem)] for b in bench_names])
        if col.sum() >= 2: A = np.hstack([A, col]); names = list(names) + [g]
    return A, list(names)


def build(df, spec=models.Spec(), priors=None, eps=EPS, ex=None):
    f = set(spec.features)
    assert spec.prior == "epoch" and f <= set(FREE), spec
    priors = priors or DEFAULT_PRIORS
    model_names, bench_names, midx, bidx = _index(df)
    K = len(bench_names)
    yraw = df["performance"].to_numpy(dtype=float)
    y = np.clip(yraw, eps, 1.0 - eps)
    with pm.Model(coords={"model": model_names, "benchmark": bench_names}) as model:
        tau_alpha = pm.LogNormal("tau_alpha", mu=priors["tau_alpha"][0], sigma=priors["tau_alpha"][1])
        sigma_median = pm.LogNormal("sigma_median", mu=priors["sigma_median"][0], sigma=priors["sigma_median"][1])
        tau_sigma = pm.LogNormal("tau_sigma", mu=priors["tau_sigma"][0], sigma=priors["tau_sigma"][1])
        sigma = pm.Truncated("sigma", pm.LogNormal.dist(mu=pm.math.log(sigma_median), sigma=tau_sigma),
                             lower=0.0, upper=MAX_SIGMA, dims="benchmark")
        pm.Deterministic("kappa", 1.0 / (4.0 * sigma ** 2) - 1.0, dims="benchmark")
        zsc = np.sqrt(K / (K - 1))
        capability = pm.Uniform("capability", -CD_BOUND, CD_BOUND, dims="model")
        difficulty = pm.Flat("difficulty", dims="benchmark", transform=ZeroSumTransform([-1]))
        pm.Potential("difficulty_bound", pm.math.switch(pm.math.all(pm.math.abs(difficulty) <= CD_BOUND), 0.0, -np.inf))
        log_slope = pm.ZeroSumNormal("log_slope", sigma=tau_alpha * zsc, dims="benchmark")
        slope = pm.Deterministic("slope", pm.math.exp(log_slope), dims="benchmark")
        cap_row = capability[midx]
        if "fam" in f:
            A, gnames = fam_matrix(bench_names, ex.get("clusters"))
            model.add_coord("family", gnames)
            tau_f = pm.HalfNormal("tau_fam", 0.5, dims="family")
            w = pm.Normal("w_fam", 0.0, 1.0, dims=("model", "family"))
            cap_row = cap_row + (w[midx] * (A[bidx] * tau_f[None, :])).sum(axis=1)
        eta = slope[bidx] * (cap_row - difficulty[bidx])
        if "dev" in f:
            tau_d = pm.HalfNormal("tau_delta", 0.5)
            zeta = pm.Normal("zeta", 0.0, 1.0, shape=ex["n_cells"])
            delta = pt.concatenate([tau_d * zeta, pt.zeros(1)])
            ci = np.where(ex["cell_idx"] < 0, ex["n_cells"], ex["cell_idx"])
            eta = eta + delta[ci]
        mu = pm.math.clip(pm.math.sigmoid(eta), MU_EPS, 1.0 - MU_EPS)
        kappa_obs = (1.0 / (4.0 * sigma ** 2) - 1.0)[bidx]
        if not (f & BND):
            pm.Beta("obs", alpha=mu * kappa_obs, beta=(1.0 - mu) * kappa_obs, observed=y)
        else:
            log_n = pm.Normal("log_n", LOG_N_PRIOR[0], LOG_N_PRIOR[1], dims="benchmark")
            n_row = pt.exp(log_n)[bidx]
            is0, is1 = y <= eps, y >= 1.0 - eps   # fixed by the data the model is built on
            cens = "bndc" in f; i0, i1 = np.where(is0)[0], np.where(is1)[0]

            def logp(value, mu_, kap_, n_):
                a, b = mu_ * kap_, (1.0 - mu_) * kap_
                lp0 = pt.gammaln(b + n_) + pt.gammaln(a + b) - pt.gammaln(b) - pt.gammaln(a + b + n_)
                lp1 = pt.gammaln(a + n_) + pt.gammaln(a + b) - pt.gammaln(a) - pt.gammaln(a + b + n_)
                p1 = pt.exp(lp1); wgt = pt.clip(1.0 - pt.exp(lp0) - p1, 1e-12, 1.0)
                mi = pt.clip((mu_ - p1) / wgt, MU_EPS, 1.0 - MU_EPS)
                ai, bi = mi * kap_, (1.0 - mi) * kap_
                lbeta = (pt.gammaln(ai + bi) - pt.gammaln(ai) - pt.gammaln(bi)
                         + (ai - 1.0) * pt.log(value) + (bi - 1.0) * pt.log1p(-value))
                if not cens:
                    return pt.switch(is0, lp0, pt.switch(is1, lp1, pt.log(wgt) + lbeta))
                out = pt.log(wgt) + lbeta          # rows at a bound: hurdle mass plus the interior Beta's mass beyond the clip
                if len(i0):
                    out = pt.set_subtensor(out[i0], pt.log(pt.exp(lp0[i0]) + wgt[i0] * _tail_mass(ai[i0], bi[i0], eps)))
                if len(i1):
                    out = pt.set_subtensor(out[i1], pt.log(p1[i1] + wgt[i1] * _tail_mass(bi[i1], ai[i1], eps)))
                return out

            pm.CustomDist("obs", mu, kappa_obs, n_row, logp=logp, observed=y)
    return model


def predict(feats, P, df, ex):
    """P: posterior arrays with a leading draw axis. Returns per-draw, per-row mu, kappa and, with bnd, the
    boundary masses p0, p1 and the interior Beta mean mu_i (without bnd: p0 = p1 = 0 and mu_i = mu)."""
    f = set(feats)
    _, bench_names, midx, bidx = _index(df)
    cap = P["capability"][:, midx]
    if "fam" in f:
        A, _ = fam_matrix(bench_names, ex.get("clusters"))
        cap = cap + (P["w_fam"][:, midx, :] * (A[bidx][None] * P["tau_fam"][:, None, :])).sum(-1)
    eta = P["slope"][:, bidx] * (cap - P["difficulty"][:, bidx])
    if "dev" in f:
        delta = np.concatenate([P["tau_delta"][:, None] * P["zeta"], np.zeros((P["zeta"].shape[0], 1))], axis=1)
        eta = eta + delta[:, np.where(ex["cell_idx"] < 0, ex["n_cells"], ex["cell_idx"])]
    mu = np.clip(np.exp(-np.logaddexp(0.0, -np.clip(eta, -700, 700))), MU_EPS, 1 - MU_EPS)
    kap = (1 / (4 * P["sigma"] ** 2) - 1)[:, bidx]
    out = dict(mu=mu, kap=kap, p0=np.zeros_like(mu), p1=np.zeros_like(mu), mu_i=mu)
    if f & BND:
        n = np.exp(P["log_n"])[:, bidx]; a, b = mu * kap, (1 - mu) * kap
        p0 = np.exp(gammaln(b + n) + gammaln(a + b) - gammaln(b) - gammaln(a + b + n))
        p1 = np.exp(gammaln(a + n) + gammaln(a + b) - gammaln(a) - gammaln(a + b + n))
        w = np.clip(1 - p0 - p1, 1e-12, 1.0)
        out.update(p0=p0, p1=p1, mu_i=np.clip((mu - p1) / w, MU_EPS, 1 - MU_EPS))
    return out


def rq(pr, P):
    """Residual quantities for lib/ppc_checks.stats: predictive mean and variance per row, expected mass at
    scores <= EPS and >= 1 - EPS (hurdle mass plus the interior Beta's mass beyond the clip), mean capability."""
    w = np.clip(1 - pr["p0"] - pr["p1"], 1e-12, 1.0); mi, kap = pr["mu_i"], pr["kap"]
    mean = pr["p1"] + w * mi
    ey2 = pr["p1"] + w * (mi * (1 - mi) / (kap + 1) + mi ** 2)
    a, b = mi * kap, (1 - mi) * kap
    return dict(mubar=mean.mean(0), v=(ey2 - mean ** 2).mean(0) + mean.var(0), chat=P["capability"].mean(0),
                p0=(pr["p0"] + w * betainc(a, b, EPS)).mean(0), p1=(pr["p1"] + w * (1 - betainc(a, b, 1 - EPS))).mean(0))


def simulate(pr, rng):
    """One model-true score per row and draw (same shape as pr["mu"]): 0 or 1 with the boundary masses, else Beta."""
    u = rng.uniform(size=pr["mu"].shape); mi, kap = pr["mu_i"], pr["kap"]
    y = rng.beta(mi * kap, (1 - mi) * kap)
    return np.where(u < pr["p0"], 0.0, np.where(u > 1 - pr["p1"], 1.0, y))


def bound_mass(pr):
    """Per-draw probability of a score <= EPS and of a score >= 1 - EPS (for mass-scale comparison of boundary rows)."""
    w = np.clip(1 - pr["p0"] - pr["p1"], 1e-12, 1.0); a, b = pr["mu_i"] * pr["kap"], (1 - pr["mu_i"]) * pr["kap"]
    return pr["p0"] + w * betainc(a, b, EPS), pr["p1"] + w * (1 - betainc(a, b, 1 - EPS))


def var_names(feats):
    return ["capability", "difficulty", "slope", "sigma"] + sum((FREE[f] for f in feats), [])


def has_bnd(feats):
    return bool(set(feats) & BND)


def install():
    for k in FREE:
        models.EXTRA_FREE[k] = FREE[k]; models.EXTRA_DIAG[k] = DIAG[k]
    models.build_model = build
