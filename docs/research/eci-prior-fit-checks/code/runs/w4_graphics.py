"""W4G (M5, M6): graphical posterior predictive checks and effect sizes for one fit, plus randomised LOO-PIT. Read only; no sampling.

  runs/.venv/bin/python runs/w4_graphics.py [--post runs/W/W2/seed12345.nc] [--null runs/W/W3] [--out runs/W/W4G]

Run from the v11 directory. Uses 400 evenly spaced draws for the replicated datasets and the check statistics (as M5), all draws for LOO-PIT.
The calibrated p-values use whatever converged G-null replicates exist in --null and are labelled interim below 150.
"""
import sys, json, time, argparse, warnings
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
warnings.filterwarnings("ignore")
import numpy as np, xarray as xr
from scipy.special import logsumexp
from lib import data, ppc_checks as ppc, ppc_graphics as pg, sbc_modrak as sm_

EPS = 1e-3
log = lambda *a: print(time.strftime("%H:%M:%S"), *a, flush=True)


def main(a):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    import arviz_stats as azs
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    df = data.fit_input(); scores = data.read_member(data.SCORES); el = ppc.Elig(df, scores)
    t = xr.open_datatree(a.post); post = t["posterior"].to_dataset()
    pooled = {v: post[v].stack(s=("chain", "draw")).transpose("s", ...).to_numpy() for v in ("capability", "difficulty", "slope", "sigma")}
    y = np.clip(df["performance"].to_numpy(float), EPS, 1 - EPS)
    assert np.allclose(np.clip(t["observed_data"]["obs"].values, EPS, 1 - EPS), y), "fit data differ from the fit input"
    th = {k: ppc.thin(v) for k, v in pooled.items()}; rq = ppc.residual_quantities(th, el); mu, kap = ppc.mu_kappa(th, el)
    rng = np.random.default_rng(20261118); Yrep = pg.simulate_yrep(mu, kap, rng)
    null_T = [json.loads(p.read_text())["T"] for p in Path(a.null).glob("rep/null_*.json") if json.loads(p.read_text())["converged"]]
    bn = np.array(el.bench_names, dtype=object); N = len(y)

    # ---- effect sizes, raw and calibrated p
    g = pg.global_checks(y, Yrep, rq, el, null_T or None); log("global checks done; null replicates", len(null_T))
    obs_b = pg.bench_statistics(y[None], rq, el); rep_b = pg.bench_statistics(Yrep, rq, el)
    bench = {k: dict(effect=pg.effect_size(obs_b[k][0], rep_b[k])) for k in obs_b}
    bres = {}
    for k in bench:
        e = bench[k]["effect"]; o = np.argsort(-np.abs(e))
        bres[k] = [dict(benchmark=str(bn[el.t1_bench[j]]), n_rows=int(len(el.rows_of_bench[el.t1_bench[j]])), observed=float(obs_b[k][0][j]), rep_mean=float(rep_b[k][:, j].mean()),
                        rep_sd=float(rep_b[k][:, j].std(ddof=1)), effect_size=float(e[j])) for j in o[:10]]
    # ---- figures: densities
    big = np.argsort(-np.array([len(r) for r in el.rows_of_bench]))[:15]
    fig, axs = plt.subplots(4, 4, figsize=(13, 10)); axs = axs.ravel()
    pg.plot_density(axs[0], y, Yrep, title="all rows", rng=rng)
    for ax, b in zip(axs[1:], big): pg.plot_density(ax, y, Yrep, rows=el.rows_of_bench[b], title=f"{str(bn[b])[:22]} (n={len(el.rows_of_bench[b])})", rng=rng)
    fig.suptitle("Observed score density (black) and 40 replicated datasets (grey), interior scores; title: clip-bound share observed vs replicated", fontsize=10); fig.tight_layout(); fig.savefig(out / "fig_density.png", dpi=80); plt.close(fig)
    # ---- figures: global statistics
    fig, axs = plt.subplots(3, 3, figsize=(11, 8)); axs = axs.ravel()
    for ax, k in zip(axs, ppc.TNAMES + ["boundary_count", "mid_range_share"]):
        pg.plot_rep_hist(ax, g[k]["_rep"], g[k]["observed"], f"{k}: effect {g[k]['effect_size']:+.2f} SD, raw p {g[k].get('raw_p', g[k].get('raw_p_upper')):.3f}")
    for ax in axs[9:]: ax.axis("off")
    fig.suptitle("Replicated (grey) against observed (red), residual quantities fixed at the real-data fit", fontsize=10); fig.tight_layout(); fig.savefig(out / "fig_global_stats.png", dpi=80); plt.close(fig)
    # ---- figures: per-benchmark statistic histograms (the four benchmarks with the largest |effect| for each statistic)
    fig, axs = plt.subplots(4, 4, figsize=(13, 10))
    for i, k in enumerate(("mean_score", "boundary_count", "Q_b", "dispersion")):
        e = bench[k]["effect"]
        for jx, j in enumerate(np.argsort(-np.abs(e))[:4]):
            pg.plot_rep_hist(axs[i, jx], rep_b[k][:, j], obs_b[k][0][j], f"{k}, {str(bn[el.t1_bench[j]])[:20]}: {e[j]:+.1f} SD")
    fig.suptitle("Per-benchmark statistics (benchmarks with at least 20 rows): the 4 largest effects per statistic", fontsize=10); fig.tight_layout(); fig.savefig(out / "fig_bench_stats.png", dpi=80); plt.close(fig)

    # ---- LOO and randomised LOO-PIT (all draws)
    r = azs.loo(t, pointwise=True)
    lw = np.asarray(r.log_weights.transpose("chain", "draw", ...).values).reshape(-1, N); lw = lw - logsumexp(lw, axis=0, keepdims=True)
    k = np.asarray(r.pareto_k.values).ravel()
    muA, kapA = ppc.mu_kappa(pooled, el)
    u = pg.loo_pit_randomised(lw, muA, kapA, y, rng)
    summ = dict(all_rows=pg.pit_summary(u), pareto_k_le_0_7=pg.pit_summary(u[k <= 0.7]), pareto_k_gt_0_7_rows=int((k > 0.7).sum()))
    nb = [b for b in range(el.K) if len(el.rows_of_bench[b]) >= 30]; pb = {}
    for b in nb: pb[str(bn[b])] = pg.pit_summary(u[el.rows_of_bench[b]])
    thr = 0.01 / len(nb); pb_flag = [n for n, s in pb.items() if s["gamma_p"] < thr]
    fig, axs = plt.subplots(3, 4, figsize=(13, 9)); axs = axs.ravel()
    gt = sm_.GammaTest(N); lo, hi = gt.band()
    for ax, (uu, ti) in zip(axs[:2], ((u, "all rows"), (u[k <= 0.7], "Pareto k <= 0.7"))):
        sm_.plot_ecdf_diff(ax, uu[:, None], title=f"LOO-PIT, {ti}")
    for ax, b in zip(axs[2:], big[:10]):
        sm_.plot_ecdf_diff(ax, u[el.rows_of_bench[b]][:, None], title=f"{str(bn[b])[:20]}, gamma p {pb[str(bn[b])]['gamma_p']:.3f}" if str(bn[b]) in pb else str(bn[b]))
    fig.suptitle("Randomised LOO-PIT, ECDF difference with 95% simultaneous bands", fontsize=10); fig.tight_layout(); fig.savefig(out / "fig_loo_pit.png", dpi=80); plt.close(fig)
    fig, ax = plt.subplots(figsize=(5, 3.5)); ax.hist(u, bins=20, density=True, color="0.7"); ax.axhline(1, color="k", lw=.5); ax.set_title("LOO-PIT histogram (randomised)", fontsize=9)
    fig.tight_layout(); fig.savefig(out / "fig_loo_pit_hist.png", dpi=80); plt.close(fig)

    clean = {kk: {k2: v for k2, v in vv.items() if k2 != "_rep"} for kk, vv in g.items()}
    res = dict(post=str(a.post), n_draws_ppc=int(mu.shape[0]), n_draws_loo=int(muA.shape[0]), n_null_replicates=len(null_T), calibrated_p_interim=len(null_T) < 150,
               elpd_loo=float(r.elpd), p_loo=float(r.p), pareto_k_gt_0_7=int((k > 0.7).sum()), global_checks=clean, benchmark_effects_top10=bres,
               loo_pit=dict(summary=summ, per_benchmark_n=len(nb), per_benchmark_bonferroni_level=thr, per_benchmark_flagged=pb_flag,
                            per_benchmark={n: dict(n=s["n"], gamma_p=s["gamma_p"], share_central90=s["share_central90"], mean=s["mean"]) for n, s in pb.items()}))
    (out / "ppc_graphics.json").write_text(json.dumps(res, indent=1, default=float))
    write_summary(out, res); log("done")


