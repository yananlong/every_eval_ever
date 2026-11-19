"""M13 SBC rank statistic and tests. Reads true parameters only through the arguments it is given."""
import numpy as np
from scipy.stats import chi2

L = 400
N_BINS = 10
ALPHA = 0.01
BANDS = dict(c90=(0.85, 0.95), c50=(0.45, 0.55))


def anchored(cap, diff, low, high):
    """Anchored ECI (S, M) and EDI (S, K) from raw draws with each draw's own anchors (130, 150)."""
    b = 20.0 / (cap[:, high] - cap[:, low]); a = 130.0 - b * cap[:, low]
    return a[:, None] + b[:, None] * cap, a[:, None] + b[:, None] * diff


def truth_anchored(cap, diff, low, high):
    e, d = anchored(cap[None], diff[None], low, high)
    return e[0], d[0]


def u_value(draws, truth):
    """Normalised rank (#{draw < truth} + 0.5) / L of each parameter; draws (L, P), truth (P,)."""
    return ((draws < truth[None, :]).sum(0) + 0.5) / draws.shape[0]


def chi2_test(U):
    """Per-parameter chi-square against uniform over N_BINS equal bins; U (R, P). Returns p-values (P,) and counts."""
    R, P = U.shape
    bins = np.minimum((U * N_BINS).astype(int), N_BINS - 1)
    counts = np.stack([np.bincount(bins[:, j], minlength=N_BINS) for j in range(P)])
    exp = R / N_BINS
    stat = ((counts - exp) ** 2 / exp).sum(1)
    return chi2.sf(stat, N_BINS - 1), counts


def coverage(U, mask, rng, B=2000):
    """Central 50% and 90% shares pooled over replicates and the masked parameters, with a 90% replicate-bootstrap interval."""
    Um = U[:, mask]
    c90 = ((Um >= .05) & (Um <= .95)).mean(1); c50 = ((Um >= .25) & (Um <= .75)).mean(1)   # per replicate
    R = U.shape[0]; out = {}
    for name, c in (("c90", c90), ("c50", c50)):
        boots = np.array([c[rng.integers(0, R, R)].mean() for _ in range(B)])
        out[name] = dict(share=float(c.mean()), lo=float(np.quantile(boots, .05)), hi=float(np.quantile(boots, .95)))
    return out


def verdict(flags, cov_all, cov_front):
    lo9, hi9 = BANDS["c90"]; lo5, hi5 = BANDS["c50"]
    ok = dict(no_flagged_parameter=bool(flags == 0), c90_all=lo9 <= cov_all["c90"]["share"] <= hi9, c90_frontier=lo9 <= cov_front["c90"]["share"] <= hi9,
              c50_all=lo5 <= cov_all["c50"]["share"] <= hi5)
    return ok, all(ok.values())


def reduced_verdict(cov_all, cov_front):
    lo9, hi9 = BANDS["c90"]; lo5, hi5 = BANDS["c50"]
    ok = dict(c90_all=lo9 <= cov_all["c90"]["share"] <= hi9, c90_frontier=lo9 <= cov_front["c90"]["share"] <= hi9, c50_all=lo5 <= cov_all["c50"]["share"] <= hi5)
    return ok, all(ok.values())
