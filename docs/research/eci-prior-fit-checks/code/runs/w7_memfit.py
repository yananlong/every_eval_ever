"""In-memory W7 fit for throwaway fits (model-true replicates, K-fold folds): the same call as the frozen
lib/fit.fit (Epoch's fit_bayesian_eci under models.epoch_with, same seed, same verdict and sidecar fields), but the trace
stays in memory and no .nc is written. The container only sees /home (on the root disk), so this replaces a /dev/shm
trace folder."""
import time, warnings
from lib import models, fit as fitmod


def fit_mem(df, spec, seed, ex):
    import eci.bayesian as eb
    t0 = time.time()
    with warnings.catch_warnings(record=True) as wl:
        warnings.simplefilter("always")
        with models.epoch_with(spec, ex, None):
            eci_df, edi_df, d = eb.fit_bayesian_eci(df, random_seed=seed, draws=None, evaluate=False, progressbar=False)
    trace = fitmod.add_groups(d["trace"], d["eci"], d["model_names"])
    ok, last = fitmod.verdict(d["attempts"])
    side = dict(started_from=d["started_from"], attempts=d["attempts"], converged=ok, last_attempt=last,
                warnings=[str(w.message)[:300] for w in wl], wall_seconds=round(time.time() - t0, 1))
    return side, trace
