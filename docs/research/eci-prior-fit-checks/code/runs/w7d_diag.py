"""W7 diagnostics for G3_ta99 (exploratory): where the fit still misses. Writes small PNG, csv and json files to
runs/W/W7/diag/. Posterior analysis uses ArviZ (az.loo pointwise, az.loo_pit, az.plot_khat, az.plot_ecdf_pit,
az.plot_forest, az.summary); matplotlib is used for layout and for what ArviZ lacks (heatmaps, scatter panels).
T1-T7 keep the frozen definitions in lib/ppc_checks.py. Envelopes are of two kinds and are labelled as such:
  PP    posterior predictive draws from the fit with the residual quantities held fixed (no refit);
  REP   the stored maxima of the 88 converged model-true replicates of G3_ta99 (refitted), a family-wise threshold.
Usage: w7d_diag.py [part ...]   parts: loo pit corr zero resid otis forest (default: all)"""
import sys, json, io, zipfile, warnings
from pathlib import Path
sys.path[:0] = ["runs/vendor/eci-public/src", "runs"]; warnings.filterwarnings("ignore")
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np, pandas as pd, xarray as xr, arviz as az
from scipy.cluster.hierarchy import linkage, leaves_list, fcluster
from scipy.spatial.distance import squareform
from scipy import stats as st
import w7d_common as c
from lib import data

OUT = c.DIAG; OUT.mkdir(parents=True, exist_ok=True)
parts = sys.argv[1:] or ["loo", "pit", "corr", "zero", "resid", "otis", "forest"]
NAME, FEATS = "G3_ta99", ("dev", "fam")
B = c.bundle_g3(f"runs/W/W7/{NAME}.nc", FEATS)
df, el, y, z, rq, mu, kap, org = B["df"], B["el"], B["y"], B["z"], B["rq"], B["mu"], B["kap"], B["org"]
M = c.meta(df, el); bn = el.bench_names; sh = [c.short(n) for n in bn]
chat = rq["chat"]; dmean = B["P"]["difficulty"].mean(0)
yr, zr = c.pp_envelope(mu, kap, rq)
REPMAX, NREP = c.rep_maxima(NAME)
res = dict(name=NAME, T=B["T"], n_rep=NREP)
print("T", {k: round(v, 3) for k, v in B["T"].items()}, flush=True)


def save(fig, name, dpi=105):
    p = OUT / name; fig.savefig(p, dpi=dpi, bbox_inches="tight"); plt.close(fig)
    kb = p.stat().st_size / 1024
    if kb > 300: fig.savefig(p, dpi=70, bbox_inches="tight"); kb = p.stat().st_size / 1024
    print(f"wrote {p} {kb:.0f} KB", flush=True)


