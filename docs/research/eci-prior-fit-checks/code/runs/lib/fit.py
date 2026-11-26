"""Fitting wrappers: Epoch's fit_bayesian_eci (unmodified) or the same function with one of our models swapped in
(models.epoch_with), the sidecar/skip logic of M10, and the PSIS-LOO helpers."""
import hashlib, json, os, time, warnings
from pathlib import Path
import numpy as np, pandas as pd
import arviz as az, pymc as pm, xarray as xr
from scipy.stats import lognorm
from . import data, models

RUNS = Path(__file__).resolve().parents[1]
CODE_FILES = [RUNS / "vendor/eci-public/src/eci/bayesian.py", RUNS / "vendor/eci-public/src/eci/evaluation.py",
              RUNS / "lib/models.py", RUNS / "lib/fit.py"]


def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha_file(p): return sha_bytes(Path(p).read_bytes())
def code_digest(extra=()):
    return sha_bytes("".join(sha_file(p) for p in list(CODE_FILES) + list(extra)).encode())
def input_digest(df): return sha_bytes(df.to_csv(index=False).encode())


def log_prior_hyper(trace, priors=models.DEFAULT_PRIORS):
    """Summed log density of the three hyperpriors per draw (group log_prior, M3 S5)."""
    tot = 0
    for name in ("tau_alpha", "sigma_median", "tau_sigma"):
        mu, s = priors[name]
        x = trace.posterior[name]
        tot = tot + (-np.log(x) - np.log(s) - 0.5 * np.log(2 * np.pi) - 0.5 * ((np.log(x) - mu) / s) ** 2)
    return tot.rename("hyperprior_logp").to_dataset()


def add_groups(trace, eci_draws, model_names):
    n_chain, n_draw = trace.posterior.sizes["chain"], trace.posterior.sizes["draw"]
    arr = np.asarray(eci_draws).reshape(n_chain, n_draw, -1)
    post = trace["posterior"].to_dataset().assign(
        eci=(("chain", "draw", "model"), arr))
    trace["posterior"] = xr.DataTree(dataset=post)
    trace["log_prior"] = xr.DataTree(dataset=log_prior_hyper(trace))
    return trace


def verdict(attempts):
    a = attempts[-1]
    return bool(a["divergences"] == 0 and a["max_rhat"] <= 1.01 and a["min_ess"] >= 400), a


def tail_bfmi(trace):
    out = {}
    try:
        t = az.ess(trace, var_names=models.BASE_DIAG, method="tail")
        out["min_tail_ess"] = min(float(np.nanmin(v.to_numpy())) for v in t.data_vars.values())
    except Exception as e: out["min_tail_ess"] = f"n/a: {type(e).__name__}"
    try:
        b = az.bfmi(trace); out["min_bfmi"] = float(np.min(np.asarray(b)))
    except Exception as e: out["min_bfmi"] = f"n/a: {type(e).__name__}"
    return out


def loo(trace):
    """PSIS-LOO over the 'obs' log-likelihood: dict with elpd, se, p_loo, per-row elpd and Pareto k."""
    r = az.loo(trace, pointwise=True, var_name="obs")
    return r


def loo_arrays(r):
    elpd_i = np.asarray(getattr(r, "elpd_i", None) if hasattr(r, "elpd_i") else r.pointwise["elpd"] if hasattr(r, "pointwise") else None)
    k = np.asarray(r.pareto_k)
    return elpd_i.ravel(), k.ravel()


def fit(name, outdir, df, spec=None, seed=12345, draws=None, evaluate=False, ex=None, loglik=False, force=False, extra_code=(), priors=None):
    """Fit and save <name>.nc plus <name>.json atomically; skip if the sidecar matches. spec=None runs Epoch's
    unmodified builder (their prior object `priors` unused); otherwise our model through Epoch's fit function."""
    import eci.bayesian as eb
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    nc, js = outdir / f"{name}.nc", outdir / f"{name}.json"
    args = dict(seed=seed, draws=draws, evaluate=evaluate, spec=None if spec is None else [list(spec.features), spec.prior],
                priors=None if priors is None else {k: list(v) for k, v in priors.items()}, chains=4, target_accept=0.95, clip=1e-3)
    want = dict(input_sha256=input_digest(df), code_sha256=code_digest(extra_code), args=args)
    if js.exists() and nc.exists() and not force:
        old = json.loads(js.read_text())
        if all(old.get(k) == v for k, v in want.items()):
            return old, None
    t0 = time.time()
    with warnings.catch_warnings(record=True) as wl:
        warnings.simplefilter("always")
        if spec is None:
            eci_df, edi_df, d = eb.fit_bayesian_eci(df, random_seed=seed, draws=draws, evaluate=evaluate, progressbar=False)
        else:
            with models.epoch_with(spec, ex, priors) as _:
                eci_df, edi_df, d = eb.fit_bayesian_eci(df, random_seed=seed, draws=draws, evaluate=False, progressbar=False)
            if loglik:
                m = models.build_model(df, spec, priors, 1e-3, ex)
                with m:
                    pm.compute_log_likelihood(d["trace"], extend_inferencedata=True, progressbar=False)
    wall = time.time() - t0
    trace = add_groups(d["trace"], d["eci"], d["model_names"])
    ok, last = verdict(d["attempts"])
    side = dict(want, name=name, started_from=d["started_from"], attempts=d["attempts"], converged=ok, last_attempt=last,
                warnings=[str(w.message)[:300] for w in wl], wall_seconds=round(wall, 1), **tail_bfmi(trace))
    tmp_nc, tmp_js = outdir / f".{name}.nc.tmp", outdir / f".{name}.json.tmp"
    if "evaluation" in d:
        import pickle
        pickle.dump(d["evaluation"], open(outdir / f"{name}_evaluation.pkl", "wb"))
    trace.to_netcdf(tmp_nc)
    tmp_js.write_text(json.dumps(side, indent=1, default=str))
    os.replace(tmp_nc, nc); os.replace(tmp_js, js)
    return side, (eci_df, edi_df, d)


def load_eci(nc):
    """(draws array (n, models), model names) from a saved trace, chain-major as fit_bayesian_eci returns them."""
    t = xr.open_datatree(nc)
    e = t["posterior"].to_dataset()["eci"]
    names = [str(x) for x in e["model"].values]
    return e.stack(s=("chain", "draw")).transpose("s", "model").to_numpy(), names, t
