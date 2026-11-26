"""W6 exploratory addition (not one of the registered F1-F7): benchmark-family effects on capability.

Each model m gets, for each benchmark family g, an offset u[m, g] = tau[g] * w[m, g] with w ~ N(0, 1) and
tau[g] ~ HalfNormal(0.5). A row of model m on benchmark b uses capability[m] + sum over the families g of b of
u[m, g], inside Epoch's slope * (capability - difficulty). ECI stays the general capability. With no family
it is F0 exactly.

Families are fixed from metadata before any fit, never from the residuals:
  - "tag": Epoch's own benchmark tags (column epoch_tags of runs/TAX/combined_eci_map.csv, copied from Epoch's
    benchmark hub); a benchmark with several tags belongs to each; untagged benchmarks have none; a tag on
    a single benchmark (Writing & creativity) is dropped, since it would only duplicate the noise term.
  - "lin": versions or tiers Epoch publishes of one benchmark (a shared name stem): FrontierMath (all four),
    ARC-AGI with ARC-AGI-2, WeirdML with WeirdML v3, CL-bench with CL-bench Life, OSWorld with OSWorld 2.0.

The frozen runs/lib/models.py is not edited: `install()` puts `build_model_x`, a copy of its builder plus the
family block, in place of `models.build_model` in memory, and registers the feature "fam" in its variable lists.
"""
import csv
from pathlib import Path
import numpy as np
import pymc as pm
import pytensor.tensor as pt
from pymc.distributions.transforms import ZeroSumTransform
from lib import models
from lib.models import MU_EPS, MAX_SIGMA, CD_BOUND, DEFAULT_PRIORS, _index

TAX = Path(__file__).resolve().parent / "TAX" / "combined_eci_map.csv"
LINEAGE = {
    "FrontierMath": lambda b: b.startswith("FrontierMath"),
    "ARC-AGI": lambda b: b in ("ARC-AGI", "ARC-AGI-2"),
    "WeirdML": lambda b: b in ("WeirdML", "WeirdML v3"),
    "CL-bench": lambda b: b in ("CL-bench", "CL-bench Life"),
    "OSWorld": lambda b: b in ("OSWorld", "OSWorld 2.0"),
}


def families(bench_names, variant):
    """Membership matrix A (K benchmarks x G families) and the family names, for variant "tag", "lin" or "both"."""
    groups = {}
    if variant in ("tag", "both"):
        tags = {r["benchmark"]: [t for t in r["epoch_tags"].split(";") if t] for r in csv.DictReader(open(TAX))}
        missing = [b for b in bench_names if b not in tags]
        assert not missing, f"benchmarks missing from the taxonomy map: {missing}"
        for b in bench_names:
            for t in tags[b]:
                groups.setdefault("tag:" + t, set()).add(b)
    if variant in ("lin", "both"):
        for g, f in LINEAGE.items():
            mem = {b for b in bench_names if f(b)}
            if len(mem) >= 2: groups["lin:" + g] = mem
    names = sorted(g for g in groups if len(groups[g]) >= 2)   # a one-benchmark family only duplicates the noise term
    A = np.array([[b in groups[g] for g in names] for b in bench_names], dtype=float)
    return A, names


def build_model_x(df, spec=models.Spec(), priors=None, eps=1e-3, ex=None):
    """models.build_model (frozen) copied unchanged, plus the "fam" block on the capability row."""
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
        else:
            s_scale = pm.LogNormal("s_scale", mu=float(np.log(2.0)), sigma=0.5)
            mu_c = pm.Normal("mu_c", 0.0, 2.0)
            capability = pm.Normal("capability", mu=mu_c, sigma=s_scale, dims="model")
            difficulty = pm.ZeroSumNormal("difficulty", sigma=s_scale * zsc, dims="benchmark")
        log_slope = pm.ZeroSumNormal("log_slope", sigma=tau_alpha * zsc, dims="benchmark")
        slope = pm.Deterministic("slope", pm.math.exp(log_slope), dims="benchmark")

        cap_row = capability[midx]
        if "fam" in feats:
            A, gnames = families(bench_names, ex["fam_variant"])
            model.add_coord("family", gnames)
            tau_f = pm.HalfNormal("tau_fam", 0.5, dims="family")
            w = pm.Normal("w_fam", 0.0, 1.0, dims=("model", "family"))
            cap_row = cap_row + (w[midx] * (A[bidx] * tau_f[None, :])).sum(axis=1)
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


def install():
    models.EXTRA_FREE["fam"] = ["w_fam", "tau_fam"]
    models.EXTRA_DIAG["fam"] = ["w_fam", "tau_fam"]
    models.build_model = build_model_x
