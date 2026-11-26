"""W7 (exploratory, beyond plan; deviations entry 15): a combined expansion aimed at the misfits C2 found.

Features (any subset; none = Epoch's base model exactly):
  dev   developer-by-benchmark offsets on the logit, as F2 (aims at T5).
  hetero per-model noise, as F5.
  fam   benchmark-family offsets per model on capability, as runs/w6x_family.py (aims at the T2 clusters);
        ex["fam_variant"] in {"lin", "tag", "both"}.
  f1r   a second capability dimension with loadings that sum to zero over benchmarks (aims at diffuse T2):
        capability row + tau_l * xi[b] * z[m], z ~ N(0, 1), xi ~ ZeroSumNormal(1), tau_l ~ HalfNormal(0.5).
        F1's loadings were free, so adding c to every loading and -c z to capability left the likelihood
        unchanged; the zero-sum constraint removes that direction, and capability stays the general capability.
        The sign of (z, xi) is not identified; its diagnostics use the sign-free tau_l and |loading|.
  skew  a per-benchmark asymmetric curve (aims at T1): mu = sigmoid(eta) ** exp(g[b]), g = tau_g * w,
        w ~ N(0, 1), tau_g ~ HalfNormal(0.5); g = 0 is Epoch's logistic.
  cell  augmented input only: a cell effect tau_u * zc on the logit for cells with more than one observation;
        for single-observation cells the Beta variance is widened by the cell effect's variance, matched in
        moments (prob-scale variance of u approximated by (mu (1 - mu) tau_u)^2), so both kinds of cell
        carry the same two variance components. ex["multi_idx"] (-1 = single), ex["n_multi"].
`mu_kappa(feats, P, df, ex)` mirrors the builder in numpy for the checks. The frozen runs/lib is not edited:
`install()` swaps the builder and registers the variable lists in memory."""
import numpy as np
import pymc as pm
import pytensor.tensor as pt
from pymc.distributions.transforms import ZeroSumTransform
from lib import models
import w6x_family as fx
from lib.models import MU_EPS, MAX_SIGMA, CD_BOUND, DEFAULT_PRIORS, _index

FREE = {"dev": ["zeta", "tau_delta"], "hetero": ["phi", "tau_omega"], "fam": ["w_fam", "tau_fam"],
        "f1r": ["z2", "xi2", "tau_l"], "skew": ["w_skew", "tau_g"], "cell": ["zc", "tau_u"]}
DIAG = {"dev": ["zeta", "tau_delta"], "hetero": ["phi", "tau_omega"], "fam": ["w_fam", "tau_fam"],
        "f1r": ["tau_l", "loading_abs"], "skew": ["w_skew", "tau_g"], "cell": ["tau_u", "zc"]}
_frozen = models.build_model


def build(df, spec=models.Spec(), priors=None, eps=1e-3, ex=None):
    f = set(spec.features)
    assert spec.prior == "epoch" and f <= set(FREE), spec
    priors = priors or DEFAULT_PRIORS
    model_names, bench_names, midx, bidx = _index(df)
    K = len(bench_names)
    y = np.clip(df["performance"].to_numpy(dtype=float), eps, 1.0 - eps)
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
            A, gnames = fx.families(bench_names, ex["fam_variant"])
            model.add_coord("family", gnames)
            tau_f = pm.HalfNormal("tau_fam", 0.5, dims="family")
            w = pm.Normal("w_fam", 0.0, 1.0, dims=("model", "family"))
            cap_row = cap_row + (w[midx] * (A[bidx] * tau_f[None, :])).sum(axis=1)
        if "f1r" in f:
            tau_l = pm.HalfNormal("tau_l", 0.5)
            z2 = pm.Normal("z2", 0.0, 1.0, dims="model")
            xi2 = pm.ZeroSumNormal("xi2", sigma=1.0, dims="benchmark")
            pm.Deterministic("loading_abs", tau_l * pt.abs(xi2), dims="benchmark")
            cap_row = cap_row + tau_l * xi2[bidx] * z2[midx]
        eta = slope[bidx] * (cap_row - difficulty[bidx])
        if "dev" in f:
            tau_d = pm.HalfNormal("tau_delta", 0.5)
            zeta = pm.Normal("zeta", 0.0, 1.0, shape=ex["n_cells"])
            delta = pt.concatenate([tau_d * zeta, pt.zeros(1)])
            ci = np.where(ex["cell_idx"] < 0, ex["n_cells"], ex["cell_idx"])
            eta = eta + delta[ci]
        if "cell" in f:
            tau_u = pm.HalfNormal("tau_u", 0.5)
            zc = pm.Normal("zc", 0.0, 1.0, shape=ex["n_multi"])
            mi_ = ex["multi_idx"]; has = mi_ >= 0
            u = pt.concatenate([tau_u * zc, pt.zeros(1)])[np.where(has, mi_, ex["n_multi"])]
            eta = eta + u
        if "skew" in f:
            tau_g = pm.HalfNormal("tau_g", 0.5)
            wsk = pm.Normal("w_skew", 0.0, 1.0, dims="benchmark")
            g = tau_g * wsk
            mu = pt.exp(pt.exp(g[bidx]) * pt.log(pm.math.sigmoid(eta)))
        else:
            mu = pm.math.sigmoid(eta)
        mu = pm.math.clip(mu, MU_EPS, 1.0 - MU_EPS)
        if "hetero" in f:
            tau_o = pm.HalfNormal("tau_omega", 0.5)
            phi = pm.Normal("phi", 0.0, 1.0, dims="model")
            s_row = 0.5 * pm.math.sigmoid(pm.math.logit(2.0 * sigma[bidx]) + tau_o * phi[midx])
            kappa_obs = 1.0 / (4.0 * s_row ** 2) - 1.0
        else:
            kappa_obs = (1.0 / (4.0 * sigma ** 2) - 1.0)[bidx]
        if "cell" in f:   # single-observation cells: add the cell-effect variance to the Beta variance
            v_w = mu * (1.0 - mu) / (kappa_obs + 1.0)
            v_t = v_w + pt.where(has, 0.0, (mu * (1.0 - mu) * tau_u) ** 2)
            kappa_obs = pt.maximum(mu * (1.0 - mu) / v_t - 1.0, 1e-3)
        pm.Beta("obs", alpha=mu * kappa_obs, beta=(1.0 - mu) * kappa_obs, observed=y)
    return model


