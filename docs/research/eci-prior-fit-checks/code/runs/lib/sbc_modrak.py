"""Rank tests for simulation-based calibration with data-dependent test quantities (numpy/scipy/matplotlib only; no sampler).

Rank statistic: Talts et al. (2018), draws thinned to their effective sample size first, ties and the discreteness of the
rank randomised so that the value is Uniform(0, 1) under calibration. Test quantities: parameters and the joint
log-likelihood, per-benchmark log-likelihood and data-dependent residual summaries (Modrak et al., Bayesian Analysis, doi:10.1214/23-BA1404).
Uniformity: ECDF-difference plot with 95% simultaneous bands and the gamma statistic (Sailynoja, Burkner & Vehtari 2022, Statistics and
Computing, doi:10.1007/s11222-022-10090-6), with Pearson chi-squared (lib/sbc.py) reported alongside.
"""
import numpy as np
from scipy.special import betaln
from scipy.stats import binom, norm

from . import sbc

EPS = 1e-3
MU_EPS = 1e-6


# ---------------------------------------------------------------- effective sample size and thinning
def _acov(x):
    n = len(x); x = x - x.mean(); f = np.fft.rfft(x, 2 * n)
    return np.fft.irfft(f * np.conj(f))[:n] / n


def ess_bulk(x):
    """Bulk ESS of one series (rank-normalised; Geyer initial monotone sequence), capped at len(x). x: (L,)."""
    L = len(x)
    if np.ptp(x) == 0: return 1.0
    if L < 4: return float(L)
    r = np.argsort(np.argsort(x, kind="stable"), kind="stable") + 1.0
    z = norm.ppf((r - 3 / 8) / (L + 1 / 4))
    a = _acov(z); rho = a / a[0]
    m = (L - 1) // 2
    pairs = rho[0:2 * m:2] + rho[1:2 * m:2]
    neg = np.where(pairs < 0)[0]
    if len(neg): pairs = pairs[:neg[0]]
    if len(pairs) == 0: return float(L)
    pairs = np.minimum.accumulate(pairs)
    tau = -1.0 + 2.0 * pairs.sum()
    return float(min(L, L / max(tau, 1e-12)))


def thin_stride(ess, L):
    """Stride that leaves roughly one draw per effective draw: max(1, floor(L / ESS)). ESS above 2L/3 keeps every draw."""
    return int(max(1, np.floor(L / max(ess, 1.0))))


def randomised_rank(draws, truth, rng, stride=1):
    """Randomised normalised rank of `truth` among `draws[::stride]`: (#{below} + U * (#{equal} + 1)) / (L' + 1), Uniform(0, 1) when calibrated."""
    d = draws[::stride]; lt = (d < truth).sum(); eq = (d == truth).sum()
    return float((lt + rng.uniform() * (eq + 1)) / (len(d) + 1))


def quantity_ranks(draws, truth, rng, thin=True):
    """draws (L, P), truth (P,). Returns u (P,), stride (P,), ess (P,) (thin=False: stride 1, ESS not computed)."""
    L, P = draws.shape
    u = np.empty(P); st = np.ones(P, int); es = np.empty(P)
    for j in range(P):
        es[j] = ess_bulk(draws[:, j]) if thin else np.nan
        if thin: st[j] = thin_stride(es[j], L)
        u[j] = randomised_rank(draws[:, j], truth[j], rng, st[j])
    return u, st, es


