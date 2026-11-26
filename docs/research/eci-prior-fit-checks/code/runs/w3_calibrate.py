"""W3 (M4, M5, M6, M13): positive control, G-null refits (SBC and null reference), misfit generators; --summarise writes calibration.json."""
import sys, json, time, argparse, warnings
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
warnings.filterwarnings("ignore")
import numpy as np, xarray as xr
from scipy.stats import beta as betad
from lib import data, fit as fitmod, fit_any, freeze, generators as G, ppc_checks as ppc, sbc, sens_metrics as sm

OUT = Path("runs/W/W3"); (OUT / "rep").mkdir(parents=True, exist_ok=True); (OUT / "truth").mkdir(exist_ok=True)
W2 = Path("runs/W/W2")
EPS = 1e-3
log = lambda *a: print(time.strftime("%H:%M:%S"), *a, flush=True)
TARGET = {"shape": "T1", "2d": "T2", "disp": "T3", "drift": "T4", "offset": "T5"}


def setup():
    df = data.fit_input(); scores = data.read_member(data.SCORES)
    freeze.freeze("ppc_checks.py", "sbc.py")
    el = ppc.Elig(df, scores); pat = G.Pattern(df, scores)
    t = xr.open_datatree(W2 / "seed12345.nc"); post = t["posterior"].to_dataset()
    pooled = {v: post[v].stack(s=("chain", "draw")).transpose("s", ...).to_numpy() for v in
              ["capability", "difficulty", "slope", "sigma", "tau_alpha", "sigma_median", "tau_sigma"]}
    names = [str(x) for x in post["model"].values]
    return df, scores, el, pat, pooled, names


def code_dig():
    return fitmod.sha_bytes("".join(fitmod.sha_file(p) for p in [fitmod.RUNS / "vendor/eci-public/src/eci/bayesian.py", fitmod.RUNS / "lib/ppc_checks.py",
                                                                 fitmod.RUNS / "lib/generators.py", fitmod.RUNS / "lib/sbc.py", fitmod.RUNS / "lib/fit_any.py"]).encode())


def run_positive_control(df, names):
    import numpy as np
    strata = json.loads(Path("runs/strata.json").read_text())
    masks = {k: np.array([n in set(strata[k]) for n in names]) for k in ("all", "frontier", "sparse", "dense")}
    res = {}
    for s in (12345, 22345, 32345):
        js = OUT / f"pc_seed{s}.json"
        if js.exists():
            res[s] = json.loads(js.read_text()); continue
        log("positive control seed", s)
        d, warns, wall = fit_any.run(df, s, epoch_priors=dict(tau_alpha=(float(np.log(0.05)), 0.1)))
        ok, last = fitmod.verdict(d["attempts"])
        e0, nm0, _ = fitmod.load_eci(W2 / f"seed{s}.nc"); assert list(nm0) == names
        sc = sm.score(d["eci"], e0, names, masks)
        for k in sc:
            if isinstance(sc[k], dict): sc[k].pop("p_top10_k", None); sc[k].pop("p_top10_0", None)
        fails = {k: bool(not (sc[k]["S1_pass"] and sc[k]["S2_pass"] and sc[k]["S3_pass"])) for k in ("all", "frontier")}
        fails["S4"] = bool(not sc["S4"]["pass_"])
        r = dict(seed=s, converged=ok, last_attempt=last, wall_seconds=round(wall, 1), scores=sc, fails_in=fails,
                 fails_S1_S4_in_frontier_or_all=bool(fails["all"] or fails["frontier"] or fails["S4"]))
        np.savez_compressed(OUT / f"pc_seed{s}.npz", eci=d["eci"].astype("float32"))
        fit_any.atomic_json(js, r); res[s] = r
    return res


