"""Graphical posterior predictive checks and effect sizes for the ECI fit (numpy/scipy/matplotlib; no sampler).

Overlaid densities of y and y_rep (Gabry et al. 2019, JRSS A), clip-mass and mid-range-share checks, per-benchmark statistic histograms,
effect sizes (observed minus mean replicated, in replicated SD units) and randomised LOO-PIT with ECDF-difference bands (Sailynoja et al. 2022;
recommendations for bounded and mixed data in Sailynoja, Johnson, Martin & Vehtari 2025). The raw in-sample p-values are conservative
(Meng 1994; Robins, van der Vaart & Ventura 2000), so effect sizes and graphics lead and calibrated p-values (lib/ppc_checks.max_t) screen.
"""
import numpy as np
from scipy.special import betainc
from scipy.stats import gaussian_kde

from . import ppc_checks as ppc, sbc_modrak as sm_

EPS = ppc.EPS


def simulate_yrep(mu, kap, rng):
    """y_rep (S, N) from the Beta with mean mu and concentration kap, clipped to [EPS, 1 - EPS] as the fit clips the data."""
    return np.clip(rng.beta(mu * kap, (1 - mu) * kap), EPS, 1 - EPS)


# ---------------------------------------------------------------- statistics on (1 + S, N) score matrices
def mid_share(Y): return ((Y >= 0.1) & (Y <= 0.9)).mean(1)
def clip_count(Y): return (Y <= EPS).sum(1) + (Y >= 1 - EPS).sum(1)


def bench_statistics(Y, rq, el):
    """Per-benchmark statistics of the rows of Y (R, N), with the residual quantities rq held at the real-data fit.
    Returns {name: (R, K) array} for the benchmarks with at least 20 rows (el.t1_bench):
    mean_score, boundary_count, Q_b (T1 component), dispersion (mean z^2)."""
    z = (Y - rq["mubar"]) / np.sqrt(rq["v"])
    out = {k: [] for k in ("mean_score", "boundary_count", "Q_b", "dispersion")}
    for b in el.t1_bench:
        rows = el.rows_of_bench[b]; order = rows[np.argsort(rq["chat"][el.mi[rows]], kind="stable")]
        out["mean_score"].append(Y[:, rows].mean(1)); out["boundary_count"].append(clip_count(Y[:, rows]).astype(float))
        out["Q_b"].append(sum(len(g) * z[:, g].mean(1) ** 2 for g in np.array_split(order, 4))); out["dispersion"].append((z[:, rows] ** 2).mean(1))
    return {k: np.stack(v, 1) for k, v in out.items()}


def effect_size(obs, rep):
    """(observed - mean of replicates) / SD of replicates, along axis 0 of rep. obs (...,), rep (S, ...)."""
    sd = rep.std(0, ddof=1)
    return (obs - rep.mean(0)) / np.where(sd > 0, sd, np.nan)


def global_checks(y, Yrep, rq, el, null_T=None):
    """T1-T7, boundary count and mid-range share: observed, replicated mean and SD, effect size, raw in-sample p; with null_T (list of T dicts from
    the W3 null refits) also the effect size against the null reference and the calibrated unadjusted and max-T adjusted p."""
    Tobs = ppc.stats(y, rq, el, with_components=False)
    Trep = [ppc.stats(Yrep[s], rq, el, with_components=False) for s in range(Yrep.shape[0])]
    res = {}
    for k in ppc.TNAMES:
        r = np.array([t[k] for t in Trep])
        res[k] = dict(observed=Tobs[k], rep_mean=float(r.mean()), rep_sd=float(r.std(ddof=1)), effect_size=float((Tobs[k] - r.mean()) / r.std(ddof=1)),
                      raw_p=float((r >= Tobs[k]).mean()), _rep=r)
    for name, f in (("boundary_count", clip_count), ("mid_range_share", mid_share)):
        o = f(y[None])[0]; r = f(Yrep)
        res[name] = dict(observed=float(o), rep_mean=float(r.mean()), rep_sd=float(r.std(ddof=1)), effect_size=float((o - r.mean()) / r.std(ddof=1)),
                         raw_p_upper=float((r >= o).mean()), raw_p_lower=float((r <= o).mean()), _rep=r)
    if null_T:
        mt = ppc.max_t(Tobs, null_T)
        for k in ppc.TNAMES:
            n = np.array([t[k] for t in null_T])
            res[k].update(null_R=len(n), effect_size_vs_null=float((Tobs[k] - n.mean()) / n.std(ddof=1)), p_calibrated_unadjusted=mt[k]["p_unadjusted"],
                          p_calibrated_maxT=mt[k]["p_adjusted"], z_log_obs=mt[k]["z_obs"])
    return res


