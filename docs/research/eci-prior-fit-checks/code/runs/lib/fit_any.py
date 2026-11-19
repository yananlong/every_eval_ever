"""Fits for W3 and later: Epoch's unmodified fit_bayesian_eci with optional Epoch priors, or one of our models swapped in.
Returns thinned draws instead of full traces where only 400 draws are kept."""
import json, os, time, warnings
from pathlib import Path
import numpy as np
import eci.bayesian as eb
from . import models, fit as fitmod

KEEP = ["capability", "difficulty", "slope", "sigma", "tau_alpha", "sigma_median", "tau_sigma", "log_slope"]


def run(df, seed, spec=None, ex=None, epoch_priors=None, draws=None, priors=None, target_accept=0.95, variant=None, s0=None, noncentred=False):
    """Returns (eci_draws (n, M) chain-major, names, trace, attempts, started_from, warnings, wall)."""
    t0 = time.time()
    with warnings.catch_warnings(record=True) as wl:
        warnings.simplefilter("always")
        if variant is not None:
            from . import variants
            with variants.epoch_with_variant(variant, s0, noncentred):
                eci_df, edi_df, d = eb.fit_bayesian_eci(df, random_seed=seed, draws=draws, evaluate=False, progressbar=False, target_accept=target_accept)
        elif spec is None:
            kw = {} if epoch_priors is None else dict(priors=eb.BayesianPriors(**epoch_priors))
            eci_df, edi_df, d = eb.fit_bayesian_eci(df, random_seed=seed, draws=draws, evaluate=False, progressbar=False, target_accept=target_accept, **kw)
        else:
            with models.epoch_with(spec, ex, priors):
                eci_df, edi_df, d = eb.fit_bayesian_eci(df, random_seed=seed, draws=draws, evaluate=False, progressbar=False, target_accept=target_accept)
    return d, [str(w.message)[:300] for w in wl], time.time() - t0


def thin_post(trace, n=400, names=KEEP, extra=()):
    import xarray as xr
    post = trace["posterior"].to_dataset()
    tot = post.sizes["chain"] * post.sizes["draw"]
    keep = np.linspace(0, tot - 1, min(n, tot)).astype(int)
    out = {}
    for v in list(names) + list(extra):
        if v in post:
            out[v] = post[v].stack(s=("chain", "draw")).transpose("s", ...).to_numpy()[keep]
    return out


def atomic_json(path, obj):
    tmp = Path(str(path) + ".tmp"); tmp.write_text(json.dumps(obj, indent=1, default=str)); os.replace(tmp, path)
