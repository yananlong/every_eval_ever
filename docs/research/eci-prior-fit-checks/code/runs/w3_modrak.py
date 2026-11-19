"""W3M (M13): Modrak-style rank tests on the finished W3 refits. Rerunnable; no sampling.

  python3 runs/w3_modrak.py --selftest            toy models (numpy only): calibrated, autocorrelated, miscalibrated, data-ignoring, posterior-drawn truth
  python3 runs/w3_modrak.py [--gens null,2d,...]  rank tests on every finished, converged replicate of runs/W/W3 (read only), written to runs/W/W3M

Quantities per replicate: ECI, EDI, slope, sigma, hyperparameters; joint and per-benchmark log-likelihood; mean residual (overall and per benchmark);
Pearson dispersion; class summaries. Ranks use draws thinned to their ESS, randomised ties, ECDF-difference gamma test beside the chi-squared test.
The output is labelled interim while fewer than the planned replicates of any generator are finished.
"""
import sys, json, time, argparse, warnings
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
warnings.filterwarnings("ignore")
import numpy as np
from lib import sbc_modrak as sm_

log = lambda *a: print(time.strftime("%H:%M:%S"), *a, flush=True)
EPS = 1e-3
TITLES = {"eci": "ECI (non-anchor models)", "edi": "EDI (benchmarks)", "slope": "slope", "sigma": "sigma", "hyper": "hyperparameters",
          "loglik_joint": "joint log-likelihood", "loglik_bench": "per-benchmark log-likelihood", "resid_overall": "mean residual",
          "resid_bench": "per-benchmark mean residual", "pearson_overall": "Pearson dispersion", "class_summaries": "class summaries"}


# ================================================================= toy validation (numpy only)
def _ar1(rng, mean, sd, L, phi):
    """Stationary AR(1) draws with marginal N(mean, sd^2); mean, sd shape (R,). Returns (R, L)."""
    z = np.empty((len(mean), L)); z[:, 0] = rng.standard_normal(len(mean))
    for t in range(1, L): z[:, t] = phi * z[:, t - 1] + np.sqrt(1 - phi ** 2) * rng.standard_normal(len(mean))
    return mean[:, None] + sd[:, None] * z


def _toy_a(rng, R, L, phi, thin, n=10):
    """Normal mean, N(0,1) prior, n unit-variance observations, exact posterior; draws iid (phi=0) or AR(1). Quantities: theta, log-lik, mean residual."""
    th = rng.standard_normal(R); y = th[:, None] + rng.standard_normal((R, n)); yb = y.mean(1)
    P = 1 + n; m = n * yb / P; s = np.full(R, 1 / np.sqrt(P))
    D = _ar1(rng, m, s, L, phi)
    ll = lambda t: -0.5 * ((y[:, None, :] - t[:, :, None]) ** 2).sum(2)
    qs = {"theta": (D, th[:, None] * np.ones((1, 1))), "loglik": (ll(D), ll(th[:, None])), "resid": (yb[:, None] - D, (yb - th)[:, None])}
    u = {}
    for k, (d, t) in qs.items():
        u[k] = np.empty(R)
        for r in range(R):
            st = sm_.thin_stride(sm_.ess_bulk(d[r]), L) if thin else 1
            u[k][r] = sm_.randomised_rank(d[r], t[r, 0], rng, st)
    return u


def _nig_draw(rng, an, bn, mun, kn, L):
    s2 = bn[:, None] / rng.gamma(an, size=(len(bn), L)) if np.ndim(an) == 0 else bn[:, None] / rng.gamma(an[:, None], size=(len(bn), L))
    return mun[:, None] + np.sqrt(s2 / kn) * rng.standard_normal(s2.shape), s2


