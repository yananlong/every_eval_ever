"""W1-J1 and W1-J2 (exploratory): prior predictive check of the normalised capability-only Jeffreys priors by direct simulation (numpy only).
Hyperparameters, slopes and sigma are drawn from Epoch's priors and d from centred uniforms exactly as in W1; each c_m is drawn from
sqrt(I_m(c)) / Z_m by inverse CDF on an 8,001-point grid over [-50, 50]. Run from the v11 root, single thread."""
import sys, json, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
from lib import data, models, jeffreys_norm as N

OUT = Path("runs/W/W1J"); OUT.mkdir(parents=True, exist_ok=True)
D = 1000; NG = 8001
df = data.fit_input()
mi = df["model_id"].astype("category").cat.codes.to_numpy(); bi = df["benchmark_id"].astype("category").cat.codes.to_numpy()
M, K = mi.max() + 1, bi.max() + 1
O = N._incidence(mi, bi, M, K)
GRID = np.linspace(-50, 50, NG)
ss = np.random.SeedSequence(20261113).spawn(4)  # 0 Epoch and 1 PR as in W1; 2 J1; 3 J2


def zsn(rng, k, sd):
    x = rng.normal(0, sd, k); return x - x.mean()


def hyper(rng):
    tau_a = np.exp(rng.normal(np.log(.5), .5)); s_med = np.exp(rng.normal(np.log(.1), .5)); tau_s = np.exp(rng.normal(np.log(.5), .5))
    sg = np.exp(rng.normal(np.log(s_med), tau_s, K))
    while (sg >= .5).any():
        bad = sg >= .5; sg[bad] = np.exp(rng.normal(np.log(s_med), tau_s, bad.sum()))
    kap = 1 / (4 * sg ** 2) - 1
    ls = zsn(rng, K, tau_a * np.sqrt(K / (K - 1)))
    return kap, ls


def sim_old(rng, kind):
    kap, ls = hyper(rng)
    if kind == "epoch":
        c = rng.uniform(-50, 50, M); d = rng.uniform(-50, 50, K); d -= d.mean()
    else:
        s = np.exp(rng.normal(np.log(2.), .5)); muc = rng.normal(0, 2.)
        c = rng.normal(muc, s, M); d = zsn(rng, K, s * np.sqrt(K / (K - 1)))
    return c, d, np.exp(ls), kap


def sim_norm(rng, variant):
    kap, ls = hyper(rng); a = np.exp(ls)
    d = rng.uniform(-50, 50, K); d -= d.mean()
    G = a[:, None] ** 2 * N.g_np(a[:, None] * (GRID[None, :] - d[:, None]), kap[:, None], variant)
    f = np.sqrt(O @ G)
    cdf = np.concatenate([np.zeros((M, 1)), np.cumsum(0.5 * (f[:, 1:] + f[:, :-1]) * np.diff(GRID), axis=1)], axis=1)
    cdf /= cdf[:, -1:]
    u = rng.uniform(0, 1, M)
    j = np.clip((cdf < u[:, None]).sum(1), 1, NG - 1)
    lo, hi = cdf[np.arange(M), j - 1], cdf[np.arange(M), j]
    c = GRID[j - 1] + (u - lo) / np.maximum(hi - lo, 1e-300) * (GRID[j] - GRID[j - 1])
    return c, d, a, kap


def observe(rng, c, d, a, kap):
    eta = a[bi] * (c[mi] - d[bi])
    mu = np.clip(1 / (1 + np.exp(-np.clip(eta, -700, 700))), 1e-6, 1 - 1e-6)
    y = rng.beta(mu * kap[bi], (1 - mu) * kap[bi])
    return y, mu, eta


def stats(y, mu, eta):
    return (((y <= 1e-3) | (y >= 1 - 1e-3)).mean(), ((y >= .1) & (y <= .9)).mean(), ((mu >= .1) & (mu <= .9)).mean(), (np.abs(eta) > 6.9).mean())