# ---------------------------------------------------------------- 1. pointwise LOO and Pareto k
if "loo" in parts:
    t0 = xr.open_datatree("runs/W/W2/f0_seed12345.nc"); l0 = az.loo(t0, pointwise=True, var_name="obs")
    e0 = np.asarray(l0.elpd_i).ravel(); e, k = B["elpd_i"], B["k"]
    row = pd.DataFrame(dict(model=df["Model"], benchmark=df["benchmark"], org=org, y=y, mubar=rq["mubar"], z=z, elpd=e,
                            elpd_f0=e0, k=k, pit=B["pit"], date=df["date"]))
    row.to_csv(OUT / "loo_pointwise.csv", index=False, float_format="%.4f")
    def agg(key):
        g = row.groupby(key).agg(n=("elpd", "size"), elpd_sum=("elpd", "sum"), elpd_mean=("elpd", "mean"), gain_vs_f0=("elpd", lambda x: 0.0),
                                 k_gt_0_7=("k", lambda x: int((x > .7).sum())), k_share=("k", lambda x: float((x > .7).mean())),
                                 k_max=("k", "max"), mean_z2=("z", lambda x: float((x ** 2).mean())),
                                 pit_tail=("pit", lambda x: float(((x < .025) | (x > .975)).mean())))
        g["gain_vs_f0"] = (row["elpd"] - row["elpd_f0"]).groupby(row[key]).sum(); return g
    gb, gm, go = agg("benchmark"), agg("model"), agg("org")
    gb.sort_values("elpd_mean").to_csv(OUT / "loo_by_benchmark.csv", float_format="%.3f")
    gm.sort_values("elpd_mean").to_csv(OUT / "loo_by_model.csv", float_format="%.3f")
    go.sort_values("elpd_mean").to_csv(OUT / "loo_by_developer.csv", float_format="%.3f")
    res["loo"] = dict(elpd=float(B["loo"].elpd), se=float(B["loo"].se), p=float(B["loo"].p), k_gt_0_7=int((k > .7).sum()), k_gt_1=int((k > 1).sum()),
                      k_share=float((k > .7).mean()),
                      worst_benchmarks_mean_elpd=gb[gb.n >= 15].sort_values("elpd_mean").head(8).round(3).reset_index().to_dict("records"),
                      most_high_k_benchmarks=gb.sort_values("k_gt_0_7", ascending=False).head(10).round(3).reset_index().to_dict("records"),
                      worst_models_mean_elpd=gm[gm.n >= 6].sort_values("elpd_mean").head(10).round(3).reset_index().to_dict("records"),
                      developers=go[go.n >= 20].sort_values("elpd_mean").round(3).reset_index().to_dict("records"),
                      k_by_rows_per_model=row.assign(nm=row.groupby("model")["k"].transform("size")).assign(
                          band=lambda d: pd.cut(d.nm, [0, 3, 6, 12, 25, 100])).groupby("band")["k"].agg(lambda x: float((x > .7).mean())).round(3).astype(float).rename(str).to_dict(),
                      k_dev_cell_share=float((k[B["ex"]["cell_idx"] >= 0] > .7).mean()), k_nocell_share=float((k[B["ex"]["cell_idx"] < 0] > .7).mean()))
    # ArviZ khat plot
    try:
        pc = az.plot_khat(B["loo"], backend="matplotlib", figure_kwargs=dict(figsize=(9, 3.2)))
        pc.savefig(OUT / "khat_G3_ta99.png", dpi=90); print("wrote khat", (OUT / "khat_G3_ta99.png").stat().st_size // 1024, "KB")
    except Exception as ex_: print("plot_khat failed", repr(ex_)[:300])
    # grid: models by capability (rows), benchmarks by difficulty (columns)
    mo, bo = np.argsort(chat), np.argsort(dmean)
    def grid(v):
        G = np.full((el.M, el.K), np.nan); G[el.mi, el.bi] = v; return G[mo][:, bo]
    fig, ax = plt.subplots(1, 3, figsize=(17, 8.5), gridspec_kw=dict(wspace=0.08))
    for a, (v, ttl, cm, lim) in zip(ax, [(z, "standardised residual z (in-sample)", "RdBu_r", (-3, 3)),
                                         (B["pit"] - .5, "LOO-PIT minus 0.5", "RdBu_r", (-.5, .5)),
                                         (k, "Pareto k (PSIS-LOO)", "viridis", (0, 1.0))]):
        im = a.imshow(grid(v), aspect="auto", cmap=cm, vmin=lim[0], vmax=lim[1], interpolation="nearest")
        a.set_title(ttl, fontsize=10); a.set_xticks(range(el.K)); a.set_xticklabels([sh[b] for b in bo], rotation=90, fontsize=5.5)
        a.set_yticks([]); fig.colorbar(im, ax=a, fraction=0.03, pad=0.01)
    ax[0].set_ylabel("models, least to most capable (top to bottom)")
    fig.suptitle(f"{NAME}: model x benchmark grid; benchmarks ordered easy to hard (left to right)", fontsize=11)
    save(fig, "loo_grid.png", dpi=80)
    # per-benchmark bars
    g = gb.loc[[bn[b] for b in bo]]
    fig, ax = plt.subplots(3, 1, figsize=(13, 8), sharex=True)
    x = np.arange(len(g)); ax[0].bar(x, g.elpd_mean, color="#4477aa"); ax[0].set_ylabel("mean LOO elpd per row")
    ax[1].bar(x, g.gain_vs_f0 / g.n, color="#228833"); ax[1].axhline(0, color="k", lw=.5); ax[1].set_ylabel("gain over F0 per row")
    ax[2].bar(x, g.k_share, color="#cc6677"); ax[2].set_ylabel("share of rows with k > 0.7")
    ax[2].set_xticks(x); ax[2].set_xticklabels([f"{c.short(n)} ({int(v)})" for n, v in zip(g.index, g.n)], rotation=90, fontsize=6.5)
    fig.suptitle(f"{NAME}: PSIS-LOO by benchmark (rows in brackets), easy to hard", fontsize=11); save(fig, "loo_by_benchmark.png", dpi=85)

# ---------------------------------------------------------------- 2. LOO-PIT per benchmark
if "pit" in parts:
    pit = B["pit"]; big = [b for b in np.argsort(dmean) if len(el.rows_of_bench[b]) >= 20]
    rows = []
    for b in range(el.K):
        p = pit[el.rows_of_bench[b]]; n = len(p)
        if n < 8: continue
        # mean PIT (bias: > 0.5 = scores above prediction), variance ratio to 1/12 (> 1 = model too narrow, U shape)
        rows.append(dict(benchmark=bn[b], n=n, pit_mean=p.mean(), mean_z=(p.mean() - .5) / np.sqrt(1 / 12 / n), var_ratio=p.var() * 12,
                         lo_tail=(p < .05).mean(), hi_tail=(p > .95).mean(), ks_p=st.kstest(p, "uniform").pvalue,
                         central50=(np.abs(p - .5) < .25).mean()))
    P = pd.DataFrame(rows).sort_values("ks_p"); P.to_csv(OUT / "loo_pit_by_benchmark.csv", index=False, float_format="%.4f")
    res["pit"] = dict(n_bench=len(P), ks_p_lt_0_01=P[P.ks_p < .01].benchmark.tolist(), ks_p_lt_bonf=P[P.ks_p < .05 / len(P)].benchmark.tolist(),
                      over_dispersed_var_ratio_gt_1_3=P[P.var_ratio > 1.3].benchmark.tolist(),
                      under_dispersed_var_ratio_lt_0_7=P[P.var_ratio < .7].benchmark.tolist(),
                      top=P.head(12).round(4).to_dict("records"), pooled_var_ratio=float(pit.var() * 12),
                      pooled_central50=float((np.abs(pit - .5) < .25).mean()))
    done = False
    try:   # ArviZ small multiples: one variable per benchmark
        ds = xr.Dataset({sh[b].replace(" ", "_"): ((f"o{b}",), pit[el.rows_of_bench[b]]) for b in big})
        dt = xr.DataTree.from_dict({"loo_pit": ds})
        pc = az.plot_ecdf_pit(dt, group="loo_pit", sample_dims=[f"o{b}" for b in big], backend="matplotlib", col_wrap=8,
                              figure_kwargs=dict(figsize=(17, 10.5)))
        fig = pc.viz["figure"].item()
        fig.suptitle(f"{NAME}: LOO-PIT delta-ECDF per benchmark (20 rows or more), easy to hard; band = 95% simultaneous envelope of uniform PIT", fontsize=10)
        pc.savefig(OUT / "loo_pit_by_benchmark.png", dpi=80); done = True
        print("wrote loo_pit_by_benchmark.png (ArviZ)", (OUT / "loo_pit_by_benchmark.png").stat().st_size // 1024, "KB")
    except Exception as ex_:
        print("az.plot_ecdf_pit per benchmark failed, drawing with matplotlib:", repr(ex_)[:300])
    if not done:
        fig, ax = plt.subplots(5, 8, figsize=(17, 10.5), sharex=True, sharey=True); ax = ax.ravel()
        for a, b in zip(ax, big):
            p = np.sort(pit[el.rows_of_bench[b]]); n = len(p); a.plot(p, (np.arange(1, n + 1)) / n - p, color="#4477aa")
            g = np.linspace(0, 1, 50); a.fill_between(g, -2.6 * np.sqrt(g * (1 - g) / n), 2.6 * np.sqrt(g * (1 - g) / n), color="0.85")
            a.axhline(0, color="k", lw=.5); a.set_title(f"{sh[b]} ({n})", fontsize=7)
        fig.suptitle(f"{NAME}: LOO-PIT ECDF minus uniform per benchmark", fontsize=10); save(fig, "loo_pit_by_benchmark.png", dpi=80)

# ---------------------------------------------------------------- 3. residual correlation between benchmarks
if "corr" in parts:
    r = c.pair_r(z, el); R = c.r_matrix(r, el)
    rr = np.array([c.pair_r(zr[s], el) for s in range(zr.shape[0])])              # PP envelope per pair
    lo, hi = np.quantile(rr, [.005, .995], axis=0); out_pp = (r < lo) | (r > hi)
    nsh = np.array([len(ra) for _, _, ra, _ in el.pairs]); q = (nsh - 3) * np.arctanh(np.clip(r, -.999, .999)) ** 2
    thr_rep = float(np.quantile(REPMAX["q"], .95)); out_rep = q > thr_rep
    exp_out = float(((rr < lo) | (rr > hi)).mean() * len(r))
    pairs = pd.DataFrame(dict(a=[bn[a] for a, _, _, _ in el.pairs], b=[bn[b] for _, b, _, _ in el.pairs], n_shared=nsh, r=r, q=q,
                              pp_lo=lo, pp_hi=hi, outside_pp99=out_pp, above_rep_max95=out_rep)).sort_values("q", ascending=False)
    pairs.to_csv(OUT / "resid_corr_pairs.csv", index=False, float_format="%.3f")
    # clustering on benchmarks that have at least 3 eligible pairs
    deg = np.sum(~np.isnan(R), axis=1) - 1; keep = np.where(deg >= 3)[0]
    Rk = np.nan_to_num(R[np.ix_(keep, keep)], nan=0.0); D = 1 - Rk; np.fill_diagonal(D, 0)
    Z = linkage(squareform(D, checks=False), "average"); order = leaves_list(Z); cl = fcluster(Z, 0.75, "distance")
    clusters = {}
    for i, cid in zip(keep, cl): clusters.setdefault(int(cid), []).append(int(i))
    clusters = [v for v in clusters.values() if len(v) >= 2]
    cinfo = []
    Rpp = lambda s: c.r_matrix(rr[s], el)
    for v in sorted(clusters, key=lambda v: -len(v)):
        iu = [(a, b) for i, a in enumerate(v) for b in v[i + 1:] if not np.isnan(R[a, b])]
        if not iu: continue
        mr = float(np.mean([R[a, b] for a, b in iu]))
        mpp = np.array([np.mean([Rpp(s)[a, b] for a, b in iu]) for s in range(0, rr.shape[0], 2)])
        mm = M.iloc[v]
        cinfo.append(dict(members=[bn[i] for i in v], n_pairs=len(iu), mean_r=mr, pp_mean_r_99=[float(np.quantile(mpp, .005)), float(np.quantile(mpp, .995))],
                          years=sorted(mm.year.tolist()), tags=sorted(set(";".join(mm.tags).split(";")) - {""}),
                          styles=sorted(set(mm["style"])), epoch_run=int(mm.epoch_run.sum()), multi_source=int((mm.n_sources >= 5).sum())))
    # eigen-structure of the residual correlation matrix against the PP envelope
    ev = np.linalg.eigvalsh(Rk)[::-1]; evpp = np.array([np.linalg.eigvalsh(np.nan_to_num(Rpp(s)[np.ix_(keep, keep)], nan=0.0))[::-1] for s in range(rr.shape[0])])
    w, V = np.linalg.eigh(Rk); V = V[:, ::-1]
    load = pd.DataFrame(V[:, :3], columns=["pc1", "pc2", "pc3"]); load.insert(0, "benchmark", [bn[i] for i in keep])
    load["year"] = M.year.to_numpy()[keep]; load["style"] = M["style"].to_numpy()[keep]; load["tags"] = M.tags.to_numpy()[keep]
    load["epoch_run"] = M.epoch_run.to_numpy()[keep]; load["n_sources"] = M.n_sources.to_numpy()[keep]
    load.to_csv(OUT / "resid_corr_loadings.csv", index=False, float_format="%.3f")
    old = load.year <= 2022
    res["corr"] = dict(n_pairs=len(r), outside_pp99=int(out_pp.sum()), expected_outside_pp99=exp_out, above_rep_max95=int(out_rep.sum()),
                       rep_max95_q=thr_rep, share_abs_r_gt_0_3=float((np.abs(r) > .3).mean()), pp_share_abs_r_gt_0_3=float((np.abs(rr) > .3).mean()),
                       mean_r=float(r.mean()), pp_mean_r=float(rr.mean()),
                       top_pairs=pairs.head(25).round(3).to_dict("records"), clusters=cinfo,
                       eig_top5=ev[:5].tolist(), eig_pp99_top5=np.quantile(evpp, .99, axis=0)[:5].tolist(), eig_pp_median_top5=np.median(evpp, axis=0)[:5].tolist(),
                       n_eig_above_pp99=int((ev > np.quantile(evpp, .99, axis=0)).sum()),
                       pc1_vs_year_spearman=float(st.spearmanr(load.pc1, load.year).statistic),
                       pc1_old_vs_new_mean=[float(load.pc1[old].mean()), float(load.pc1[~old].mean())],
                       pc2_vs_year_spearman=float(st.spearmanr(load.pc2, load.year).statistic),
                       pc_by_style={s: [float(g.pc1.mean()), float(g.pc2.mean()), int(len(g))] for s, g in load.groupby("style")},
                       pc_top={f"pc{j}": dict(pos=load.sort_values(f"pc{j}").benchmark.tail(6).tolist()[::-1], neg=load.sort_values(f"pc{j}").benchmark.head(6).tolist()) for j in (1, 2, 3)},
                       within_between=dict(
                           old_old=float(np.nanmean([R[a, b] for a, b, _, _ in el.pairs if M.year[a] <= 2022 and M.year[b] <= 2022])),
                           new_new=float(np.nanmean([R[a, b] for a, b, _, _ in el.pairs if M.year[a] > 2022 and M.year[b] > 2022])),
                           old_new=float(np.nanmean([R[a, b] for a, b, _, _ in el.pairs if (M.year[a] <= 2022) != (M.year[b] <= 2022)] or [np.nan])),
                           n_old_new=int(sum((M.year[a] <= 2022) != (M.year[b] <= 2022) for a, b, _, _ in el.pairs)),
                           same_style=float(np.mean([R[a, b] for a, b, _, _ in el.pairs if M["style"][a] == M["style"][b]])),
                           diff_style=float(np.mean([R[a, b] for a, b, _, _ in el.pairs if M["style"][a] != M["style"][b]])),
                           both_epoch_run=float(np.mean([R[a, b] for a, b, _, _ in el.pairs if M.epoch_run[a] and M.epoch_run[b]])),
                           share_tag=float(np.mean([R[a, b] for a, b, _, _ in el.pairs if set(M.tags[a].split(";")) & set(M.tags[b].split(";")) - {""}])),
                           no_share_tag=float(np.mean([R[a, b] for a, b, _, _ in el.pairs if not (set(M.tags[a].split(";")) & set(M.tags[b].split(";")) - {""})]))))
    ko = keep[order]; Ro = R[np.ix_(ko, ko)]
    fig, ax = plt.subplots(figsize=(11.5, 10))
    im = ax.imshow(Ro, cmap="RdBu_r", vmin=-.8, vmax=.8, interpolation="nearest"); fig.colorbar(im, ax=ax, fraction=0.035, pad=0.01, label="residual correlation r")
    pos = {int(b): i for i, b in enumerate(ko)}
    for (a, b, _, _), o1, o2 in zip(el.pairs, out_pp, out_rep):
        if a in pos and b in pos and (o1 or o2):
            for (i, j) in ((pos[a], pos[b]), (pos[b], pos[a])):
                ax.plot(j, i, marker="s" if o2 else ".", ms=7 if o2 else 3.5, mfc="none" if o2 else "k", mec="k", mew=1.0)
    lab = [f"{sh[b]} '{str(M.year[b])[2:]}{'*' if M.epoch_run[b] else ''}" for b in ko]
    ax.set_xticks(range(len(ko))); ax.set_xticklabels(lab, rotation=90, fontsize=6.5); ax.set_yticks(range(len(ko))); ax.set_yticklabels(lab, fontsize=6.5)
    ax.set_title(f"{NAME}: residual correlation between benchmarks (pairs sharing 15+ models; blank = not eligible), average-linkage order.\n"
                 f"dot = outside the 99% posterior predictive envelope ({int(out_pp.sum())} of {len(r)} pairs; {exp_out:.1f} expected); "
                 f"square = pair component above the 95th percentile of the largest pair over {NREP} model-true replicates ({int(out_rep.sum())}).\n"
                 "label = benchmark 'release year; * = run by Epoch", fontsize=8.5)
    save(fig, "resid_corr_matrix.png", dpi=88)
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.6))
    ax[0].plot(range(1, 11), ev[:10], "o-", color="#cc3311", label="observed")
    ax[0].fill_between(range(1, 11), np.quantile(evpp, .005, axis=0)[:10], np.quantile(evpp, .995, axis=0)[:10], color="0.8", label="99% posterior predictive")
    ax[0].set_xlabel("component"); ax[0].set_ylabel("eigenvalue of residual correlation matrix"); ax[0].legend(fontsize=8)
    sc = ax[1].scatter(load.pc1, load.pc2, c=load.year, cmap="viridis", s=28)
    for _, rw in load.iterrows():
        if abs(rw.pc1) > .16 or abs(rw.pc2) > .2: ax[1].annotate(c.short(rw.benchmark, 14), (rw.pc1, rw.pc2), fontsize=6.5)
    fig.colorbar(sc, ax=ax[1], label="benchmark release year"); ax[1].set_xlabel("loading on residual component 1"); ax[1].set_ylabel("loading on component 2")
    fig.suptitle(f"{NAME}: eigen-structure of the residual correlation matrix", fontsize=10); save(fig, "resid_corr_eigen.png")

