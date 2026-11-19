"""Normalised, capability-only Jeffreys priors J1 and J2 (exploratory). Epoch's model plus one potential

    sum_m [ 1/2 log I_m(c_m) - log Z_m ],   I_m(c) = sum_{b in obs(m)} a_b^2 g(a_b (c - d_b), kappa_b),
    Z_m = int_{-50}^{50} sqrt(I_m(c)) dc,

so that each c_m has the proper conditional density sqrt(I_m(c)) / Z_m on [-50, 50] given (a, d, kappa); difficulties get no
Jeffreys term. J1: g is the Beta information about eta, [mu(1-mu)]^2 kappa^2 [psi1(mu kappa) + psi1((1-mu) kappa)].
J2: g = mu (1 - mu), the Bernoulli information (the textbook item-response form; only heuristic for the Beta likelihood).
Z_m is a fixed-node composite Gauss-Legendre rule, differentiable in PyTensor. Reuses lib/jeffreys.py and models.py.
"""
import numpy as np
import pymc as pm
import pytensor.tensor as pt
from . import models, jeffreys as J

BOUND = 50.0


def nodes(dense=16.0, dense_n=8, coarse_n=6, n_coarse_panels=4):
    """Composite Gauss-Legendre nodes and weights on [-50, 50]: unit panels (8 nodes) on [-16, 16], 4 panels of width 8.5 (6 nodes) on each side."""
    edges = np.unique(np.concatenate([np.linspace(-BOUND, -dense, n_coarse_panels + 1), np.arange(-dense, dense + 1e-9, 1.0), np.linspace(dense, BOUND, n_coarse_panels + 1)]))
    xs, ws = [], []
    for lo, hi in zip(edges[:-1], edges[1:]):
        x, w = np.polynomial.legendre.leggauss(dense_n if hi - lo <= 1.0 + 1e-9 else coarse_n)
        xs.append(0.5 * (hi - lo) * x + 0.5 * (hi + lo)); ws.append(0.5 * (hi - lo) * w)
    return np.concatenate(xs), np.concatenate(ws)


def g_expr(eta, kappa, variant):
    if variant == "J2":
        return pt.exp(-pt.softplus(-eta) - pt.softplus(eta))
    return pt.exp(J.log_info_g(eta, kappa))


def _incidence(midx, bidx, M, K):
    O = np.zeros((M, K)); np.add.at(O, (midx, bidx), 1.0)
    return O


def norm_potential(cap, dif, slope, kappa, midx, bidx, M, K, variant="J1", xw=None):
    x, w = xw if xw is not None else nodes()
    eta = slope[bidx] * (cap[midx] - dif[bidx])
    I_cell = slope[bidx] ** 2 * g_expr(eta, kappa[bidx], variant)
    I_m = pt.inc_subtensor(pt.zeros((M,))[midx], I_cell)
    eta_k = slope[:, None] * (x[None, :] - dif[:, None])
    G = slope[:, None] ** 2 * g_expr(eta_k, kappa[:, None], variant)
    I_mk = pt.dot(_incidence(midx, bidx, M, K), G)
    Z = pt.sum(w[None, :] * pt.sqrt(I_mk), axis=1)
    return 0.5 * pt.log(I_m).sum() - pt.log(Z).sum()


def build_jn(df, variant="J1", potential=True, likelihood=True, priors=None):
    """F0 (models.build_model) plus the potential `jeffreys_norm`. potential=False gives F0 itself; likelihood=False drops the Beta likelihood."""
    model = J._F0(df, models.Spec(), priors)
    names, bnames, midx, bidx = models._index(df)
    M, K = len(names), len(bnames)
    if potential:
        with model:
            pm.Potential("jeffreys_norm", norm_potential(model["capability"], model["difficulty"], model["slope"], model["kappa"], midx, bidx, M, K, variant))
    if not likelihood:
        obs = model["obs"]
        model.observed_RVs.remove(obs); model.rvs_to_values.pop(obs); model.named_vars.pop("obs"); model.named_vars_to_dims.pop("obs", None)
    return model


class epoch_with_jn:
    """Context manager: models.build_model returns J1 or J2 for Spec() in this process, so fit.fit(spec=Spec()) fits it."""
    def __init__(self, variant): self.variant = variant

    def __enter__(self):
        self._saved = models.build_model
        v = self.variant
        models.build_model = lambda df, spec=models.Spec(), priors=None, eps=1e-3, ex=None: build_jn(df, v, priors=priors)
        return self

    def __exit__(self, *a):
        models.build_model = self._saved


# ---------------- numpy versions, for direct simulation and independent checks
_ASY = (1 / 6, -1 / 30, 1 / 42, -1 / 30, 5 / 66, -691 / 2730, 7 / 6)


def trigamma1p_np(x):
    """psi1(x + 1), x >= 0: recurrence to argument >= 7 then the asymptotic series."""
    z = np.asarray(x, float) + 1.0
    acc = sum(1.0 / (z + k) ** 2 for k in range(6))
    w = z + 6.0; iw = 1.0 / w; iw2 = iw * iw
    s = iw + 0.5 * iw2; p = iw * iw2
    for c in _ASY:
        s = s + c * p; p = p * iw2
    return acc + s


def g_np(eta, kappa, variant):
    """g(eta, kappa) in numpy, stable for large |eta|."""
    eta = np.asarray(eta, float)
    sp = lambda t: np.logaddexp(0.0, t)
    log_mu, log_om = -sp(-eta), -sp(eta)
    if variant == "J2":
        return np.exp(log_mu + log_om)
    mu, om = np.exp(log_mu), np.exp(log_om)
    a, b = mu * kappa, om * kappa
    h = lambda x: 1.0 + x ** 2 * trigamma1p_np(x)
    return om ** 2 * h(a) + mu ** 2 * h(b)