def write_summary(out, r):
    L = [f"# W4G summary ({'INTERIM calibrated p' if r['calibrated_p_interim'] else 'final'})", "",
         f"Posterior: `{Path(r['post']).name}`. Replicated datasets and statistics: {r['n_draws_ppc']} draws; LOO-PIT: {r['n_draws_loo']} draws. elpd_loo {r['elpd_loo']:.2f}, p_loo {r['p_loo']:.1f}, Pareto k above 0.7 for {r['pareto_k_gt_0_7']} rows.",
         f"Calibrated p-values use {r['n_null_replicates']} G-null replicates (planned 199, minimum 150 for a verdict); with fewer, the smallest possible p is 1/(R + 1) and no rejection at 0.01 is possible.", "",
         "## Global checks (effect size = (observed - mean replicated) / SD replicated)", "",
         "| Check | Observed | Replicated mean (SD) | Effect size | Raw in-sample p | Effect vs null SD | Calibrated p | Max-T adjusted p |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for k, v in r["global_checks"].items():
        rp = v.get("raw_p", None); rp = f"{rp:.3f}" if rp is not None else f"{v['raw_p_upper']:.3f} (upper) / {v['raw_p_lower']:.3f} (lower)"
        L.append(f"| {k} | {v['observed']:.4g} | {v['rep_mean']:.4g} ({v['rep_sd']:.3g}) | {v['effect_size']:+.2f} | {rp} | " +
                 (f"{v['effect_size_vs_null']:+.2f} | {v['p_calibrated_unadjusted']:.3f} | {v['p_calibrated_maxT']:.3f} |" if "p_calibrated_maxT" in v else " | | |"))
    L += ["", "## Largest per-benchmark effects (benchmarks with at least 20 rows)", ""]
    for k, rows in r["benchmark_effects_top10"].items():
        L += [f"**{k}**", "", "| Benchmark | Rows | Observed | Replicated mean (SD) | Effect size |", "| --- | --- | --- | --- | --- |"]
        L += [f"| {x['benchmark']} | {x['n_rows']} | {x['observed']:.4g} | {x['rep_mean']:.4g} ({x['rep_sd']:.3g}) | {x['effect_size']:+.2f} |" for x in rows[:5]] + [""]
    s = r["loo_pit"]["summary"]; a_ = s["all_rows"]; b_ = s["pareto_k_le_0_7"]
    L += ["## Randomised LOO-PIT", "", f"All rows ({a_['n']}): mean {a_['mean']:.3f}, SD {a_['sd']:.3f} (uniform 0.289), share below 0.05 / above 0.95 = {a_['share_below05']:.3f} / {a_['share_above95']:.3f}, gamma {a_['gamma']:.4f}, p {a_['gamma_p']:.4g}.",
          f"Rows with Pareto k at most 0.7 ({b_['n']}): mean {b_['mean']:.3f}, SD {b_['sd']:.3f}, share below 0.05 / above 0.95 = {b_['share_below05']:.3f} / {b_['share_above95']:.3f}, gamma p {b_['gamma_p']:.4g}.",
          f"Per benchmark ({r['loo_pit']['per_benchmark_n']} with at least 30 rows), gamma test flagged at {r['loo_pit']['per_benchmark_bonferroni_level']:.2g}: {', '.join(r['loo_pit']['per_benchmark_flagged']) or 'none'}.", ""]
    (out / "summary.md").write_text("\n".join(L))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--post", default="runs/W/W2/seed12345.nc"); ap.add_argument("--null", default="runs/W/W3"); ap.add_argument("--out", default="runs/W/W4G")
    main(ap.parse_args())