def run_rep(gen, r, df, el, pat, pooled, names, low, high, force=False):
    js = OUT / "rep" / f"{gen}_{r}.json"; nc = OUT / "rep" / f"{gen}_{r}.nc"
    S = pooled["capability"].shape[0]; pos = G.position(gen, r, S)
    want = dict(gen=gen, r=r, seed=G.seed_of(gen, r), position=pos, code_sha256=code_dig(), input_sha256=fitmod.input_digest(df))
    if js.exists() and not force:
        old = json.loads(js.read_text())
        if old.get("timeout") and old.get("code_sha256") == want["code_sha256"]: return old
        if nc.exists() and all(old.get(k) == v for k, v in want.items()): return old
    theta = {k: pooled[k][pos] for k in ("capability", "difficulty", "slope", "sigma")}
    y, info = G.simulate(gen, r, theta, pat)
    df_r = df.copy(); df_r["performance"] = y
    d, warns, wall = fit_any.run(df_r, want["seed"])
    ok, last = fitmod.verdict(d["attempts"])
    th = fit_any.thin_post(d["trace"])
    yc = np.clip(y, EPS, 1 - EPS)
    rq = ppc.residual_quantities(th, el); T, comp, mx = ppc.stats(yc, rq, el)
    side = dict(want, info=info, converged=ok, last_attempt=last, attempts=d["attempts"], started_from=d["started_from"], warnings=warns,
                wall_seconds=round(wall, 1), T=T, maxima=mx)
    np.savez_compressed(OUT / "truth" / f"{gen}_{r}.npz", **theta, tau_alpha=pooled["tau_alpha"][pos], sigma_median=pooled["sigma_median"][pos], tau_sigma=pooled["tau_sigma"][pos])
    if gen == "null":
        te, td = sbc.truth_anchored(theta["capability"], theta["difficulty"], low, high)
        de, dd = sbc.anchored(th["capability"], th["difficulty"], low, high)
        side["u_eci"] = sbc.u_value(de, te).tolist(); side["u_edi"] = sbc.u_value(dd, td).tolist()
        side["u_hyper"] = {h: float(sbc.u_value(th[h][:, None], np.array([pooled[h][pos]]))[0]) for h in ("tau_alpha", "sigma_median", "tau_sigma")}
        side["u_slope"] = sbc.u_value(th["slope"], theta["slope"]).tolist(); side["u_sigma"] = sbc.u_value(th["sigma"], theta["sigma"]).tolist()
    ds = xr.Dataset({k: (("draw",) + tuple(f"{k}_d{i}" for i in range(v.ndim - 1)), v) for k, v in th.items()})
    tmp = OUT / "rep" / f".{gen}_{r}.nc.tmp"; ds.to_netcdf(tmp); import os; os.replace(tmp, nc)
    fit_any.atomic_json(js, side)
    return side


def cp(k, n, level=.90):
    a = (1 - level) / 2
    return (float(betad.ppf(a, k, n - k + 1)) if k > 0 else 0.0, float(betad.ppf(1 - a, k + 1, n - k)) if k < n else 1.0)