def mu_kappa(feats, P, df, ex):
    """P: posterior arrays with a leading draw axis. Returns mu (S, N) and kappa_obs (S, N), as the builder."""
    f = set(feats)
    _, bench_names, midx, bidx = _index(df)
    cap = P["capability"][:, midx]
    if "fam" in f:
        A, _ = fx.families(bench_names, ex["fam_variant"])
        cap = cap + (P["w_fam"][:, midx, :] * (A[bidx][None] * P["tau_fam"][:, None, :])).sum(-1)
    if "f1r" in f:
        cap = cap + P["tau_l"][:, None] * P["xi2"][:, bidx] * P["z2"][:, midx]
    eta = P["slope"][:, bidx] * (cap - P["difficulty"][:, bidx])
    if "dev" in f:
        delta = np.concatenate([P["tau_delta"][:, None] * P["zeta"], np.zeros((P["zeta"].shape[0], 1))], axis=1)
        eta = eta + delta[:, np.where(ex["cell_idx"] < 0, ex["n_cells"], ex["cell_idx"])]
    if "cell" in f:
        mi_ = ex["multi_idx"]; has = mi_ >= 0
        u = np.concatenate([P["tau_u"][:, None] * P["zc"], np.zeros((P["zc"].shape[0], 1))], axis=1)
        eta = eta + u[:, np.where(has, mi_, ex["n_multi"])]
    ls = -np.logaddexp(0.0, -np.clip(eta, -700, 700))   # log sigmoid
    if "skew" in f:
        ls = np.exp(P["tau_g"][:, None] * P["w_skew"])[:, bidx] * ls
    mu = np.clip(np.exp(ls), MU_EPS, 1 - MU_EPS)
    if "hetero" in f:
        lg = np.log(2 * P["sigma"][:, bidx]) - np.log1p(-2 * P["sigma"][:, bidx])
        s_row = 0.5 / (1 + np.exp(-(lg + P["tau_omega"][:, None] * P["phi"][:, midx])))
        kap = 1 / (4 * s_row ** 2) - 1
    else:
        kap = (1 / (4 * P["sigma"] ** 2) - 1)[:, bidx]
    if "cell" in f:
        v = mu * (1 - mu) / (kap + 1) + np.where(has, 0.0, (mu * (1 - mu) * P["tau_u"][:, None]) ** 2)
        kap = np.maximum(mu * (1 - mu) / v - 1, 1e-3)
    return mu, kap


POST_VARS = {"dev": ["zeta", "tau_delta"], "hetero": ["phi", "tau_omega"], "fam": ["w_fam", "tau_fam"],
             "f1r": ["z2", "xi2", "tau_l"], "skew": ["w_skew", "tau_g"], "cell": ["zc", "tau_u"]}


def install():
    for k in FREE:
        models.EXTRA_FREE[k] = FREE[k]; models.EXTRA_DIAG[k] = DIAG[k]
    models.build_model = build
