"""P8-P10 model variants of the grid (M10): Epoch's builder is swapped in memory for ours; nothing under ext/ is edited."""
from contextlib import contextmanager
import numpy as np, pymc as pm
import pytensor.tensor as pt
from pymc.distributions.transforms import ZeroSumTransform
from . import models as M


def build(variant, df, s0=None, noncentred=False, eps=1e-3):
    names_m, names_b, midx, bidx = M._index(df)
    K = len(names_b); zsc = np.sqrt(K / (K - 1))
    y = np.clip(df["performance"].to_numpy(dtype=float), eps, 1 - eps)
    pri = M.DEFAULT_PRIORS
    with pm.Model(coords={"model": names_m, "benchmark": names_b}) as model:
        tau_alpha = pm.LogNormal("tau_alpha", mu=pri["tau_alpha"][0], sigma=pri["tau_alpha"][1])
        if variant == "P10":
            sigma = pm.Truncated("sigma", pm.LogNormal.dist(mu=float(np.log(0.1)), sigma=0.75), lower=0.0, upper=M.MAX_SIGMA, dims="benchmark")
        else:
            sigma_median = pm.LogNormal("sigma_median", mu=pri["sigma_median"][0], sigma=pri["sigma_median"][1])
            tau_sigma = pm.LogNormal("tau_sigma", mu=pri["tau_sigma"][0], sigma=pri["tau_sigma"][1])
            sigma = pm.Truncated("sigma", pm.LogNormal.dist(mu=pm.math.log(sigma_median), sigma=tau_sigma), lower=0.0, upper=M.MAX_SIGMA, dims="benchmark")
        kappa = pm.Deterministic("kappa", 1.0 / (4.0 * sigma ** 2) - 1.0, dims="benchmark")
        flat_d = True
        if variant == "P8":
            sc = 3.0 if (s0 is None or s0 <= 3.0) else 2.0 * s0
            capability = pm.Normal("capability", 0.0, sc, dims="model")
            difficulty = pm.ZeroSumNormal("difficulty", sigma=sc, dims="benchmark"); flat_d = False
        elif variant == "P9":
            mu_c = pm.Normal("mu_c", 0.0, 5.0); s_c = pm.HalfNormal("s_c", 3.0)
            if noncentred:
                cz = pm.Normal("cap_z", 0.0, 1.0, dims="model"); capability = pm.Deterministic("capability", mu_c + s_c * cz, dims="model")
            else:
                capability = pm.Normal("capability", mu_c, s_c, dims="model")
        else:
            capability = pm.Uniform("capability", -M.CD_BOUND, M.CD_BOUND, dims="model")
        if flat_d:
            difficulty = pm.Flat("difficulty", dims="benchmark", transform=ZeroSumTransform([-1]))
            pm.Potential("difficulty_bound", pm.math.switch(pm.math.all(pm.math.abs(difficulty) <= M.CD_BOUND), 0.0, -np.inf))
        log_slope = pm.ZeroSumNormal("log_slope", sigma=tau_alpha * zsc, dims="benchmark")
        slope = pm.Deterministic("slope", pm.math.exp(log_slope), dims="benchmark")
        mu = pm.math.clip(pm.math.sigmoid(slope[bidx] * (capability[midx] - difficulty[bidx])), M.MU_EPS, 1 - M.MU_EPS)
        pm.Beta("obs", alpha=mu * kappa[bidx], beta=(1 - mu) * kappa[bidx], observed=y)
    return model


FREE = {"P8": M.BASE_FREE, "P9": M.BASE_FREE + ["mu_c", "s_c"], "P10": ["tau_alpha", "sigma", "capability", "difficulty", "log_slope"]}
FREE_NC = {"P9": ["tau_alpha", "sigma_median", "tau_sigma", "sigma", "cap_z", "mu_c", "s_c", "difficulty", "log_slope"]}
DIAG = {"P8": M.BASE_DIAG, "P9": M.BASE_DIAG + ["mu_c", "s_c"], "P10": ["capability", "difficulty", "slope", "sigma", "tau_alpha"]}


@contextmanager
def epoch_with_variant(variant, s0=None, noncentred=False):
    import eci.bayesian as eb
    saved = (eb.build_bayesian_model, eb._FREE_VARS, eb._DIAGNOSTIC_VARS)
    eb.build_bayesian_model = lambda df, p=None, performance_clip_eps=1e-3: build(variant, df, s0, noncentred, performance_clip_eps)
    free = FREE_NC["P9"] if (variant == "P9" and noncentred) else FREE[variant]
    eb._FREE_VARS = tuple(free); eb._DIAGNOSTIC_VARS = list(DIAG[variant])
    try: yield eb
    finally: eb.build_bayesian_model, eb._FREE_VARS, eb._DIAGNOSTIC_VARS = saved