def summarise(names, el):
    strata = json.loads(Path("runs/strata.json").read_text())
    anchor = np.array([n in sm.ANCHORS for n in names]); na = ~anchor
    masks = {k: np.array([n in set(strata[k]) for n in names]) for k in ("all", "frontier", "sparse", "dense")}
    reps = {}
    for g in G.GENERATORS:
        reps[g] = [json.loads(p.read_text()) for p in sorted((OUT / "rep").glob(f"{g}_*.json"), key=lambda p: int(p.stem.split("_")[1]))]
    res = dict(counts={g: dict(finished=len(reps[g]), converged=sum(x["converged"] for x in reps[g]), planned=G.REPS[g]) for g in G.GENERATORS})
    null = [x for x in reps["null"] if x["converged"]]
    rng = np.random.default_rng(20261113)
    if null:
        Ue = np.array([x["u_eci"] for x in null]); Ud = np.array([x["u_edi"] for x in null])
        Ua = Ue[:, na]; strat_na = {k: masks[k][na] for k in ("all", "frontier", "sparse", "dense")}
        rec = {k: sbc.coverage(Ua, strat_na[k], rng) for k in strat_na}
        P = np.hstack([Ua, Ud]); pv, counts = sbc.chi2_test(P); thr = sbc.ALPHA / P.shape[1]
        flagged = np.where(pv < thr)[0]
        bn = [str(b) for b in el.bench_names]; nonanchor_names = [n for n, a in zip(names, anchor) if not a]
        labels = [f"ECI:{n}" for n in nonanchor_names] + [f"EDI:{b}" for b in bn]
        ok, sbc_pass = sbc.verdict(len(flagged), rec["all"], rec["frontier"])
        res["recovery"] = dict(n_converged_null=len(null), coverage90_all=rec["all"]["c90"], by_stratum={k: rec[k] for k in rec},
                               in_band_0_85_0_95=bool(0.85 <= rec["all"]["c90"]["share"] <= 0.95))
        res["SBC"] = dict(n_parameters=int(P.shape[1]), bonferroni_level=float(thr), n_flagged=int(len(flagged)), flagged=[labels[j] for j in flagged[:50]],
                          min_p=float(pv.min()), median_p=float(np.median(pv)), checks=ok, pass_=bool(sbc_pass), gates_nothing=True,
                          pooled_rank_histogram_eci=np.histogram(Ua.ravel(), 10, (0, 1))[0].tolist(),
                          pooled_rank_histogram_edi=np.histogram(Ud.ravel(), 10, (0, 1))[0].tolist(),
                          descriptive_hist={h: np.histogram([x["u_hyper"][h] for x in null], 10, (0, 1))[0].tolist() for h in ("tau_alpha", "sigma_median", "tau_sigma")} |
                          {"slope_pooled": np.histogram(np.array([x["u_slope"] for x in null]).ravel(), 10, (0, 1))[0].tolist(),
                           "sigma_pooled": np.histogram(np.array([x["u_sigma"] for x in null]).ravel(), 10, (0, 1))[0].tolist()})
        Tn = [x["T"] for x in null]
        res["null_reference"] = {k: dict(mean=float(np.mean([t[k] for t in Tn])), sd=float(np.std([t[k] for t in Tn], ddof=1)),
                                         q05=float(np.quantile([t[k] for t in Tn], .05)), median=float(np.median([t[k] for t in Tn])),
                                         q95=float(np.quantile([t[k] for t in Tn], .95)), max=float(np.max([t[k] for t in Tn]))) for k in ppc.TNAMES}
        power = {}
        for g, tk in TARGET.items():
            cv = [x for x in reps[g] if x["converged"]]
            if not cv: continue
            hits = [ppc.max_t(x["T"], Tn)[tk]["p_adjusted"] < 0.01 for x in cv]
            lo, hi = cp(sum(hits), len(cv))
            power[g] = dict(check=tk, n_converged=len(cv), n_reject=int(sum(hits)), power=float(np.mean(hits)), cp90=[lo, hi],
                            meets_16_of_20_and_15_converged=bool(sum(hits) >= 16 and len(cv) >= 15), planted=[x["info"] for x in cv][:3])
        res["power"] = power
    # timeouts: inspect and compare the censored truths with the converged ones (coordinator request)
    from scipy.stats import mannwhitneyu
    def truth_stats(x):
        z = np.load(OUT / "truth" / f"{x['gen']}_{x['r']}.npz")
        return dict(tau_alpha=float(z["tau_alpha"]), sigma_median=float(z["sigma_median"]), tau_sigma=float(z["tau_sigma"]), slope_min=float(z["slope"].min()), slope_max=float(z["slope"].max()),
                    slope_range=float(z["slope"].max() / z["slope"].min()))
    tos = {g: [dict(r=x["r"], seed=x["seed"], position=x.get("position"), runs_completed=x.get("runs_completed_before_cap"), truth=truth_stats(x)) for x in reps[g] if x.get("timeout")] for g in G.GENERATORS}
    res["timeouts"] = {g: v for g, v in tos.items() if v}
    nt = len(tos["null"]); res["timeouts_null"] = dict(n=nt, share=nt / max(1, len(reps["null"])), stop_rule_more_than_5pct=bool(nt > 10))
    if nt:
        cv = [truth_stats(x) for x in null]; tt = [t["truth"] for t in tos["null"]]
        cmp_ = {}
        for k in ("tau_alpha", "sigma_median", "tau_sigma", "slope_min", "slope_max", "slope_range"):
            a_, b_ = [c[k] for c in cv], [t[k] for t in tt]
            cmp_[k] = dict(converged_mean=float(np.mean(a_)), timed_out_mean=float(np.mean(b_)), timed_out_values=b_, mannwhitney_p=float(mannwhitneyu(a_, b_).pvalue) if len(b_) > 1 else None)
        res["timeouts_null"]["truth_comparison"] = cmp_
    pcs = {}
    for s in (12345, 22345, 32345):
        if (OUT / f"pc_seed{s}.json").exists(): pcs[s] = json.loads((OUT / f"pc_seed{s}.json").read_text())
    res["positive_control"] = {str(s): dict(converged=v["converged"], fails_in=v["fails_in"], fails_S1_S4_in_frontier_or_all=v["fails_S1_S4_in_frontier_or_all"],
                                            all_S1=v["scores"]["all"]["S1"], frontier_S1=v["scores"]["frontier"]["S1"],
                                            all_S2=[v["scores"]["all"]["S2_count"], v["scores"]["all"]["S2_limit"]], frontier_S2=[v["scores"]["frontier"]["S2_count"], v["scores"]["frontier"]["S2_limit"]],
                                            all_S3=[v["scores"]["all"]["S3_count"], v["scores"]["all"]["S3_limit"]], S4=v["scores"]["S4"]["pass_"]) for s, v in pcs.items()}
    # G1
    if "recovery" in res and len(pcs) == 3 and "power" in res:
        rv = res["recovery"]["coverage90_all"]["share"]
        g1 = dict(recovery_in_band=bool(.85 <= rv <= .95), n_null_converged_ge_150=len(null) >= 150,
                  T2_power_on_2d=bool(res["power"].get("2d", {}).get("meets_16_of_20_and_15_converged", False)),
                  T5_power_on_offset=bool(res["power"].get("offset", {}).get("meets_16_of_20_and_15_converged", False)),
                  positive_control_fails_all_3_seeds=all(v["fails_S1_S4_in_frontier_or_all"] for v in pcs.values()))
        g1["proceed"] = all(g1.values()); g1["stop_recovery_below_0_75"] = bool(rv < .75); g1["recovery"] = rv
        res["G1"] = g1
    (OUT / "calibration.json").write_text(json.dumps(res, indent=1, default=str))
    return res


