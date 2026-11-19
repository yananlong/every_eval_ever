"""W1-J (exploratory): prior predictive check of the Jeffreys prior J on the observed cell pattern, next to Epoch's priors and PR.
J is sampled with PyMC NUTS (no likelihood); Epoch's and PR draws are regenerated from the W1 seeds. Run from the v11 root."""
import sys, json, time, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pymc as pm, arviz as az
from lib import data, models, jeffreys as J

OUT = Path("runs/W/W1J"); OUT.mkdir(parents=True, exist_ok=True)
D = 1000
df = data.fit_input()
mi = df["model_id"].astype("category").cat.codes.to_numpy(); bi = df["benchmark_id"].astype("category").cat.codes.to_numpy()
M, K = mi.max() + 1, bi.max() + 1
ss = np.random.SeedSequence(20261113).spawn(3)  # streams 0 and 1 are those of W1 (Epoch, PR); stream 2 is J's simulation of y


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
    return c, d, np.exp(ls), kap


def observe(rng, c, d, a, kap):
    """Pre-noise mean, eta and a simulated score vector on the observed cells (as in W1)."""
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
    return dict(mean_mid_ge_040=r["mid_range_share"]["mean"] >= .40, datasets_mid_ge_015_at_least_950=r["n_datasets_mid_ge_015"] >= 950,
                mean_bound_le_035=r["clip_bound_share"]["mean"] <= .35)


def nuts_prior(potential, seed):
    m = J.build_j(df, potential=potential, likelihood=False)
    t0 = time.time()
    with m:
        tr = pm.sample(draws=2000, tune=1000, chains=1, cores=1, target_accept=0.95, random_seed=seed, progressbar=False, compute_convergence_checks=False)
    wall = time.time() - t0
    post = tr["posterior"].to_dataset(); st = tr["sample_stats"].to_dataset()
    div = int(st["diverging"].sum())
    tree = st["tree_depth"].to_numpy().ravel() if "tree_depth" in st else None
    names = ["capability", "difficulty", "log_slope", "sigma", "tau_alpha", "sigma_median", "tau_sigma"]
    rh, eb, et = {}, {}, {}
    for v in names:
        rh[v] = float(np.nanmax(az.rhat(tr, var_names=[v])[v].to_numpy())); eb[v] = float(np.nanmin(az.ess(tr, var_names=[v])[v].to_numpy()))
        et[v] = float(np.nanmin(az.ess(tr, var_names=[v], method="tail")[v].to_numpy()))
    diag = dict(draws=2000, tune=1000, chains=1, target_accept=0.95, divergences=div, step_size=float(st["step_size"].to_numpy().ravel()[-1]),
                max_tree_depth=int(tree.max()) if tree is not None else None, share_tree_depth_ge_8=float((tree >= 8).mean()) if tree is not None else None,
                max_rhat_split=rh, min_ess_bulk=eb, min_ess_tail=et, wall_seconds=round(wall, 1),
                bfmi=float(np.min(np.asarray(az.bfmi(tr)))), rhat_note="split r_hat of the single chain (ArviZ rank-normalised, 4 sub-chains)")
    keep = np.arange(1, 2000, 2)[:D]  # every second draw: 1,000 datasets
    g = lambda n: post[n].to_numpy()[0][keep]
    return dict(c=g("capability"), d=g("difficulty"), a=g("slope"), kap=g("kappa")), diag, tr


if __name__ == "__main__":
    res = {"n_datasets": D, "n_cells": int(len(df)), "seed": "numpy SeedSequence(20261113).spawn(3): stream 0 Epoch, 1 PR (as W1), 2 simulated y for J; PyMC NUTS seeds 20261118 (J) and 20261119 (Epoch sampler check)"}
    fig = {}
    for k, kind in enumerate(["epoch", "reference"]):
        rng = np.random.default_rng(ss[k]); rows = []
        for _ in range(D):
            c, d, a, kap = sim(rng, kind); rows.append(stats(*observe(rng, c, d, a, kap)))
        res[kind], fig[kind] = summarise(rows)
    old = json.loads(Path("runs/W/W1/prior_predictive.json").read_text())
    res["regenerated_W1_matches_stored"] = bool(all(old[k][q] == res[k][q] for k in ("epoch", "reference") for q in ("clip_bound_share", "mid_range_share", "n_datasets_mid_ge_015")))
    # J by NUTS
    dr, diag, _ = nuts_prior(True, 20261118)
    rng = np.random.default_rng(ss[2]); rows = []
    for i in range(D):
        rows.append(stats(*observe(rng, dr["c"][i], dr["d"][i], dr["a"][i], dr["kap"][i])))
    res["J"], fig["J"] = summarise(rows); res["J_sampler"] = diag
    res["J_criterion_descriptive"] = criteria(res["J"]); res["J_would_pass_PR_criterion"] = all(res["J_criterion_descriptive"].values())
    # sampler validation: NUTS on Epoch's flat prior (no potential) against the direct simulation
    de, diag_e, _ = nuts_prior(False, 20261119)
    rng = np.random.default_rng(ss[2]); rows = [stats(*observe(rng, de["c"][i], de["d"][i], de["a"][i], de["kap"][i])) for i in range(D)]
    res["epoch_by_NUTS"], _ = summarise(rows); res["epoch_by_NUTS_sampler"] = diag_e
    # prior summaries of c and d under J and Epoch's prior (NUTS)
    res["parameter_spread"] = {nm: dict(sd_c=float(x["c"].std()), sd_d=float(x["d"].std()), share_abs_c_gt_25=float((np.abs(x["c"]) > 25).mean()),
                                        median_abs_c=float(np.median(np.abs(x["c"]))), sd_log_slope=float(np.log(x["a"]).std())) for nm, x in (("J", dr), ("epoch_NUTS", de))}
    (OUT / "prior_predictive_J.json").write_text(json.dumps(res, indent=1))
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    f, ax = plt.subplots(1, 2, figsize=(9, 3.5))
    for kind, col, lab in (("epoch", "tab:red", "Epoch's flat priors"), ("reference", "tab:blue", "reference prior PR"), ("J", "tab:green", "Jeffreys prior J")):
        ax[0].hist(fig[kind][0], 40, alpha=.6, color=col, label=lab); ax[1].hist(fig[kind][1], 40, alpha=.6, color=col)
    ax[0].set_xlabel("share of scores at the clip bounds"); ax[1].set_xlabel("share of scores in [0.1, 0.9]"); ax[0].legend(fontsize=8)
    f.tight_layout(); f.savefig(OUT / "fig_prior_predictive_J.png", dpi=110)
    print(json.dumps({k: res[k] for k in ("regenerated_W1_matches_stored", "epoch", "reference", "J", "J_criterion_descriptive", "epoch_by_NUTS", "parameter_spread")}, indent=1))
    print(json.dumps(res["J_sampler"], indent=1)); print(json.dumps(res["epoch_by_NUTS_sampler"], indent=1))