def _toy_b(rng, R, L, variant, n=10, a0=3.0, b0=2.0, k0=1.0):
    """Normal-inverse-gamma model. Posterior variants: correct, overconfident (mu sd x0.6), ignores_data (posterior = prior), sigma_prior_only
    (sigma^2 from its prior, mu from the correct conditional). Quantities: mu, log sigma^2, log-likelihood, mean residual."""
    s2t = b0 / rng.gamma(a0, size=R); mut = np.sqrt(s2t / k0) * rng.standard_normal(R)
    y = mut[:, None] + np.sqrt(s2t)[:, None] * rng.standard_normal((R, n)); yb = y.mean(1); ss = ((y - yb[:, None]) ** 2).sum(1)
    kn = k0 + n; mun = n * yb / kn; an = a0 + n / 2; bn = b0 + 0.5 * (ss + k0 * n * yb ** 2 / kn)
    if variant == "correct": mu, s2 = _nig_draw(rng, an, bn, mun, kn, L)
    elif variant == "overconfident":
        mu, s2 = _nig_draw(rng, an, bn, mun, kn, L); mu = mun[:, None] + 0.6 * (mu - mun[:, None])
    elif variant == "ignores_data": mu, s2 = _nig_draw(rng, np.full(R, a0), np.full(R, b0), np.zeros(R), k0, L)
    elif variant == "sigma_prior_only":
        s2 = b0 / rng.gamma(a0, size=(R, L)); mu = mun[:, None] + np.sqrt(s2 / kn) * rng.standard_normal((R, L))
    ll = lambda m, v: -0.5 * (n * np.log(2 * np.pi * v) + (ss[:, None] + n * (yb[:, None] - m) ** 2) / v)
    qs = {"mu": (mu, mut[:, None]), "log_sigma2": (np.log(s2), np.log(s2t)[:, None]), "loglik": (ll(mu, s2), ll(mut[:, None], s2t[:, None])),
          "resid": (yb[:, None] - mu, (yb - mut)[:, None])}
    return {k: np.array([sm_.randomised_rank(d[r], t[r, 0], rng, sm_.thin_stride(sm_.ess_bulk(d[r]), L)) for r in range(R)]) for k, (d, t) in qs.items()}


def _toy_c(rng, R, L, n=2, ybar_obs=1.2):
    """Truth drawn from the posterior given y_obs (n units, mean ybar_obs); refit on y_sim alone (W3 design) or on y_obs + y_sim (posterior SBC)."""
    from scipy.stats import norm
    P = 1 + n; mo = n * ybar_obs / P; so = 1 / np.sqrt(P)
    th = mo + so * rng.standard_normal(R); ys = th + rng.standard_normal(R) / np.sqrt(n)     # ybar of the n simulated values
    out = {}
    m1 = n * ys / P; D1 = m1[:, None] + so * rng.standard_normal((R, L))
    P2 = 1 + 2 * n; m2 = n * (ys + ybar_obs) / P2; D2 = m2[:, None] + rng.standard_normal((R, L)) / np.sqrt(P2)
    for k, D in (("y_sim_only", D1), ("y_obs_plus_y_sim", D2)):
        out[k] = np.array([sm_.randomised_rank(D[r], th[r], rng, 1) for r in range(R)])
    w = n / P; mu_ = (1 - w) * mo / so; sd_ = np.sqrt(1 - w + w * w)
    out["analytic_c90_y_sim_only"] = float(norm.cdf((1.645 - mu_) / sd_) - norm.cdf((-1.645 - mu_) / sd_))
    out["analytic_mean_u_y_sim_only"] = float(norm.cdf(mu_ / np.sqrt(1 + sd_ ** 2)))
    return out