# ---------------------------------------------------------------- 4. mass at 0 and at 1
if "zero" in parts:
    is0, is1 = y <= c.EPS, y >= 1 - c.EPS; r0, r1 = yr <= c.EPS, yr >= 1 - c.EPS
    rows = []
    for b in range(el.K):
        rb = el.rows_of_bench[b]; s0 = r0[:, rb].sum(1); s1 = r1[:, rb].sum(1)
        rows.append(dict(benchmark=bn[b], n=len(rb), zeros=int(is0[rb].sum()), exp_zeros=float(rq["p0"][rb].sum()), pp_zeros_lo=float(np.quantile(s0, .025)),
                         pp_zeros_hi=float(np.quantile(s0, .975)), p_zeros_ge=float((s0 >= is0[rb].sum()).mean()),
                         ones=int(is1[rb].sum()), exp_ones=float(rq["p1"][rb].sum()), pp_ones_lo=float(np.quantile(s1, .025)), pp_ones_hi=float(np.quantile(s1, .975)),
                         p_ones_ge=float((s1 >= is1[rb].sum()).mean()), cb=float(B["comp"]["cb"][b]),
                         near0_obs=float((y[rb] < .02).mean()), near0_pp=float((yr[:, rb] < .02).mean()), near1_obs=float((y[rb] > .98).mean()), near1_pp=float((yr[:, rb] > .98).mean()),
                         sigma=float(B["P"]["sigma"][:, b].mean()), style=M["style"][b], epoch_run=bool(M.epoch_run[b])))
    Zt = pd.DataFrame(rows).sort_values("cb", ascending=False); Zt.to_csv(OUT / "bounds_by_benchmark.csv", index=False, float_format="%.3f")
    thr = float(np.quantile(REPMAX["cb"], .95))
    # do the zeros sit where the model predicts low scores?  mean predicted score of the zero rows
    zrow = pd.DataFrame(dict(benchmark=df["benchmark"], model=df["Model"], mubar=rq["mubar"], p0=rq["p0"], chat=chat[el.mi]))[is0]
    res["bounds"] = dict(zeros=int(is0.sum()), exp_zeros=float(rq["p0"].sum()), ones=int(is1.sum()), exp_ones=float(rq["p1"].sum()),
                         rep_max95_cb=thr, above_rep_max95=Zt[Zt.cb > thr].benchmark.tolist(),
                         top=Zt.head(10).round(3).to_dict("records"),
                         zero_rows_pred_mean_quantiles=[float(v) for v in np.quantile(zrow.mubar, [.1, .5, .9])],
                         zero_rows_pred_gt_0_1=int((zrow.mubar > .1).sum()), zero_by_style=M.groupby("style")[["zeros", "ones", "n"]].sum().to_dict("index"),
                         zero_by_epoch_run=M.groupby("epoch_run")[["zeros", "ones", "n"]].sum().to_dict("index"))
    sel = Zt[(Zt.zeros + Zt.ones > 0) | (Zt.exp_zeros + Zt.exp_ones > 1)].sort_values("zeros")
    fig, ax = plt.subplots(1, 3, figsize=(15, 6.2), gridspec_kw=dict(width_ratios=[1, 1, 1.15], wspace=0.45))
    for a, (o, lo, hi, e_, ttl) in zip(ax, [("zeros", "pp_zeros_lo", "pp_zeros_hi", "exp_zeros", "scores at 0 (at or below 0.001)"),
                                            ("ones", "pp_ones_lo", "pp_ones_hi", "exp_ones", "scores at 1 (at or above 0.999)")]):
        yy = np.arange(len(sel)); a.hlines(yy, sel[lo], sel[hi], color="0.6", lw=4, label="95% posterior predictive"); a.plot(sel[e_], yy, "|", color="k", ms=9, label="expected")
        a.plot(sel[o], yy, "o", color="#cc3311", label="observed"); a.set_yticks(yy); a.set_yticklabels([f"{c.short(n)} ({k_})" for n, k_ in zip(sel.benchmark, sel.n)], fontsize=7)
        a.set_title(ttl, fontsize=9); a.set_xlabel("rows"); a.legend(fontsize=7, loc="lower right")
    a = ax[2]; top = Zt.head(4).benchmark.tolist(); col = ["#cc3311", "#4477aa", "#228833", "#aa3377"]
    for nme, cc in zip(top, col):
        rb = el.rows_of_bench[bn.index(nme)]; a.scatter(rq["mubar"][rb], y[rb], s=14, color=cc, label=c.short(nme), alpha=.8)
    a.plot([0, 1], [0, 1], color="k", lw=.5); a.set_xscale("symlog", linthresh=.01); a.set_yscale("symlog", linthresh=.01)
    a.set_xlabel("posterior mean predicted score"); a.set_ylabel("observed score"); a.legend(fontsize=7); a.set_title("largest bound components: observed against predicted", fontsize=9)
    fig.suptitle(f"{NAME}: mass at the bounds per benchmark (rows in brackets)", fontsize=10); save(fig, "bounds_by_benchmark.png")