# ---------------------------------------------------------------- randomised LOO-PIT
def loo_pit_randomised(logw, mu, kap, y, rng):
    """Randomised LOO-PIT of each row. logw (S, N): normalised log PSIS weights of the leave-one-out predictive; mu, kap (S, N); y (N,) clipped scores.
    Interior value: the weighted Beta CDF at y. A score at the lower clip (mass at EPS): U x weighted CDF(EPS). At the upper clip: the weighted
    CDF(1 - EPS) + U x (1 - that). U is Uniform(0, 1) per row, so the PIT is exactly Uniform(0, 1) under a calibrated predictive."""
    low = y <= EPS; high = y >= 1 - EPS
    yy = np.where(low, EPS, np.where(high, 1 - EPS, y)); N = len(y); u = np.empty(N); U = rng.uniform(size=N)
    for c in range(0, N, 400):                                   # row chunks bound the memory of the (S, rows) work arrays
        sl = slice(c, min(N, c + 400)); m, k = mu[:, sl], kap[:, sl]
        F = betainc(m * k, (1 - m) * k, yy[None, sl])
        Flo = np.where(high[None, sl], F, np.where(low[None, sl], 0.0, F)); Fhi = np.where(high[None, sl], 1.0, F)
        w = np.exp(logw[:, sl]); lo = (w * Flo).sum(0); hi = (w * Fhi).sum(0)
        u[sl] = lo + U[sl] * (hi - lo)
    return u


def pit_summary(u):
    """Shape summaries of a PIT sample: share central 90%, mean, and SD against the uniform 0.2887; gamma test."""
    g, p = sm_.gamma_test(u)
    return dict(n=len(u), mean=float(u.mean()), sd=float(u.std(ddof=1)), uniform_sd=float(np.sqrt(1 / 12)), share_below05=float((u < .05).mean()),
                share_above95=float((u > .95).mean()), share_central90=float(((u >= .05) & (u <= .95)).mean()), gamma=g, gamma_p=p)


# ---------------------------------------------------------------- plots
def _reflected_kde(v, grid):
    if len(v) < 5 or np.ptp(v) == 0: return np.zeros_like(grid)
    k = gaussian_kde(v); bw = k.factor * v.std(ddof=1)
    aug = np.concatenate([v, -v, 2 - v]); kk = gaussian_kde(aug, bw_method=bw / aug.std(ddof=1))
    return 3 * kk(grid)


def plot_density(ax, y, Yrep, rows=None, title="", n_rep=40, rng=None):
    """Observed density (black) over density of replicated datasets (grey), interior scores only, reflected at 0 and 1; the share at the clip bounds
    is shown in the title (observed and mean replicated)."""
    grid = np.linspace(0, 1, 201); rows = np.arange(len(y)) if rows is None else rows
    rng = rng or np.random.default_rng(0); idx = rng.choice(Yrep.shape[0], min(n_rep, Yrep.shape[0]), replace=False)
    inner = lambda v: v[(v > EPS) & (v < 1 - EPS)]
    for s in idx: ax.plot(grid, _reflected_kde(inner(Yrep[s][rows]), grid), color="0.7", lw=0.5)
    ax.plot(grid, _reflected_kde(inner(y[rows]), grid), color="k", lw=1.2)
    ob = clip_count(y[None, rows])[0] / len(rows); rb = clip_count(Yrep[:, rows]).mean() / len(rows)
    ax.set_title(f"{title}  clip share {ob:.3f} vs {rb:.3f}", fontsize=7); ax.tick_params(labelsize=6)


def plot_rep_hist(ax, rep, obs, title=""):
    ax.hist(rep, bins=25, color="0.75"); ax.axvline(obs, color="C3", lw=1.5); ax.set_title(title, fontsize=7); ax.tick_params(labelsize=6)
