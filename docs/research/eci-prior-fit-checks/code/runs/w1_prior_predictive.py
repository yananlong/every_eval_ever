"""W1 (M11): prior predictive check of Epoch's priors and of the reference prior PR on the observed cell pattern."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
from lib import data

OUT = Path("runs/W/W1"); OUT.mkdir(parents=True, exist_ok=True)
D = 1000
df = data.fit_input()
mi = df["model_id"].astype("category").cat.codes.to_numpy(); bi = df["benchmark_id"].astype("category").cat.codes.to_numpy()
# first-appearance order is irrelevant for the simulation; only the (model, benchmark) pattern is used
M, K = mi.max() + 1, bi.max() + 1
ss = np.random.SeedSequence(20261113).spawn(2)


def zsn(rng, k, sd):
    x = rng.normal(0, sd, k); return x - x.mean()


def sim(rng, kind):
    tau_a = np.exp(rng.normal(np.log(.5), .5)); s_med = np.exp(rng.normal(np.log(.1), .5)); tau_s = np.exp(rng.normal(np.log(.5), .5))
    sg = np.exp(rng.normal(np.log(s_med), tau_s, K))
    while (sg >= .5).any():
        bad = sg >= .5; sg[bad] = np.exp(rng.normal(np.log(s_med), tau_s, bad.sum()))
    kap = 1 / (4 * sg ** 2) - 1
    ls = zsn(rng, K, tau_a * np.sqrt(K / (K - 1)))
    if kind == "epoch":
        c = rng.uniform(-50, 50, M); d = rng.uniform(-50, 50, K); d -= d.mean()
    else:
        s = np.exp(rng.normal(np.log(2.), .5)); muc = rng.normal(0, 2.)
        c = rng.normal(muc, s, M); d = zsn(rng, K, s * np.sqrt(K / (K - 1)))
    eta = np.exp(ls[bi]) * (c[mi] - d[bi])
    mu = np.clip(1 / (1 + np.exp(-np.clip(eta, -700, 700))), 1e-6, 1 - 1e-6)
    y = rng.beta(mu * kap[bi], (1 - mu) * kap[bi])
    return y, mu, eta


res = {"n_datasets": D, "n_cells": int(len(df)), "seed": "numpy SeedSequence(20261113).spawn(2): stream 0 Epoch, stream 1 PR"}
fig_data = {}
for k, kind in enumerate(["epoch", "reference"]):
    rng = np.random.default_rng(ss[k]); bnd, mid, mu_mid, sat = [], [], [], []
    for _ in range(D):
        y, mu, eta = sim(rng, kind)
        bnd.append(((y <= 1e-3) | (y >= 1 - 1e-3)).mean()); mid.append(((y >= .1) & (y <= .9)).mean())
        mu_mid.append(((mu >= .1) & (mu <= .9)).mean()); sat.append((np.abs(eta) > 6.9).mean())
    bnd, mid, mu_mid, sat = map(np.array, (bnd, mid, mu_mid, sat))
    q = lambda a: dict(mean=float(a.mean()), p05=float(np.quantile(a, .05)), p95=float(np.quantile(a, .95)))
    res[kind] = dict(clip_bound_share=q(bnd), mid_range_share=q(mid), mu_in_01_09_share=q(mu_mid), abs_logit_gt_6p9_share=q(sat),
                     n_datasets_mid_ge_015=int((mid >= .15).sum()))
    fig_data[kind] = (bnd, mid)
pr = res["reference"]
res["PR_criterion"] = dict(mean_mid_ge_040=pr["mid_range_share"]["mean"] >= .40, datasets_mid_ge_015_at_least_950=pr["n_datasets_mid_ge_015"] >= 950,
                           mean_bound_le_035=pr["clip_bound_share"]["mean"] <= .35)
res["PR_passes"] = all(res["PR_criterion"].values())
e = res["epoch"]
res["epoch_reproduces_review_figures"] = bool(abs(e["clip_bound_share"]["mean"] - .89) <= .01 and abs(e["mid_range_share"]["mean"] - .05) <= .01)
res["epoch_criterion"] = dict(mean_mid_ge_040=e["mid_range_share"]["mean"] >= .40, datasets_mid_ge_015_at_least_950=e["n_datasets_mid_ge_015"] >= 950, mean_bound_le_035=e["clip_bound_share"]["mean"] <= .35)
(OUT / "prior_predictive.json").write_text(json.dumps(res, indent=1))
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
f, ax = plt.subplots(1, 2, figsize=(9, 3.5))
for kind, col in (("epoch", "tab:red"), ("reference", "tab:blue")):
    ax[0].hist(fig_data[kind][0], 40, alpha=.6, color=col, label=kind); ax[1].hist(fig_data[kind][1], 40, alpha=.6, color=col)
ax[0].set_xlabel("share of scores at the clip bounds"); ax[1].set_xlabel("share of scores in [0.1, 0.9]"); ax[0].legend()
f.tight_layout(); f.savefig(OUT / "fig_prior_predictive.png", dpi=110)
print(json.dumps({k: res[k] for k in ("epoch", "reference", "PR_criterion", "PR_passes", "epoch_reproduces_review_figures")}, indent=1))