# ---------------------------------------------------------------- 5. residuals against ability, date, developer, family
if "resid" in parts:
    Qb = B["comp"]["Qb"]; t1b = el.t1_bench; thr = float(np.quantile(REPMAX["Qb"], .95))
    Qpp = []
    from lib import ppc_checks as ppc
    for s in range(0, zr.shape[0], 2):
        yy_ = yr[s]; zz = zr[s]; qq = []
        for b in t1b:
            rows_ = el.rows_of_bench[b]; o = rows_[np.argsort(chat[el.mi[rows_]], kind="stable")]
            qq.append(sum(len(g) * zz[g].mean() ** 2 for g in np.array_split(o, 4)))
        Qpp.append(qq)
    Qpp = np.array(Qpp)
    quart = []
    for b in t1b:
        rows_ = el.rows_of_bench[b]; o = rows_[np.argsort(chat[el.mi[rows_]], kind="stable")]
        quart.append([float(z[g].mean()) for g in np.array_split(o, 4)])
    T1 = pd.DataFrame(dict(benchmark=[bn[b] for b in t1b], n=[len(el.rows_of_bench[b]) for b in t1b], Qb=Qb, pp99=np.quantile(Qpp, .99, axis=0),
                           p_pp=(Qpp >= Qb[None]).mean(0), z_q1=[q_[0] for q_ in quart], z_q2=[q_[1] for q_ in quart], z_q3=[q_[2] for q_ in quart], z_q4=[q_[3] for q_ in quart],
                           mean_z2=[float((z[el.rows_of_bench[b]] ** 2).mean()) for b in t1b])).sort_values("Qb", ascending=False)
    T1.to_csv(OUT / "t1_by_benchmark.csv", index=False, float_format="%.3f")
    # curve panels for the 12 largest T1 components
    S_ = B["P"]; grid = np.linspace(chat.min() - .3, chat.max() + .3, 80)
    fig, ax = plt.subplots(3, 4, figsize=(16, 10)); ax = ax.ravel()
    for a, nme in zip(ax, T1.benchmark.head(12)):
        b = bn.index(nme); rb = el.rows_of_bench[b]
        cur = 1 / (1 + np.exp(-S_["slope"][:, b][:, None] * (grid[None] - S_["difficulty"][:, b][:, None])))
        a.fill_between(grid, np.quantile(cur, .05, 0), np.quantile(cur, .95, 0), color="0.8"); a.plot(grid, cur.mean(0), color="k", lw=1)
        a.scatter(chat[el.mi[rb]], y[rb], s=9, c=np.clip(z[rb], -3, 3), cmap="RdBu_r", vmin=-3, vmax=3, edgecolor="0.3", lw=.2)
        o = rb[np.argsort(chat[el.mi[rb]], kind="stable")]
        for g in np.array_split(o, 4):
            a.plot(chat[el.mi[g]].mean(), y[g].mean(), "D", color="#ee7733", ms=6); a.plot(chat[el.mi[g]].mean(), rq["mubar"][g].mean(), "x", color="k", ms=6)
        a.set_title(f"{c.short(nme, 30)}  Q={Qb[list(t1b).index(b)]:.1f}  n={len(rb)}", fontsize=8.5); a.set_ylim(-.03, 1.03)
    fig.suptitle(f"{NAME}: score against general capability for the 12 largest T1 components. Line and band = benchmark curve without offsets (90%); "
                 "diamonds = observed quartile means, crosses = predicted quartile means (with offsets); colour = residual z", fontsize=9)
    fig.supxlabel("posterior mean capability (raw scale)"); save(fig, "t1_curves.png", dpi=75)
    # pooled panels
    dates = pd.to_datetime(df["date"]); yrs = dates.dt.year + (dates.dt.month - 1) / 12
    lg = np.log(rq["mubar"] / (1 - rq["mubar"]))
    def binned(x, v, nb=12):
        e = np.quantile(x, np.linspace(0, 1, nb + 1)); i = np.clip(np.digitize(x, e[1:-1]), 0, nb - 1)
        return (np.array([x[i == j].mean() for j in range(nb)]), np.array([v[i == j].mean() for j in range(nb)]),
                np.array([v[i == j].std() / np.sqrt((i == j).sum()) for j in range(nb)]))
    fig, ax = plt.subplots(2, 3, figsize=(16, 9))
    for a, (x, xl) in zip(ax[0], [(chat[el.mi], "model capability (posterior mean)"), (lg, "logit of predicted mean score"), (yrs.to_numpy(), "model release date")]):
        a.scatter(x, z, s=3, color="0.6", alpha=.5); bx, bm, bs = binned(x, z); a.errorbar(bx, bm, 2 * bs, fmt="o-", color="#cc3311", ms=4, label="binned mean of z, +-2 SE")
        bx, bm, bs = binned(x, z ** 2); a.plot(bx, bm - 1, "s--", color="#4477aa", ms=4, label="binned mean of z squared, minus 1")
        a.axhline(0, color="k", lw=.5); a.set_ylim(-2.5, 2.5); a.set_xlabel(xl); a.set_ylabel("standardised residual z"); a.legend(fontsize=7)
    # developers
    od = pd.DataFrame(dict(org=org, z=z, b=el.bi)); g = od.groupby("org")["z"].agg(["size", "mean", "std"]); g = g[g["size"] >= 20].sort_values("mean")
    g["se"] = g["std"] / np.sqrt(g["size"]); g["mean_z2"] = od.assign(z2=od.z ** 2).groupby("org")["z2"].mean()
    a = ax[1, 0]; yy = np.arange(len(g)); a.errorbar(g["mean"], yy, xerr=2 * g["se"], fmt="o", color="#cc3311"); a.axvline(0, color="k", lw=.5)
    a.set_yticks(yy); a.set_yticklabels([f"{o[:22]} ({n})" for o, n in zip(g.index, g["size"])], fontsize=7); a.set_xlabel("mean residual z, +-2 SE"); a.set_title("by developer (20+ rows)", fontsize=9)
    # families: lineage families in the model, and Epoch tags, interaction styles outside it
    fam = {"lin:" + k: [b for b in range(el.K) if f(bn[b])] for k, f in __import__("w6x_family").LINEAGE.items()}
    for tname in sorted(set(";".join(M.tags).split(";")) - {""}): fam["tag:" + tname] = [b for b in range(el.K) if tname in M.tags[b].split(";")]
    for sname in sorted(set(M["style"])): fam["style:" + sname] = [b for b in range(el.K) if M["style"][b] == sname]
    frow = []
    for kf, bs_ in fam.items():
        rws = np.where(np.isin(el.bi, bs_))[0]
        if len(rws) < 15 or len(bs_) < 2: continue
        # between-model variance of the family-mean residual, against the PP envelope: what a family offset would absorb
        def fstat(zz):
            d_ = pd.DataFrame(dict(m=el.mi[rws], z=zz[rws])).groupby("m")["z"].agg(["sum", "size"]); d_ = d_[d_["size"] >= 2]
            return float(np.mean(d_["sum"] ** 2 / d_["size"])) if len(d_) else np.nan
        f_obs = fstat(z); f_pp = np.array([fstat(zr[s]) for s in range(0, zr.shape[0], 4)])
        frow.append(dict(family=kf, benchmarks=len(bs_), rows=len(rws), mean_z=float(z[rws].mean()), mean_z2=float((z[rws] ** 2).mean()),
                         model_block_stat=f_obs, pp99=float(np.nanquantile(f_pp, .99)), p_pp=float(np.nanmean(f_pp >= f_obs))))
    F = pd.DataFrame(frow).sort_values("p_pp"); F.to_csv(OUT / "resid_by_family.csv", index=False, float_format="%.3f")
    a = ax[1, 1]; Fs = F.sort_values("model_block_stat"); yy = np.arange(len(Fs)); a.barh(yy, Fs.model_block_stat, color=["#cc3311" if p < .01 else "0.6" for p in Fs.p_pp])
    a.plot(Fs.pp99, yy, "|", color="k", ms=8); a.set_yticks(yy); a.set_yticklabels([f"{f} ({n})" for f, n in zip(Fs.family, Fs.benchmarks)], fontsize=6.5)
    a.set_xlabel("mean over models of (sum z)^2 / n within the family; tick = PP 99%"); a.set_title("shared model-by-family residual (red: beyond PP 99%)", fontsize=9)
    # benchmark dispersion
    disp = pd.DataFrame(dict(benchmark=bn, n=[len(r_) for r_ in el.rows_of_bench], mean_z2=[float((z[r_] ** 2).mean()) for r_ in el.rows_of_bench],
                             pp_lo=[float(np.quantile((zr[:, r_] ** 2).mean(1), .005)) for r_ in el.rows_of_bench],
                             pp_hi=[float(np.quantile((zr[:, r_] ** 2).mean(1), .995)) for r_ in el.rows_of_bench], sigma=B["P"]["sigma"].mean(0)))
    disp.to_csv(OUT / "dispersion_by_benchmark.csv", index=False, float_format="%.3f")
    a = ax[1, 2]; edges = [0, .1, .3, .7, .9, 1.0000001]; gI = np.digitize(rq["mubar"], edges[1:-1])
    vb = [float((z[gI == j] ** 2).mean()) for j in range(5)]; vpp = np.array([[(zr[s][gI == j] ** 2).mean() for j in range(5)] for s in range(zr.shape[0])])
    a.bar(range(5), vb, color="#4477aa"); a.errorbar(range(5), np.median(vpp, 0), yerr=[np.median(vpp, 0) - np.quantile(vpp, .005, 0), np.quantile(vpp, .995, 0) - np.median(vpp, 0)], fmt="k_", capsize=4)
    a.set_xticks(range(5)); a.set_xticklabels([f"{edges[j]:.1f}-{min(edges[j + 1], 1):.1f}\n(n={int((gI == j).sum())})" for j in range(5)], fontsize=8)
    a.set_xlabel("predicted mean score band (T3)"); a.set_ylabel("mean z squared; bars with caps = PP 99%"); a.axhline(1, color="k", lw=.5)
    fig.suptitle(f"{NAME}: residuals against capability, predicted score, release date, developer, family and score band", fontsize=10); save(fig, "resid_panels.png", dpi=75)
    # by source (per-source noise) and by date x benchmark era
    sd = pd.DataFrame(dict(source=df["source"].fillna("(Epoch run)").to_numpy(), z=z, z2=z ** 2)); gs = sd.groupby("source").agg(n=("z", "size"), mean_z=("z", "mean"), mean_z2=("z2", "mean"))
    gs = gs[gs.n >= 15].sort_values("mean_z2", ascending=False); gs.to_csv(OUT / "resid_by_source.csv", float_format="%.3f")
    era = np.where(M.year.to_numpy()[el.bi] <= 2022, "old", "new"); late = yrs.to_numpy() >= 2025
    res["resid"] = dict(T1_rep_max95=thr, T1_above_rep_max95=T1[T1.Qb > thr].benchmark.tolist(), T1_top=T1.head(10).round(3).to_dict("records"),
                        T1_n_beyond_pp99=int((T1.Qb > T1.pp99).sum()), T1_n=len(T1),
                        z_vs_date_spearman=float(st.spearmanr(z, yrs).statistic), z_vs_capability_spearman=float(st.spearmanr(z, chat[el.mi]).statistic),
                        mean_z_by_era_and_model_date={f"{e_}_bench/{'2025+' if l_ else 'pre-2025'}_model": [float(z[(era == e_) & (late == l_)].mean()), int(((era == e_) & (late == l_)).sum())]
                                                      for e_ in ("old", "new") for l_ in (False, True)},
                        developers=g.round(3).reset_index().to_dict("records"), families=F.round(3).to_dict("records"),
                        band_mean_z2=vb, band_pp99=[[float(np.quantile(vpp[:, j], .005)), float(np.quantile(vpp[:, j], .995))] for j in range(5)],
                        dispersion_outside_pp99=disp[(disp.mean_z2 > disp.pp_hi) | (disp.mean_z2 < disp.pp_lo)].round(3).to_dict("records"),
                        sources_top=gs.head(8).round(3).reset_index().to_dict("records"), sources_bottom=gs.tail(5).round(3).reset_index().to_dict("records"),
                        epoch_run_vs_external_mean_z2=[float((z[M.epoch_run.to_numpy()[el.bi]] ** 2).mean()), float((z[~M.epoch_run.to_numpy()[el.bi]] ** 2).mean())])

