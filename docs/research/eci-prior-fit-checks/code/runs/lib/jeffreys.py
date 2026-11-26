"""Prior J (exploratory): Epoch's model plus the block-diagonal conditional Jeffreys prior on (c, d) given (a, kappa).

    log p_J(c, d | a, kappa) = sum_m 1/2 log I_m + sum_b 1/2 log I_b,
    I_m = sum_{b in obs(m)} a_b^2 g(eta_mb, kappa_b),   I_b = sum_{m in obs(b)} a_b^2 g(eta_mb, kappa_b),
    g(eta, kappa) = [mu (1 - mu)]^2 kappa^2 [psi1(mu kappa) + psi1((1 - mu) kappa)],   mu = sigmoid(eta).

g is evaluated from the unclipped eta, in the equivalent form g = (1 - mu)^2 h(mu kappa) + mu^2 h((1 - mu) kappa) with
h(x) = x^2 psi1(x) = 1 + x^2 psi1(x + 1), which stays finite as mu goes to 0 or 1. The sums run over the observed cells.
The Beta likelihood's clipping of y is ignored. Reuses models.build_model; nothing in models.py is changed.
"""
import numpy as np
import pymc as pm
import pytensor.tensor as pt
from . import models

_F0 = models.build_model  # captured at import so that swapping models.build_model for J does not recurse

_ASY = (1 / 6, 0.0, -1 / 30, 0.0, 1 / 42, 0.0, -1 / 30, 0.0, 5 / 66, 0.0, -691 / 2730, 0.0, 7 / 6)


def trigamma1p(x, shifts=6):
    """psi1(x + 1) for x >= 0: recurrence up to an argument of at least 7, then the asymptotic series. Differentiable."""
    z = x + 1.0
    acc = 0.0
    for k in range(shifts):
        acc = acc + 1.0 / (z + k) ** 2
    w = z + shifts
    iw = 1.0 / w
    iw2 = iw * iw
    # 1/w + 1/(2 w^2) + sum_k B_2k / w^(2k+1)
    s = iw + 0.5 * iw2
    p = iw * iw2
    for c in _ASY[::2]:
        s = s + c * p
        p = p * iw2
    return acc + s


def _h(x, backend="custom"):
    """x^2 psi1(x) for x > 0."""
    if backend == "pytensor":
        return x ** 2 * pt.tri_gamma(x)
    return 1.0 + x ** 2 * trigamma1p(x)


def log_info_g(eta, kappa, backend="custom"):
    """log g(eta, kappa), stable for |eta| large."""
    log_mu = -pt.softplus(-eta)
    log_1mu = -pt.softplus(eta)
    a = pt.exp(log_mu) * kappa
    b = pt.exp(log_1mu) * kappa
    t1 = 2.0 * log_1mu + pt.log(_h(a, backend))
    t2 = 2.0 * log_mu + pt.log(_h(b, backend))
    return pt.logaddexp(t1, t2)


def jeffreys_logp(eta, kappa_obs, slope_obs, midx, bidx, M, K, backend="custom"):
    """The potential: sum over models and benchmarks of 1/2 log of the information."""
    term = 2.0 * pt.log(slope_obs) + log_info_g(eta, kappa_obs, backend)  # log(a_b^2 g) per observed cell
    e = pt.exp(term)
    I_m = pt.zeros((M,))
    I_m = pt.inc_subtensor(I_m[midx], e)
    I_b = pt.zeros((K,))
    I_b = pt.inc_subtensor(I_b[bidx], e)
    return 0.5 * pt.log(I_m).sum() + 0.5 * pt.log(I_b).sum()


def build_j(df, potential=True, likelihood=True, backend="custom", priors=None):
    """F0 (models.build_model, Epoch's model) with the Jeffreys potential `jeffreys` added.
    potential=False gives F0 itself; likelihood=False drops the Beta likelihood for prior-only sampling."""
    model = _F0(df, models.Spec(), priors)
    names, bnames, midx, bidx = models._index(df)
    M, K = len(names), len(bnames)
    if potential:
        with model:
            cap, dif, slope, kappa = (model[n] for n in ("capability", "difficulty", "slope", "kappa"))
            eta = slope[bidx] * (cap[midx] - dif[bidx])
            pm.Potential("jeffreys", jeffreys_logp(eta, kappa[bidx], slope[bidx], midx, bidx, M, K, backend))
    if not likelihood:
        obs = model["obs"]
        model.observed_RVs.remove(obs)
        model.rvs_to_values.pop(obs)
        model.named_vars.pop("obs")
        model.named_vars_to_dims.pop("obs", None)
    return model


class epoch_with_j:
    """Context manager: models.build_model returns J for Spec() in this process, so fit.fit(spec=Spec()) fits J."""
    def __enter__(self):
        self._saved = models.build_model
        models.build_model = lambda df, spec=models.Spec(), priors=None, eps=1e-3, ex=None: build_j(df, priors=priors)
        return self

    def __exit__(self, *a):
        models.build_model = self._saved