def selftest(out):
    rng = np.random.default_rng(20261118); res = {}
    # size of the tests under calibration: iid and thinned AR(1), 200 meta-replicates of R = 100
    meta, R, L = 200, 100, 400
    def rej(phi, thin):
        pg = {k: [] for k in ("theta", "loglik", "resid")}; pc = {k: [] for k in pg}
        for _ in range(meta):
            u = _toy_a(rng, R, L, phi, thin)
            for k in pg: pg[k].append(sm_.gamma_test(u[k])[1]); pc[k].append(sm_.scalar_summary(u[k])["chi2_p"])
        return {k: dict(gamma_reject_05=float(np.mean(np.array(pg[k]) < .05)), chi2_reject_05=float(np.mean(np.array(pc[k]) < .05))) for k in pg}
    res["A_calibrated_iid"] = rej(0.0, True)
    res["A_autocorrelated_phi0.9_thinned"] = rej(0.9, True)
    res["A_autocorrelated_phi0.9_unthinned"] = rej(0.9, False)
    res["A_thinning_matters_R1500_phi0.9_gamma_p_6_seeds"] = {t: [round(sm_.gamma_test(_toy_a(rng, 1500, L, 0.9, t == "thinned")["theta"])[1], 4) for _ in range(6)] for t in ("thinned", "unthinned")}
    import pandas as pd
    dfo = pd.DataFrame({"model_id": ["a", "b", "a"], "benchmark_id": [1, 1, 2], "performance": [.1, .2, .3]}); da = sm_.augment(dfo, [.4, .5, .6])
    res["augment_check"] = dict(rows=len(da), same_cells=bool((da.iloc[:3][["model_id", "benchmark_id"]].values == da.iloc[3:][["model_id", "benchmark_id"]].values).all()),
                                first_appearance_order_kept=list(da["model_id"].unique()) == ["a", "b"], obs_unchanged=da["performance"].iloc[:3].tolist() == [.1, .2, .3], sim_part=da["performance"].iloc[3:].tolist() == [.4, .5, .6])
    res["A_ess_check"] = {}
    for phi in (0.0, 0.5, 0.9):
        x = _ar1(rng, np.zeros(200), np.ones(200), 400, phi); e = np.mean([sm_.ess_bulk(r) for r in x])
        res["A_ess_check"][str(phi)] = dict(mean_ess=float(e), theory=float(400 * (1 - phi) / (1 + phi)), mean_stride=float(np.mean([sm_.thin_stride(sm_.ess_bulk(r), 400) for r in x])))
    try:
        import arviz_stats  # noqa: F401
        from arviz_stats import ess as _ess
        x = _ar1(rng, np.zeros(1), np.ones(1), 4000, 0.5)[0]
        res["A_ess_check"]["arviz_stats_single_series_phi0.5_L4000"] = dict(ours=sm_.ess_bulk(x) * 1.0, arviz_stats=float(np.asarray(_ess(x[None, :], method="bulk"))), theory=4000 / 3)
    except Exception as e:  # reported, not fatal
        res["A_ess_check"]["arviz_stats_crosscheck"] = f"skipped: {type(e).__name__}"
    # B: one run per variant, R = 200
    res["B_normal_inverse_gamma_R200"] = {}
    for var in ("correct", "overconfident", "ignores_data", "sigma_prior_only"):
        u = _toy_b(rng, 200, 400, var)
        res["B_normal_inverse_gamma_R200"][var] = {k: dict(gamma_p=sm_.scalar_summary(v)["gamma_p"], chi2_p=sm_.scalar_summary(v)["chi2_p"], c90=sm_.scalar_summary(v)["share_central90"]) for k, v in u.items()}
    # B correct: size over 100 meta-replicates R = 100
    sz = {k: [] for k in ("mu", "log_sigma2", "loglik", "resid")}
    for _ in range(100):
        u = _toy_b(rng, 100, 400, "correct")
        for k in sz: sz[k].append(sm_.gamma_test(u[k])[1])
    res["B_correct_size_100x"] = {k: float(np.mean(np.array(v) < .05)) for k, v in sz.items()}
    # C: truth from the posterior given y_obs
    c = _toy_c(rng, 2000, 1000); rc = {}
    for k in ("y_sim_only", "y_obs_plus_y_sim"):
        s = sm_.scalar_summary(c[k]); rc[k] = dict(gamma_p=s["gamma_p"], chi2_p=s["chi2_p"], c90=s["share_central90"], mean_u=s["mean_u"])
    rc["analytic_c90_y_sim_only"] = c["analytic_c90_y_sim_only"]; rc["analytic_mean_u_y_sim_only"] = c["analytic_mean_u_y_sim_only"]; res["C_truth_from_posterior_R2000"] = rc
    Path(out).mkdir(parents=True, exist_ok=True)
    (Path(out) / "selftest.json").write_text(json.dumps(res, indent=1)); return res


# ================================================================= analysis of W3 replicates
def finished(w3, gen):
    reps = []
    for p in sorted((w3 / "rep").glob(f"{gen}_*.json"), key=lambda p: int(p.stem.split("_")[1])):
        try: j = json.loads(p.read_text())
        except Exception: continue
        r = int(p.stem.split("_")[1])
        if j.get("converged") and (w3 / "rep" / f"{gen}_{r}.nc").exists() and (w3 / "truth" / f"{gen}_{r}.npz").exists(): reps.append((r, j))
    return reps


def main(a):
    import xarray as xr
    from lib import data, generators as G, ppc_checks as ppc
    w3, out = Path(a.w3), Path(a.out); out.mkdir(parents=True, exist_ok=True)
    df = data.fit_input(); scores = data.read_member(data.SCORES); pat = G.Pattern(df, scores)
    names = [str(x) for x in xr.open_datatree(Path(a.w2) / "seed12345.nc")["posterior"].to_dataset()["model"].values]
    low, high = names.index("Claude 3.5 Sonnet"), names.index("GPT-5")
    el = ppc.Elig(df, scores) if a.verify else None
    all_res = {}; counts = {}
    for gen in a.gens.split(","):
        reps = finished(w3, gen); counts[gen] = dict(used=len(reps), planned=G.REPS[gen]); per = []
        if not reps: continue
        for r, j in reps:
            ds = xr.open_dataset(w3 / "rep" / f"{gen}_{r}.nc").load(); draws = {k: ds[k].values for k in ds.data_vars if k != "log_slope"}
            z = np.load(w3 / "truth" / f"{gen}_{r}.npz"); truth = {k: z[k] for k in z.files}
            y, _ = G.simulate(gen, r, truth, pat); yc = np.clip(y, EPS, 1 - EPS)
            if a.verify and not per:
                rq = ppc.residual_quantities(draws, el); T, _, _ = ppc.stats(yc, rq, el)
                dev = max(abs(T[k] - j["T"][k]) / (abs(j["T"][k]) + 1e-12) for k in T); log(gen, r, "regenerated-data check: max relative difference in T1-T7 =", dev); assert dev < 1e-8
            rng = np.random.default_rng(G.seed_of("modrak:" + gen, r))
            per.append(sm_.replicate_ranks(draws, truth, yc, pat.mi, pat.bi, pat.K, low, high, rng, thin=not a.no_thin))
        res, figU = sm_.aggregate(per)
        # the three data-dependent one-number quantities share a panel
        all_res[gen] = dict(n_replicates=len(per), replicates=[r for r, _ in reps], quantities=res)
        np.savez_compressed(out / f"ranks_{gen}.npz", **{c: figU[c][0] for c in figU})
        _figure(out, gen, figU, len(per))
    planned_done = all(counts[g]["used"] >= counts[g]["planned"] for g in counts)
    meta = dict(interim=not planned_done, counts=counts, thinning=not a.no_thin, written=time.strftime("%Y-%m-%d %H:%M:%S"),
                caveat="truth drawn from the W2 posterior and the refit uses y_sim only; ranks are not exactly uniform even when everything is exact (selftest C)")
    (out / "modrak.json").write_text(json.dumps(dict(meta=meta, results=all_res), indent=1, default=float))
    _summary(out, meta, all_res); log("done", json.dumps(counts))