# ---------------------------------------------------------------- 6. OTIS Mock AIME in detail
if "otis" in parts:
    nme = "OTIS Mock AIME 2024-2025"; b = bn.index(nme); rb = el.rows_of_bench[b]
    raw = pd.read_csv(io.BytesIO(zipfile.ZipFile(data.ZIP).read(c.INTERNAL[nme])))
    n_items = (raw["mean_score"] * (1 - raw["mean_score"]) / raw["stderr"] ** 2).replace([np.inf, -np.inf], np.nan)
    o = rb[np.argsort(chat[el.mi[rb]], kind="stable")]; qs = np.array_split(o, 4)
    d_ = pd.DataFrame(dict(model=df["Model"].to_numpy()[rb], org=org[rb], date=df["date"].to_numpy()[rb], y=df["performance"].to_numpy()[rb], pred=rq["mubar"][rb],
                           z=z[rb], chat=chat[el.mi[rb]], elpd=B["elpd_i"][rb], k=B["k"][rb], pit=B["pit"][rb]))
    d_["quartile"] = 0
    for j, g in enumerate(qs): d_.loc[np.isin(rb, g), "quartile"] = j + 1
    d_.sort_values("chat").to_csv(OUT / "otis_rows.csv", index=False, float_format="%.4f")
    S_ = B["P"]; kap_b = float((1 / (4 * S_["sigma"][:, b] ** 2) - 1).mean())
    res["otis"] = dict(n=len(rb), zeros=int((y[rb] <= c.EPS).sum()), ones=int((y[rb] >= 1 - c.EPS).sum()), exp_ones=float(rq["p1"][rb].sum()),
                       scores_ge_0_9=int((y[rb] >= .9).sum()), pred_ge_0_9=int((rq["mubar"][rb] >= .9).sum()),
                       Qb=float(B["comp"]["Qb"][list(el.t1_bench).index(b)]),
                       quartile=[dict(q=j + 1, n=len(g), cap_lo=float(chat[el.mi[g]].min()), cap_hi=float(chat[el.mi[g]].max()), mean_y=float(y[g].mean()), mean_pred=float(rq["mubar"][g].mean()),
                                      mean_z=float(z[g].mean()), contribution=float(len(g) * z[g].mean() ** 2)) for j, g in enumerate(qs)],
                       slope=float(S_["slope"][:, b].mean()), slope_rank_of_57=int((S_["slope"].mean(0) > S_["slope"][:, b].mean()).sum() + 1),
                       sigma=float(S_["sigma"][:, b].mean()), kappa=kap_b, difficulty=float(S_["difficulty"][:, b].mean()),
                       implied_items_from_stderr=dict(median=float(n_items.median()), q25=float(n_items.quantile(.25)), q75=float(n_items.quantile(.75))),
                       raw_runs=len(raw), stderr_median=float(raw["stderr"].median()), source="run by Epoch (zip member otis_mock_aime_2024_2025.csv; column mean_score with stderr)",
                       sources_in_fit_input=df["source"].iloc[rb].fillna("(none: Epoch run)").value_counts().to_dict(),
                       mean_z2=float((z[rb] ** 2).mean()), loo_pit_var_ratio=float(B["pit"][rb].var() * 12),
                       by_org={o_: [float(v["z"].mean()), int(len(v))] for o_, v in d_.groupby("org") if len(v) >= 5},
                       largest_abs_z=d_.reindex(d_.z.abs().sort_values(ascending=False).index).head(12).round(3).to_dict("records"),
                       top_quartile_rows=d_[d_.quartile == 4].sort_values("z").head(8).round(3).to_dict("records"),
                       has_dev_cell=int((B["ex"]["cell_idx"][rb] >= 0).sum()))
    grid = np.linspace(chat[el.mi[rb]].min() - .2, chat.max() + .2, 100)
    cur = 1 / (1 + np.exp(-S_["slope"][:, b][:, None] * (grid[None] - S_["difficulty"][:, b][:, None])))
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.8))
    a = ax[0]; a.fill_between(grid, np.quantile(cur, .05, 0), np.quantile(cur, .95, 0), color="0.8"); a.plot(grid, cur.mean(0), "k", lw=1)
    sc = a.scatter(d_.chat, d_.y, s=14, c=np.clip(d_.z, -3, 3), cmap="RdBu_r", vmin=-3, vmax=3, edgecolor="0.3", lw=.2); fig.colorbar(sc, ax=a, label="z")
    for g in qs: a.plot(chat[el.mi[g]].mean(), y[g].mean(), "D", color="#ee7733", ms=7); a.plot(chat[el.mi[g]].mean(), rq["mubar"][g].mean(), "kx", ms=7)
    a.set_xlabel("capability"); a.set_ylabel("score"); a.set_title("curve (90% band), observed (diamond) and predicted (cross) quartile means", fontsize=8)
    a = ax[1]; a.scatter(d_.pred, d_.z, s=12, color="#4477aa"); a.axhline(0, color="k", lw=.5); a.set_xlabel("predicted mean score"); a.set_ylabel("z")
    a.set_title(f"residual against prediction; {res['otis']['ones']} scores at 1 against {res['otis']['exp_ones']:.1f} expected", fontsize=8)
    a = ax[2]; a.hist(n_items.dropna(), bins=40, color="0.6"); a.set_xlabel("implied item count, p(1-p)/stderr^2, per run in Epoch's file"); a.set_ylabel("runs")
    a.set_title(f"fitted concentration kappa = {kap_b:.0f} (sigma {res['otis']['sigma']:.3f}); implied items median {n_items.median():.0f}", fontsize=8)
    fig.suptitle(f"{NAME}: OTIS Mock AIME 2024-2025 ({len(rb)} models), T1 component {res['otis']['Qb']:.1f}", fontsize=10); save(fig, "otis_detail.png")

