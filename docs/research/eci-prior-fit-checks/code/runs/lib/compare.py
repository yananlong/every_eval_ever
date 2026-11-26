"""M14 comparison helpers: PSIS-LOO, the K-fold trigger, the preference rule, the adequate set. Frozen before the first W6 fit."""
import numpy as np
import arviz as az

DELTA_MIN, Z_MIN, K_SHARE, K_LIM, ADEQUATE_WINDOW = 4.0, 2.5, 0.02, 0.7, 4.0


def loo_stats(trace):
    """PSIS-LOO over the 'obs' log-likelihood of a fit: elpd, se, p_loo, per-row elpd and Pareto k."""
    r = az.loo(trace, pointwise=True, var_name="obs")
    elpd_i = np.asarray(r.elpd_i if hasattr(r, "elpd_i") else r["elpd_i"]).ravel()
    k = np.asarray(r.pareto_k).ravel()
    return dict(elpd=float(r.elpd), se=float(r.se), p=float(r.p), elpd_i=elpd_i, k=k, k_share=float(np.mean(k > K_LIM)), n_k_gt_0_7=int((k > K_LIM).sum()))


def paired(elpd_i_j, elpd_i_0):
    d = np.asarray(elpd_i_j) - np.asarray(elpd_i_0)
    return float(d.sum()), float(np.sqrt(len(d)) * d.std(ddof=1))


def kfold_trigger(k_share_a, k_share_b):
    return bool(k_share_a > K_SHARE or k_share_b > K_SHARE)


def preferred(delta, se):
    return bool(delta > DELTA_MIN and delta > Z_MIN * se)


def adequate_set(adopted_elpd):
    """adopted_elpd: dict name -> elpd on a common estimator. The adopted models within 4 of the best."""
    if not adopted_elpd: return []
    best = max(adopted_elpd.values())
    return sorted([n for n, e in adopted_elpd.items() if best - e <= ADEQUATE_WINDOW], key=lambda n: -adopted_elpd[n])