def summarise(rows):
    bnd, mid, mu_mid, sat = map(np.array, zip(*rows))
    q = lambda a: dict(mean=float(a.mean()), p05=float(np.quantile(a, .05)), p95=float(np.quantile(a, .95)))
    return dict(clip_bound_share=q(bnd), mid_range_share=q(mid), mu_in_01_09_share=q(mu_mid), abs_logit_gt_6p9_share=q(sat),
                n_datasets_mid_ge_015=int((mid >= .15).sum())), (bnd, mid)


def criteria(r):
    return dict(mean_mid_ge_040=bool(r["mid_range_share"]["mean"] >= .40), datasets_mid_ge_015_at_least_950=bool(r["n_datasets_mid_ge_015"] >= 950),
                mean_bound_le_035=bool(r["clip_bound_share"]["mean"] <= .35))


if __name__ == "__main__":
    res = {"n_datasets": D, "n_cells": int(len(df)), "grid_points": NG,
           "seed": "numpy SeedSequence(20261113).spawn(4): stream 0 Epoch and 1 PR (as W1), 2 J1, 3 J2; direct simulation, no NUTS"}
    fig = {}
    for k, kind in enumerate(["epoch", "reference"]):
        rng = np.random.default_rng(ss[k]); rows = []
        for _ in range(D):
            c, d, a, kap = sim_old(rng, kind); rows.append(stats(*observe(rng, c, d, a, kap)))
        res[kind], fig[kind] = summarise(rows)
    old = json.loads(Path("runs/W/W1/prior_predictive.json").read_text())
    res["regenerated_W1_matches_stored"] = bool(all(old[k][q] == res[k][q] for k in ("epoch", "reference") for q in ("clip_bound_share", "mid_range_share", "n_datasets_mid_ge_015")))
    for k, variant in ((2, "J1"), (3, "J2")):
        rng = np.random.default_rng(ss[k]); rows = []; spread = []; t0 = time.time()
        for i in range(D):
            c, d, a, kap = sim_norm(rng, variant); rows.append(stats(*observe(rng, c, d, a, kap))); spread.append((c.std(), np.abs(c).mean(), (np.abs(c) > 25).mean()))
            if i % 100 == 0: print(variant, i, round(time.time() - t0), flush=True)
        res[variant], fig[variant] = summarise(rows)
        sp = np.array(spread).mean(0); res[variant]["capability_draws"] = dict(mean_sd=float(sp[0]), mean_abs=float(sp[1]), mean_share_abs_gt_25=float(sp[2]))
        res[variant + "_criterion_descriptive"] = criteria(res[variant]); res[variant + "_would_pass_PR_criterion"] = all(res[variant + "_criterion_descriptive"].values())
    (OUT / "prior_predictive_J1J2.json").write_text(json.dumps(res, indent=1))
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    f, ax = plt.subplots(1, 2, figsize=(9, 3.5))
    for kind, col, lab in (("epoch", "tab:red", "Epoch's flat priors"), ("reference", "tab:blue", "reference prior PR"), ("J1", "tab:green", "J1 (Beta information)"), ("J2", "tab:orange", "J2 (Bernoulli information)")):
        ax[0].hist(fig[kind][0], 40, alpha=.55, color=col, label=lab); ax[1].hist(fig[kind][1], 40, alpha=.55, color=col)
    ax[0].set_xlabel("share of scores at the clip bounds"); ax[1].set_xlabel("share of scores in [0.1, 0.9]"); ax[0].legend(fontsize=7)
    f.tight_layout(); f.savefig(OUT / "fig_prior_predictive_J1J2.png", dpi=110)
    print(json.dumps({k: res[k] for k in ("regenerated_W1_matches_stored", "epoch", "reference", "J1", "J2", "J1_criterion_descriptive", "J2_criterion_descriptive")}, indent=1))