# ---------------------------------------------------------------- 7. per-benchmark parameters
if "forest" in parts:
    t = B["t"]; post = t["posterior"].to_dataset()
    ds = xr.Dataset(dict(difficulty=post["difficulty"], log_slope=post["log_slope"], sigma=post["sigma"]))
    order = [bn[b] for b in np.argsort(dmean)]; ds = ds.sel(benchmark=order)
    sm = az.summary(xr.DataTree.from_dict({"posterior": ds}), kind="all", ci_prob=0.9, ci_kind="eti", round_to="none")
    sm.to_csv(OUT / "benchmark_params_summary.csv", float_format="%.4f")
    capr = (float(chat.min()), float(chat.max())); n_b = {bn[b]: len(el.rows_of_bench[b]) for b in range(el.K)}
    sig = post["sigma"].stack(s=("chain", "draw")); dif = post["difficulty"].stack(s=("chain", "draw")); lsl = post["log_slope"].stack(s=("chain", "draw"))
    flags = []
    for nme in order:
        s_ = sig.sel(benchmark=nme).to_numpy(); d__ = dif.sel(benchmark=nme).to_numpy(); l_ = lsl.sel(benchmark=nme).to_numpy()
        f = dict(benchmark=nme, n=n_b[nme], difficulty=float(d__.mean()), difficulty_sd=float(d__.std()), slope=float(np.exp(l_).mean()), log_slope_sd=float(l_.std()),
                 sigma=float(s_.mean()), sigma_q95=float(np.quantile(s_, .95)), p_sigma_gt_0_45=float((s_ > .45).mean()),
                 outside_capability_range=bool(d__.mean() > capr[1] or d__.mean() < capr[0]),
                 share_draws_beyond_cap_max=float((d__ > capr[1]).mean()),
                 corr_difficulty_log_slope=float(np.corrcoef(d__, l_)[0, 1]))
        f["flag"] = ";".join(x for x, v in [("sigma near 0.5 bound", f["p_sigma_gt_0_45"] > .05), ("difficulty beyond most capable model", f["share_draws_beyond_cap_max"] > .5),
                                             ("difficulty sd > 1", f["difficulty_sd"] > 1.0), ("log slope sd > 0.4", f["log_slope_sd"] > .4),
                                             ("difficulty-slope corr > 0.9", abs(f["corr_difficulty_log_slope"]) > .9)] if v)
        flags.append(f)
    Fl = pd.DataFrame(flags); Fl.to_csv(OUT / "benchmark_params_flags.csv", index=False, float_format="%.4f")
    rh = sm["r_hat"] if "r_hat" in sm else None
    res["params"] = dict(flagged=Fl[Fl.flag != ""][["benchmark", "n", "difficulty", "difficulty_sd", "slope", "log_slope_sd", "sigma", "flag"]].round(3).to_dict("records"),
                         capability_range=capr, max_rhat=float(sm["r_hat"].max()) if rh is not None else None,
                         min_ess_bulk=float(sm["ess_bulk"].min()) if "ess_bulk" in sm else None,
                         sigma_range=[float(Fl.sigma.min()), float(Fl.sigma.max())], slope_range=[float(Fl.slope.min()), float(Fl.slope.max())],
                         log_slope_sd_vs_n_spearman=float(st.spearmanr(Fl.log_slope_sd, Fl.n).statistic),
                         tau=az.summary(t, var_names=["tau_alpha", "sigma_median", "tau_sigma", "tau_delta", "tau_fam"], kind="stats", ci_prob=0.9, round_to="none").round(4).to_dict("index"))
    try:
        pc = az.plot_forest(xr.DataTree.from_dict({"posterior": ds}), var_names=["difficulty", "log_slope", "sigma"], combined=True, ci_kind="eti", ci_probs=(0.5, 0.9),
                            backend="matplotlib", figure_kwargs=dict(figsize=(9, 26)))
        pc.savefig(OUT / "forest_benchmark_params_arviz.png", dpi=60); print("wrote forest (ArviZ)", (OUT / "forest_benchmark_params_arviz.png").stat().st_size // 1024, "KB")
    except Exception as ex_: print("az.plot_forest failed", repr(ex_)[:300])
    # compact three-column layout of the same az.summary intervals
    fig, ax = plt.subplots(1, 3, figsize=(13, 10), sharey=True); yy = np.arange(len(order))[::-1]
    for a, v, ttl in zip(ax, ["difficulty", "log_slope", "sigma"], ["difficulty (raw scale); dashed = capability range", "log slope", "sigma (noise SD at 0.5); upper bound 0.5"]):
        s_ = sm.loc[[f"{v}[{n}]" for n in order]]; lo_c, hi_c = [c_ for c_ in sm.columns if c_.startswith("eti")][:2]
        colr = ["#cc3311" if fl else "#4477aa" for fl in Fl.flag != ""]
        a.hlines(yy, s_[lo_c], s_[hi_c], color=colr, lw=1.6); a.scatter(s_["mean"], yy, s=10, color=colr, zorder=3); a.set_title(ttl, fontsize=9); a.grid(axis="x", lw=.3)
        if v == "difficulty": a.axvline(capr[0], color="k", ls="--", lw=.6); a.axvline(capr[1], color="k", ls="--", lw=.6)
        if v == "sigma": a.axvline(.5, color="k", ls="--", lw=.6)
    ax[0].set_yticks(yy); ax[0].set_yticklabels([f"{c.short(n, 26)} ({n_b[n]})" for n in order], fontsize=6.5)
    fig.suptitle(f"{NAME}: per-benchmark posterior means and 90% intervals (az.summary), easy to hard; red = flagged (see benchmark_params_flags.csv)", fontsize=10)
    save(fig, "forest_benchmark_params.png", dpi=85)

tag = "_".join(parts) if len(sys.argv) > 1 else "all"
(OUT / f"diag_{NAME}_{tag}.json").write_text(json.dumps(res, indent=1, default=float))
print("DONE", flush=True)