def _figure(out, gen, figU, R):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    classes = [c for c in TITLES if c in figU and c not in ("loglik_joint", "resid_overall", "pearson_overall")]
    scal = np.stack([figU[c][0][:, 0] for c in ("loglik_joint", "resid_overall", "pearson_overall") if c in figU], 1)
    fig, axs = plt.subplots(3, 3, figsize=(12, 10)); axs = axs.ravel(); i = 0
    for c in classes:
        sm_.plot_ecdf_diff(axs[i], figU[c][0], title=TITLES[c], labels=figU[c][1] if figU[c][0].shape[1] < 8 else None); i += 1
    sm_.plot_ecdf_diff(axs[i], scal, labels=["joint log-lik", "mean residual", "Pearson dispersion"], title="data-dependent scalars")
    for k in range(i + 1, 9): axs[k].axis("off")
    fig.suptitle(f"W3M ECDF-difference plots, generator {gen} ({R} replicates)", fontsize=11); fig.tight_layout()
    fig.savefig(out / f"ecdf_{gen}.png", dpi=90); plt.close(fig)


def _summary(out, meta, res):
    L = [f"# W3M summary ({'INTERIM' if meta['interim'] else 'final'})", "", f"Written {meta['written']}. Replicates used per generator: " + ", ".join(f"{g} {c['used']} of {c['planned']}" for g, c in meta["counts"].items()) + ".", "",
         f"Thinning to ESS: {meta['thinning']}. Caveat: {meta['caveat']}. gamma p-values come from 20,000 simulated uniform samples, so the smallest reportable p is 5e-5; the Bonferroni column is p x P and floors at 5e-5 x P. Pearson chi-squared has fewer than 5 expected per bin when R < 50 and is then only indicative.", ""]
    for g, r in res.items():
        L += [f"## Generator {g} ({r['n_replicates']} replicates)", "", "| Quantity | P | gamma p (scalar) or min gamma p x P | gamma flagged | chi2 p (scalar) or min chi2 p | chi2 flagged | central 90% share | share u<0.05 / u>0.95 | mean u | median stride |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
        for c, s in r["quantities"].items():
            if s["kind"] == "scalar": L.append(f"| {TITLES[c]} | 1 | {s['gamma_p']:.3g} | | {s['chi2_p']:.3g} | | {s['share_central90']:.2f} | {s['share_below05']:.2f} / {s['share_above95']:.2f} | {s['mean_u']:.2f} | {s['median_stride']:.0f} |")
            else: L.append(f"| {TITLES[c]} | {s['P']} | {s['gamma_p_bonferroni']:.3g} | {s['gamma_n_flagged']} | {s['chi2_min_p']:.3g} | {s['chi2_n_flagged']} | {s['share_central90']:.2f} | {s['share_below05']:.2f} / {s['share_above95']:.2f} | {s['mean_u']:.2f} | {s['median_stride']:.0f} |")
        L.append("")
    (out / "summary.md").write_text("\n".join(L))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true"); ap.add_argument("--w3", default="runs/W/W3"); ap.add_argument("--w2", default="runs/W/W2")
    ap.add_argument("--out", default="runs/W/W3M"); ap.add_argument("--gens", default="null,2d,offset,shape,disp,drift")
    ap.add_argument("--no-thin", action="store_true"); ap.add_argument("--verify", action="store_true", help="recompute T1-T7 on the first replicate of each generator to check the regenerated data")
    a = ap.parse_args()
    if a.selftest: print(json.dumps(selftest(a.out), indent=1))
    else: main(a)