# ---------------------------------------------------------------- ECDF-difference bands and the gamma statistic
class GammaTest:
    """Simultaneous ECDF-difference test for R independent Uniform(0, 1) values on the grid z_i = i / (G + 1), i = 1..G.

    gamma_i = 2 min(P(Z_i <= K_i), P(Z_i >= K_i)), Z_i ~ Binomial(R, z_i), K_i = #{u <= z_i}; gamma = min_i gamma_i.
    The p-value is the share of simulated uniform samples with gamma no larger than the observed one; the 95% band is the set of K_i
    with gamma_i above the 5% quantile of the simulated gamma.
    """
    _cache = {}

    def __init__(self, R, G=None, nsim=20000, seed=20261118):
        self.R = R; self.G = G or int(min(200, max(R, 50)))
        self.z = np.arange(1, self.G + 1) / (self.G + 1)
        k = np.arange(R + 1)
        lo = binom.cdf(k[None, :], R, self.z[:, None]); hi = binom.sf(k[None, :] - 1, R, self.z[:, None])
        self.tab = np.minimum(1.0, 2 * np.minimum(lo, hi))       # (G, R + 1)
        key = (R, self.G, nsim, seed)
        if key not in GammaTest._cache:
            rng = np.random.default_rng(seed)
            edges = np.concatenate([[0.0], self.z, [1.0]]); pv = np.diff(edges)
            cnt = rng.multinomial(R, pv, size=nsim)[:, :self.G].cumsum(1)
            gam = self.tab[np.arange(self.G)[None, :], cnt].min(1)
            GammaTest._cache[key] = np.sort(gam)
        self.gsim = GammaTest._cache[key]
        self.g05 = float(np.quantile(self.gsim, 0.05))
        ok = self.tab > self.g05
        self.k_lo = np.array([np.argmax(r) if r.any() else 0 for r in ok]); self.k_hi = np.array([R - np.argmax(r[::-1]) if r.any() else R for r in ok])

    def counts(self, u):
        return np.searchsorted(np.sort(u), self.z, side="right")

    def diff(self, u):
        return self.counts(u) / self.R - self.z

    def band(self):
        return self.k_lo / self.R - self.z, self.k_hi / self.R - self.z

    def test(self, u):
        """(gamma, p). p = (1 + #{gamma_sim <= gamma}) / (nsim + 1)."""
        assert len(u) == self.R
        g = float(self.tab[np.arange(self.G), self.counts(u)].min())
        p = (1 + np.searchsorted(self.gsim, g, side="right")) / (len(self.gsim) + 1)
        return g, float(p)


def gamma_test(u):
    return GammaTest(len(u)).test(np.asarray(u))


def class_summary(U, labels=None, alpha=0.01):
    """U (R, P): one randomised rank per replicate and parameter. Per-column gamma and chi-squared tests; across columns Bonferroni at alpha / P.
    Ranks within a replicate are dependent, so the pooled gamma test (all columns stacked) is descriptive."""
    R, P = U.shape; gt = GammaTest(R)
    gp = np.array([gt.test(U[:, j]) for j in range(P)])
    cp, _ = sbc.chi2_test(np.minimum(U, 1 - 1e-12))
    thr = alpha / P
    out = dict(R=R, P=P, bonferroni_level=thr,
               gamma_min_p=float(gp[:, 1].min()), gamma_median_p=float(np.median(gp[:, 1])), gamma_n_flagged=int((gp[:, 1] < thr).sum()),
               gamma_p_bonferroni=float(min(1.0, gp[:, 1].min() * P)),
               chi2_min_p=float(cp.min()), chi2_median_p=float(np.median(cp)), chi2_n_flagged=int((cp < thr).sum()),
               chi2_expected_per_bin=R / sbc.N_BINS,
               share_central90=float(((U >= .05) & (U <= .95)).mean()), share_central50=float(((U >= .25) & (U <= .75)).mean()),
               share_below05=float((U < .05).mean()), share_above95=float((U > .95).mean()), mean_u=float(U.mean()))
    rng = np.random.default_rng(1)
    flat = U.ravel(); flat = flat if len(flat) <= 2000 else rng.choice(flat, 2000, replace=False)
    pg = GammaTest(len(flat)).test(flat)
    out.update(pooled_gamma=pg[0], pooled_gamma_p_descriptive=pg[1])
    if labels is not None and out["gamma_n_flagged"]:
        out["gamma_flagged"] = [labels[j] for j in np.where(gp[:, 1] < thr)[0][:30]]
    return out, gp


