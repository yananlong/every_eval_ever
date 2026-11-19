"""Our PyMC implementations of the base model F0, the reference prior PR and the expansions F1-F5 (and F7 by
combining features), as specified in M11, M12 and M14 of the plan. Written without importing Epoch's builder.

A model is described by `Spec(features, prior)`; features is a subset of
{"2d", "dev", "asym", "drift", "hetero"} and prior is "epoch" or "reference".
`fitted(spec, df, ex, ...)` runs Epoch's own `fit_bayesian_eci` (pilot, then dense mass matrix) with this
builder swapped in memory; nothing under ext/ or the vendored copy is edited.
"""
from contextlib import contextmanager
from dataclasses import dataclass
import numpy as np
import pymc as pm
import pytensor.tensor as pt
from pymc.distributions.transforms import ZeroSumTransform

MU_EPS = 1e-6
MAX_SIGMA = 0.5
CD_BOUND = 50.0
BASE_FREE = ["tau_alpha", "sigma_median", "tau_sigma", "sigma", "capability", "difficulty", "log_slope"]
BASE_DIAG = ["capability", "difficulty", "slope", "sigma", "tau_alpha", "sigma_median", "tau_sigma"]
FEATURES = ("2d", "dev", "asym", "drift", "hetero")
EXTRA_FREE = {"2d": ["z", "xi_ref", "xi_rest", "tau_lambda"], "dev": ["zeta", "tau_delta"], "asym": ["eps"],
              "drift": ["gamma"], "hetero": ["phi", "tau_omega"]}
EXTRA_DIAG = {"2d": ["z", "xi_ref", "xi_rest", "tau_lambda"], "dev": ["zeta", "tau_delta"], "asym": ["eps"],
              "drift": ["gamma"], "hetero": ["phi", "tau_omega"]}
PR_FREE = ["s_scale", "mu_c"]
DEFAULT_PRIORS = dict(tau_alpha=(float(np.log(0.5)), 0.5), sigma_median=(float(np.log(0.1)), 0.5),
                      tau_sigma=(float(np.log(0.5)), 0.5))


@dataclass(frozen=True)
class Spec:
    features: tuple = ()
    prior: str = "epoch"

    def free_vars(self):
        v = list(BASE_FREE) + (PR_FREE if self.prior == "reference" else [])
        for f in self.features:
            v += EXTRA_FREE[f]
        return tuple(v)

    def diag_vars(self):
        v = list(BASE_DIAG) + (PR_FREE if self.prior == "reference" else [])
        for f in self.features:
            v += EXTRA_DIAG[f]
        return v


def _index(df):
    mids, bids = df["model_id"].unique(), df["benchmark_id"].unique()
    mi = {m: i for i, m in enumerate(mids)}; bi = {b: i for i, b in enumerate(bids)}
    nm = df.drop_duplicates("model_id").set_index("model_id")["Model"]
    nb = df.drop_duplicates("benchmark_id").set_index("benchmark_id")["benchmark"]
    return ([nm[m] for m in mids], [nb[b] for b in bids],
            np.array([mi[m] for m in df["model_id"]]), np.array([bi[b] for b in df["benchmark_id"]]))