CAP_SECONDS = 3600   # deviation 10: a replicate whose Epoch draw ladder runs past 60 minutes is stopped and counted as non-converged


def run_rep_capped(gen, r, pooled=None):
    import subprocess, os, signal, re
    js = OUT / "rep" / f"{gen}_{r}.json"; lg = OUT / "rep" / f"{gen}_{r}.log"
    if js.exists():
        old = json.loads(js.read_text())
        if old.get("timeout") or (old.get("code_sha256") == code_dig() and (OUT / "rep" / f"{gen}_{r}.nc").exists()): return old
    with open(lg, "w") as f:
        p = subprocess.Popen([sys.executable, "runs/w3_calibrate.py", "--one", gen, str(r)], start_new_session=True, stdout=f, stderr=subprocess.STDOUT)
        try:
            p.wait(timeout=CAP_SECONDS)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL); p.wait()
            txt = lg.read_text(); took = re.findall(r"Sampling 4 chains for ([\d_]+) tune and ([\d_]+) draw iterations .*? took (\d+) seconds", txt)
            S = pooled["capability"].shape[0]; pos = G.position(gen, r, S)
            truth = {k: pooled[k][pos] for k in ("capability", "difficulty", "slope", "sigma", "tau_alpha", "sigma_median", "tau_sigma")}
            np.savez_compressed(OUT / "truth" / f"{gen}_{r}.npz", **truth)
            fit_any.atomic_json(js, dict(gen=gen, r=r, seed=G.seed_of(gen, r), position=pos, converged=False, timeout=True, cap_seconds=CAP_SECONDS, code_sha256=code_dig(),
                                         started_from=None, runs_completed_before_cap=[dict(tune=t, draws=d, seconds=int(w)) for t, d, w in took],
                                         n_runs_completed=len(took), last_attempt=dict(divergences=None, max_rhat=None, min_ess=None, draws=None), wall_seconds=CAP_SECONDS,
                                         truth_summary=dict(tau_alpha=float(truth["tau_alpha"]), sigma_median=float(truth["sigma_median"]), tau_sigma=float(truth["tau_sigma"]),
                                                            slope_min=float(truth["slope"].min()), slope_max=float(truth["slope"].max()))))
    return json.loads(js.read_text())


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--stage", default="pc,null,2d,offset,shape,disp,drift"); ap.add_argument("--summarise", action="store_true")
    ap.add_argument("--one", nargs=2, default=None)
    a = ap.parse_args()
    if a.one:
        df, scores, el, pat, pooled, names = setup(); low, high = names.index("Claude 3.5 Sonnet"), names.index("GPT-5")
        run_rep(a.one[0], int(a.one[1]), df, el, pat, pooled, names, low, high); sys.exit(0)
    df, scores, el, pat, pooled, names = setup()
    low, high = names.index("Claude 3.5 Sonnet"), names.index("GPT-5")
    if not a.summarise:
        for st in a.stage.split(","):
            if st == "pc": run_positive_control(df, names); continue
            for r in range(G.REPS[st]):
                t0 = time.time(); x = run_rep_capped(st, r, pooled)
                log(st, r, "converged", x["converged"], x.get("started_from"), x["last_attempt"]["draws"], f"{x['wall_seconds']}s", "TIMEOUT" if x.get("timeout") else "")
    res = summarise(names, el); log(json.dumps(res.get("G1", res["counts"]), default=str)[:600])
