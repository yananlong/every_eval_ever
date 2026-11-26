"""M1 quantities and M3 sensitivity metrics S1-S4 on the anchored scale (S5 lives in w5_sensitivity.py).
Inputs are posterior draws of the anchored ECI, arrays (n_draws, n_models), with model names in a fixed order."""
import json
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr

ANCHORS = ("Claude 3.5 Sonnet", "GPT-5")
S1_MIN, S2_SHIFT, S2_SHARE, S3_LO, S3_HI, S3_SHARE = 0.99, 0.25, 0.05, 0.8, 1.25, 0.05
S4_PAIR = 0.10


def summarise(draws):
    q05, q95 = np.quantile(draws, [0.05, 0.95], axis=0)
    return dict(mean=draws.mean(axis=0), lo=q05, hi=q95, width=q95 - q05)


def p_greater(draws, i, j):
    return float(np.mean(draws[:, i] > draws[:, j]))


def top10(mean):
    return set(np.argsort(-mean)[:10].tolist())


def p_in_top10(draws):
    ranks = np.argsort(np.argsort(-draws, axis=1), axis=1)
    return (ranks < 10).mean(axis=0)


def score(draws_k, draws_0, names, strata, s2_shift=S2_SHIFT):
    """S1-S4 of fit k against baseline 0, per stratum. strata: dict name -> boolean mask over models."""
    sk, s0 = summarise(draws_k), summarise(draws_0)
    anchor = np.array([n in ANCHORS for n in names])
    shift = np.abs(sk["mean"] - s0["mean"]) / np.where(anchor, np.nan, s0["width"])
    wr = sk["width"] / np.where(anchor, np.nan, s0["width"])
    order0 = np.argsort(-s0["mean"])
    t0, tk = top10(s0["mean"]), top10(sk["mean"])
    pair_changes = [abs(p_greater(draws_k, order0[r], order0[r + 1]) - p_greater(draws_0, order0[r], order0[r + 1])) for r in range(9)]
    s4a, s4b = tk == t0, max(pair_changes) < S4_PAIR
    out = {"S4": dict(top10_same=bool(s4a), max_pair_change=float(max(pair_changes)), pass_=bool(s4a and s4b),
                      p_top10_k=p_in_top10(draws_k).tolist(), p_top10_0=p_in_top10(draws_0).tolist())}
    for sname, mask in strata.items():
        mask = np.asarray(mask); na = mask & ~anchor
        n = int(na.sum()); lim = int(np.floor(S2_SHARE * n))
        c2 = int((shift[na] > s2_shift).sum()); c3 = int(((wr[na] < S3_LO) | (wr[na] > S3_HI)).sum())
        rho = float(spearmanr(sk["mean"][mask], s0["mean"][mask]).statistic)
        out[sname] = dict(n=n, S1=rho, S1_pass=bool(rho >= S1_MIN), S2_count=c2, S2_limit=lim, S2_pass=bool(c2 <= lim),
                          S3_count=c3, S3_limit=lim, S3_pass=bool(c3 <= lim),
                          max_rel_shift=float(np.nanmax(shift[na])), median_width_ratio=float(np.nanmedian(wr[na])))
    return out


def strata_from(path="runs/strata.json"):
    d = json.loads(Path(path).read_text())
    return d