def scalar_summary(u):
    """One test quantity, one rank per replicate (u (R,)): exact gamma test, chi-squared, central shares."""
    u = np.asarray(u); g, p = gamma_test(u)
    cp, _ = sbc.chi2_test(np.minimum(u, 1 - 1e-12)[:, None])
    return dict(R=len(u), gamma=g, gamma_p=p, chi2_p=float(cp[0]), chi2_expected_per_bin=len(u) / sbc.N_BINS,
                share_central90=float(((u >= .05) & (u <= .95)).mean()), share_below05=float((u < .05).mean()), share_above95=float((u > .95).mean()), mean_u=float(u.mean()))


# ---------------------------------------------------------------- model quantities (Beta likelihood of the ECI model)
def loglik_rows(theta, y, mi, bi):
    """Row log-likelihoods (S, N) of the clipped scores y under theta = dict(capability (S, M), difficulty (S, K), slope (S, K), sigma (S, K))."""
    eta = theta["slope"][:, bi] * (theta["capability"][:, mi] - theta["difficulty"][:, bi])
    mu = np.clip(1 / (1 + np.exp(-np.clip(eta, -700, 700))), MU_EPS, 1 - MU_EPS)
    kap = (1 / (4 * theta["sigma"] ** 2) - 1)[:, bi]
    a, b = mu * kap, (1 - mu) * kap
    ll = (a - 1) * np.log(y)[None, :] + (b - 1) * np.log1p(-y)[None, :] - betaln(a, b)
    return ll, mu, kap


def stack_theta(draws, truth):
    """Draw arrays (L, ...) with the truth appended as the last row."""
    return {k: np.concatenate([draws[k], np.asarray(truth[k])[None]], 0) for k in ("capability", "difficulty", "slope", "sigma")}


def data_quantities(theta, y, mi, bi, K):
    """Test quantities that depend on the data, each evaluated at every theta row. Returns {class: (names, array (S, P))}.

    loglik_joint: sum of row log-likelihoods; loglik_bench: per benchmark; resid_overall / resid_bench: mean of y - mu overall and per benchmark;
    pearson_overall: mean of (y - mu)^2 (kappa + 1) / (mu (1 - mu))."""
    ll, mu, kap = loglik_rows(theta, y, mi, bi)
    r = y[None, :] - mu
    pear = r ** 2 * (kap + 1) / (mu * (1 - mu))
    cnt = np.bincount(bi, minlength=K).astype(float)
    llb = np.stack([np.bincount(bi, weights=ll[s], minlength=K) for s in range(ll.shape[0])])
    rb = np.stack([np.bincount(bi, weights=r[s], minlength=K) for s in range(r.shape[0])]) / np.maximum(cnt, 1)
    return {"loglik_joint": (["loglik_joint"], ll.sum(1, keepdims=True)),
            "loglik_bench": ([f"b{k}" for k in range(K)], llb),
            "resid_overall": (["resid_overall"], r.mean(1, keepdims=True)),
            "resid_bench": ([f"b{k}" for k in range(K)], rb),
            "pearson_overall": (["pearson_overall"], pear.mean(1, keepdims=True))}


def parameter_quantities(theta, hyper_draws, hyper_truth, low, high):
    """Parameter classes as in lib/sbc.py: anchored ECI (non-anchor models) and EDI, slope, sigma, hyperparameters; plus class summaries
    (ECI mean and SD over non-anchor models, EDI mean and SD, SD of log slope, mean sigma), each one scalar per replicate."""
    cap, dif = theta["capability"], theta["difficulty"]
    eci, edi = sbc.anchored(cap, dif, low, high)
    na = np.ones(cap.shape[1], bool); na[[low, high]] = False
    out = {"eci": ([f"m{j}" for j in np.where(na)[0]], eci[:, na]), "edi": ([f"b{k}" for k in range(dif.shape[1])], edi),
           "slope": ([f"b{k}" for k in range(dif.shape[1])], theta["slope"]), "sigma": ([f"b{k}" for k in range(dif.shape[1])], theta["sigma"]),
           "hyper": (list(hyper_draws), np.stack([np.append(hyper_draws[h], hyper_truth[h]) for h in hyper_draws], 1))}
    out["class_summaries"] = (["eci_mean", "eci_sd", "edi_mean", "edi_sd", "logslope_sd", "sigma_mean"],
                              np.stack([eci[:, na].mean(1), eci[:, na].std(1), edi.mean(1), edi.std(1), np.log(theta["slope"]).std(1), theta["sigma"].mean(1)], 1))
    return out


