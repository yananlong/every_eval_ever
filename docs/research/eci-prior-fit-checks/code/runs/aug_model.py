"""Augmented-input model (exploratory, beyond plan): Epoch's base model with Epoch's priors, plus
  - a cell effect u[c] = tau_u * zc[c], zc ~ N(0, 1), tau_u ~ HalfNormal(0.5), shared by every observation of a
    (model, benchmark) cell, on the logit scale inside the S-curve. The Beta noise then describes how sources
    disagree within a cell, and u the part of a cell's deviation every source sees.
  - a source-class offset beta_src[k] ~ N(0, 0.5) on the logit scale for EEE rows (k = independent,
    upstream-unknown); Epoch's rows are the reference.
Feature name "cell". With no feature the builder is the frozen models.build_model (Epoch's base). The frozen
runs/lib/models.py is not edited: install() swaps the builder in memory, as runs/w6x_family.py does."""
import numpy as np
import pymc as pm
from pymc.distributions.transforms import ZeroSumTransform
from lib import models
from lib.models import MU_EPS, MAX_SIGMA, CD_BOUND, DEFAULT_PRIORS, _index

_frozen = models.build_model


def build_model_aug(df, spec=models.Spec(), priors=None, eps=1e-3, ex=None):
    if "cell" not in spec.features:
        return _frozen(df, spec, priors, eps, ex)
    assert set(spec.features) == {"cell"} and spec.prior == "epoch"
    priors = priors or DEFAULT_PRIORS
    model_names, bench_names, midx, bidx = _index(df)
    K = len(bench_names)
    y = np.clip(df["performance"].to_numpy(dtype=float), eps, 1.0 - eps)
    cell = ex["cell"]; n_cell = int(cell.max()) + 1; cls = ex["obs_class"]
    with pm.Model(coords={"model": model_names, "benchmark": bench_names, "src_class": ["independent", "upstream-unknown"]}) as model:
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
        tau_u = pm.HalfNormal("tau_u", 0.5)
        zc = pm.Normal("zc", 0.0, 1.0, shape=n_cell)
        beta = pm.Normal("beta_src", 0.0, 0.5, dims="src_class")
        b_row = pm.math.concatenate([np.zeros(1), beta])[cls]
        eta = slope[bidx] * (capability[midx] - difficulty[bidx]) + tau_u * zc[cell] + b_row
        mu = pm.math.clip(pm.math.sigmoid(eta), MU_EPS, 1.0 - MU_EPS)
        kappa_obs = (1.0 / (4.0 * sigma ** 2) - 1.0)[bidx]
        pm.Beta("obs", alpha=mu * kappa_obs, beta=(1.0 - mu) * kappa_obs, observed=y)
    return model


def install():
    models.EXTRA_FREE["cell"] = ["zc", "tau_u", "beta_src"]
    models.EXTRA_DIAG["cell"] = ["tau_u", "beta_src", "zc"]
    models.build_model = build_model_aug