def build_model(df, spec=Spec(), priors=None, eps=1e-3, ex=None):
    """The PyMC model. For Spec() it has the same free variables, transforms, bounds and likelihood as Epoch's."""
    priors = priors or DEFAULT_PRIORS
    model_names, bench_names, midx, bidx = _index(df)
    K = len(bench_names)
    y = np.clip(df["performance"].to_numpy(dtype=float), eps, 1.0 - eps)
    coords = {"model": model_names, "benchmark": bench_names}
    feats = set(spec.features)
    with pm.Model(coords=coords) as model:
        tau_alpha = pm.LogNormal("tau_alpha", mu=priors["tau_alpha"][0], sigma=priors["tau_alpha"][1])
        sigma_median = pm.LogNormal("sigma_median", mu=priors["sigma_median"][0], sigma=priors["sigma_median"][1])
        tau_sigma = pm.LogNormal("tau_sigma", mu=priors["tau_sigma"][0], sigma=priors["tau_sigma"][1])
        sigma = pm.Truncated("sigma", pm.LogNormal.dist(mu=pm.math.log(sigma_median), sigma=tau_sigma),
                             lower=0.0, upper=MAX_SIGMA, dims="benchmark")
        kappa = pm.Deterministic("kappa", 1.0 / (4.0 * sigma ** 2) - 1.0, dims="benchmark")
        zsc = np.sqrt(K / (K - 1))
        if spec.prior == "epoch":
            capability = pm.Uniform("capability", -CD_BOUND, CD_BOUND, dims="model")
            difficulty = pm.Flat("difficulty", dims="benchmark", transform=ZeroSumTransform([-1]))
            pm.Potential("difficulty_bound", pm.math.switch(pm.math.all(pm.math.abs(difficulty) <= CD_BOUND), 0.0, -np.inf))
        else:  # PR, M11
            s_scale = pm.LogNormal("s_scale", mu=float(np.log(2.0)), sigma=0.5)
            mu_c = pm.Normal("mu_c", 0.0, 2.0)
            capability = pm.Normal("capability", mu=mu_c, sigma=s_scale, dims="model")
            difficulty = pm.ZeroSumNormal("difficulty", sigma=s_scale * zsc, dims="benchmark")
        log_slope = pm.ZeroSumNormal("log_slope", sigma=tau_alpha * zsc, dims="benchmark")
        slope = pm.Deterministic("slope", pm.math.exp(log_slope), dims="benchmark")

        cap_row = capability[midx]
        if "2d" in feats:
            tau_l = pm.HalfNormal("tau_lambda", 1.0)
            z = pm.Normal("z", 0.0, 1.0, dims="model")
            ref = ex["ref_bench"]
            xi_ref = pm.HalfNormal("xi_ref", 1.0)
            xi_rest = pm.Normal("xi_rest", 0.0, 1.0, shape=K - 1)
            rest_pos = np.array([b for b in range(K) if b != ref]); inv = np.zeros(K, dtype=int)
            inv[ref] = 0; inv[rest_pos] = 1 + np.arange(K - 1)
            xi = pt.concatenate([xi_ref[None], xi_rest])[inv]
            loading = pm.Deterministic("loading", tau_l * xi, dims="benchmark")
            cap_row = cap_row + loading[bidx] * z[midx]
        eta = slope[bidx] * (cap_row - difficulty[bidx])
        if "dev" in feats:
            tau_d = pm.HalfNormal("tau_delta", 0.5)
            zeta = pm.Normal("zeta", 0.0, 1.0, shape=ex["n_cells"])
            delta = pt.concatenate([tau_d * zeta, pt.zeros(1)])
            ci = np.where(ex["cell_idx"] < 0, ex["n_cells"], ex["cell_idx"])
            eta = eta + delta[ci]
        if "drift" in feats:
            gamma = pm.Normal("gamma", 0.0, 0.5)
            eta = eta + gamma * ex["gap"]
        mu = pm.math.sigmoid(eta)
        if "asym" in feats:
            e = pm.Beta("eps", 1.0, 9.0, dims="benchmark")
            mu = (1.0 - e[bidx]) * mu
        mu = pm.math.clip(mu, MU_EPS, 1.0 - MU_EPS)
        if "hetero" in feats:
            tau_o = pm.HalfNormal("tau_omega", 0.5)
            phi = pm.Normal("phi", 0.0, 1.0, dims="model")
            s_row = 0.5 * pm.math.sigmoid(pm.math.logit(2.0 * sigma[bidx]) + tau_o * phi[midx])
            kappa_obs = 1.0 / (4.0 * s_row ** 2) - 1.0
        else:
            kappa_obs = kappa[bidx]
        pm.Beta("obs", alpha=mu * kappa_obs, beta=(1.0 - mu) * kappa_obs, observed=y)
    return model


@contextmanager
def epoch_with(spec, ex=None, priors=None):
    """Swap Epoch's builder and variable lists in memory so `fit_bayesian_eci` fits our model unchanged."""
    import eci.bayesian as eb
    saved = (eb.build_bayesian_model, eb._FREE_VARS, eb._DIAGNOSTIC_VARS)
    eb.build_bayesian_model = lambda df, p=None, performance_clip_eps=1e-3: build_model(df, spec, priors, performance_clip_eps, ex)
    eb._FREE_VARS = spec.free_vars(); eb._DIAGNOSTIC_VARS = spec.diag_vars()
    try:
        yield eb
    finally:
        eb.build_bayesian_model, eb._FREE_VARS, eb._DIAGNOSTIC_VARS = saved