def replicate_ranks(draws, truth, y, mi, bi, K, low, high, rng, thin=True):
    """All test-quantity ranks of one replicate. draws: dict of (L, ...) arrays (capability, difficulty, slope, sigma, tau_alpha, sigma_median, tau_sigma);
    truth: dict of the same without the draw axis; y: clipped scores. Returns {class: dict(names, u, stride, ess)}."""
    th = stack_theta(draws, truth)
    hd = {h: draws[h] for h in ("tau_alpha", "sigma_median", "tau_sigma")}; ht = {h: float(truth[h]) for h in hd}
    q = parameter_quantities(th, hd, ht, low, high); q.update(data_quantities(th, y, mi, bi, K))
    res = {}
    for cls, (names, A) in q.items():
        u, st, es = quantity_ranks(A[:-1], A[-1], rng, thin)
        res[cls] = dict(names=names, u=u, stride=st, ess=es)
    return res


def aggregate(per):
    """per: list of replicate_ranks outputs. Returns (summary per class, {class: (U (R, P), names)})."""
    res, figU = {}, {}
    for cls in per[0]:
        U = np.stack([p[cls]["u"] for p in per]); lab = per[0][cls]["names"]; figU[cls] = (U, lab)
        ess = np.stack([p[cls]["ess"] for p in per]); st = np.stack([p[cls]["stride"] for p in per])
        if U.shape[1] == 1:
            s = scalar_summary(U[:, 0]); s["kind"] = "scalar"
        else:
            s, _ = class_summary(U, lab); s["kind"] = "vector"
        s.update(median_ess=float(np.nanmedian(ess)) if np.isfinite(ess).any() else None, median_stride=float(np.median(st)), share_thinned=float((st > 1).mean()))
        res[cls] = s
    return res, figU


def augment(df_obs, y_sim):
    """Posterior SBC data: the observed rows followed by the simulated rows on the same (model, benchmark) cells (performance replaced by y_sim).
    Model and benchmark codes keep their first-appearance order, so parameters line up with the observed-data fit."""
    import pandas as pd
    sim = df_obs.copy(); sim["performance"] = np.asarray(y_sim)
    return pd.concat([df_obs, sim], ignore_index=True)


# ---------------------------------------------------------------- plotting
def plot_ecdf_diff(ax, U, labels=None, title="", single_color="C0", pooled=False):
    """ECDF difference of each column of U (R, P) with the 95% simultaneous band for R values; many columns are drawn faint."""
    R = U.shape[0]; gt = GammaTest(R); lo, hi = gt.band()
    ax.fill_between(gt.z, lo, hi, color="0.85", label="95% simultaneous band")
    P = U.shape[1]
    for j in range(P):
        ax.plot(gt.z, gt.diff(U[:, j]), lw=0.8 if P < 8 else 0.4, alpha=1 if P < 8 else 0.5, color=None if P < 8 else single_color,
                label=(labels[j] if labels is not None and P < 8 else None))
    ax.axhline(0, color="k", lw=0.5); ax.set_title(f"{title} (R={R}, P={P})", fontsize=9); ax.set_xlabel("rank u"); ax.set_ylabel("ECDF(u) - u")
    if labels is not None and P < 8: ax.legend(fontsize=6)
