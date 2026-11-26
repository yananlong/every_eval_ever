"""Side-by-side headline numbers: Epoch-data results (runs/W, docs results) against EEE-data results (runs/EEE).
Run from eci_work/v11. Writes runs/EEE/headline.json (both columns) and prints a compact table. Missing stages give None."""
import sys, json, glob, os, warnings; sys.path.insert(0, "runs"); warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
DOCS = "../wt-pr14/docs/research/eci-prior-fit-checks/results/W"


def J(*paths):
    for p in paths:
        if p and os.path.exists(p):
            try: return json.load(open(p))
            except Exception: pass
    return None


def g(d, *ks, default=None):
    for k in ks:
        if d is None: return default
        try: d = d[k]
        except (KeyError, IndexError, TypeError): return default
    return d


def stage(root, alt=None):
    R = {}
    alt = alt or root
    # ---------- W2
    rep = J(f"{root}/W2/reproduction.json", f"{alt}/W2/reproduction.json")
    d = g(rep, "G0", "per_seed_diag", "12345") or {}
    R["W2"] = dict(seeds_converged=sum(bool(v) for v in (g(rep, "G0", "per_seed_converged") or {}).values()), divergences=d.get("divergences"), max_rhat=d.get("max_rhat"),
                   min_ess=d.get("min_ess"), min_tail_ess=d.get("min_tail_ess"), seed_to_seed_sd_max=g(rep, "G0", "seed_to_seed_sd_max"),
                   elpd_loo=g(rep, "EQ", "fits", "12345", "elpd_loo_epoch"), p_loo=g(rep, "EQ", "fits", "12345", "p_loo_epoch"), elpd_se=g(rep, "EQ", "fits", "12345", "se_epoch"))
    # ---------- W3
    c = J(f"{root}/W3/calibration.json")
    if c:
        cnt = c["counts"]; rec = c["recovery"]
        R["W3"] = dict(counts={k: [v["converged"], v["finished"], v["planned"]] for k, v in cnt.items()},
                       null_unusable=cnt["null"]["planned"] - cnt["null"]["converged"],
                       coverage90_all=g(rec, "by_stratum", "all", "c90", "share"), coverage90_all_ci=[g(rec, "by_stratum", "all", "c90", "lo"), g(rec, "by_stratum", "all", "c90", "hi")],
                       coverage90_frontier=g(rec, "by_stratum", "frontier", "c90", "share"), coverage50_all=g(rec, "by_stratum", "all", "c50", "share"),
                       coverage90_sparse=g(rec, "by_stratum", "sparse", "c90", "share"), coverage90_dense=g(rec, "by_stratum", "dense", "c90", "share"),
                       power={gen: dict(check=v["check"], n_converged=v["n_converged"], n_reject=v["n_reject"], power=v["power"], cp90=v.get("cp90")) for gen, v in c["power"].items()},
                       timeouts={k: len(v) for k, v in (c.get("timeouts") or {}).items()}, timeouts_null=g(c, "timeouts_null", "n"),
                       sbc=dict(n_parameters=g(c, "SBC", "n_parameters"), n_flagged=g(c, "SBC", "n_flagged"), median_p=g(c, "SBC", "median_p"), pass_=g(c, "SBC", "pass_")),
                       positive_control={s: dict(converged=v.get("converged"), fails_all=g(v, "fails_in", "all"), fails_frontier=g(v, "fails_in", "frontier"), S4_pass=v.get("S4"),
                                                 all_S1=v.get("all_S1"), all_S2=v.get("all_S2"), all_S3=v.get("all_S3"), frontier_S2=v.get("frontier_S2")) for s, v in (c.get("positive_control") or {}).items()},
                       G1=c.get("G1"), null_reference={t: dict(mean=v["mean"], sd=v["sd"], max=v["max"]) for t, v in c["null_reference"].items()})
        # crashed 2d (no JSON) and reasons
        crashed = []
        for r in range(20):
            if not os.path.exists(f"{root}/W3/rep/2d_{r}.json"):
                lg = f"{root}/W3/rep/2d_{r}.log"; txt = open(lg, errors="ignore").read()[-3000:] if os.path.exists(lg) else ""
                crashed.append(dict(r=r, anchor_error=("anchor" in txt.lower() and "ValueError" in txt)))
        R["W3"]["crashed_2d"] = crashed
        # non-converged detail for nulls
        nn = []
        for p in glob.glob(f"{root}/W3/rep/null_*.json"):
            x = json.load(open(p))
            if not x.get("converged"): nn.append(dict(r=x.get("r"), timeout=bool(x.get("timeout")), div=g(x, "last_attempt", "divergences"), rhat=g(x, "last_attempt", "max_rhat"), ess=g(x, "last_attempt", "min_ess")))
        R["W3"]["null_nonconverged"] = sorted(nn, key=lambda z: z["r"] if z["r"] is not None else -1)
    # ---------- W3M
    m = J(f"{root}/W3M_full/modrak_full.json")
    if m:
        q = m["quantities"]
        R["W3M"] = dict(n=m["meta"]["n"], rows={k: dict(P=v.get("P", 1), gamma_p=v.get("gamma_p", v.get("gamma_p_bonferroni")), gamma_flagged=v.get("gamma_n_flagged"), chi2_p=v.get("chi2_p", v.get("chi2_min_p")),
                                                     chi2_flagged=v.get("chi2_n_flagged"), central90=v.get("share_central90"), below05=v.get("share_below05"), above95=v.get("share_above95"), mean_u=v.get("mean_u")) for k, v in q.items()})
    # ---------- W4
    p = J(f"{root}/W4/ppc.json")
    if p:
        mt = p["W4b"]["maxT"]; Rn = mt["R"]
        R["W4"] = dict(n_null=Rn, min_p=1 / (Rn + 1), rejected=p["W4b"]["rejected"],
                       T={t: dict(obs=mt[t]["observed"], p_adj=mt[t]["p_adjusted"], p_unadj=mt[t]["p_unadjusted"], z=mt[t]["z_obs"]) for t in ("T1", "T2", "T3", "T4", "T5", "T6", "T7")},
                       heldout_coverage=p["W4c"]["overall_coverage"], heldout_boot90=p["W4c"]["bootstrap90"], n_heldout=g(p, "W4c_folds", "n_heldout"), flagged=p["W4c"]["flagged_benchmarks"],
                       n_benchmarks_tested=p["W4c"]["n_benchmarks_tested"], loo_coverage90=p["W4c"].get("epoch_loo_coverage_0_9"), all_folds_converged=p["W4c"].get("all_folds_converged"),
                       eligibility=p.get("eligibility"), C2_clean=p.get("C2_clean"))
        nr = g(R, "W3", "null_reference")
        if nr: R["W4"]["T2_sd_above_null_mean"] = (R["W4"]["T"]["T2"]["obs"] - nr["T2"]["mean"]) / nr["T2"]["sd"]
        # Epoch's suite tables
        try:
            cal = pd.read_csv(f"{root}/W4/epoch_calibration.csv"); ov = cal[cal.iloc[:, 0].astype(str).str.upper() == "OVERALL"].iloc[0]
            R["W4"]["loo_cov"] = {k: float(ov[k]) for k in ov.index if "coverage" in str(k)}
            R["W4"]["loo_coverage90"] = float(ov.get("coverage_0.9_loo", R["W4"]["loo_coverage90"]))
        except Exception as e: R["W4"]["loo_cov_error"] = repr(e)
        try:
            lo = pd.read_csv(f"{root}/W4/epoch_loo_summary.csv"); R["W4"]["loo_summary"] = lo.iloc[0].to_dict() if len(lo) == 1 else lo.set_index(lo.columns[0]).iloc[:, 0].to_dict()
        except Exception as e: R["W4"]["loo_summary_error"] = repr(e)
    loc = J(f"{root}/W4/localisation.json")
    if loc: R["W4_loc"] = {k: loc.get(k) for k in ("T2_median_q", "T2_share_q_gt_3.84", "T5_share_abs_t_gt_2", "T1_share_Qb_gt_9.49", "T1_Qb_median")} | dict(
        T2_top_pairs=[x for x in (loc.get("T2_top_pairs") or [])[:5]], T5_top_cells=[x for x in (loc.get("T5_top_cells") or [])[:5]], T1_top=[x for x in (loc.get("T1_top_benchmarks") or [])[:5]])
    s1 = J(f"{root}/W4d/step1.json"); dl = J(f"{root}/W4d/deletion_test.json"); vc = J(f"{root}/W4/verdict_C2.json")
    if s1:
        R["W4d"] = dict(n_F=s1["n_F"], F=sorted(s1["F"]), thresholds=s1["thresholds_99"], obs_maxima=s1.get("obs_maxima"))
    if dl:
        pr = dl["primary_all_converged_nulls"]
        R["W4d"] = (R.get("W4d") or {}) | dict(rows_deleted=dl["sub_info"]["rows_deleted"], rows_kept=dl["sub_info"]["rows_kept"], n_null_used=dl["n_null_used"],
                                              after={t: pr[t] for t in pr})
    if vc: R["C2"] = dict(verdict=vc.get("verdict"), text=vc.get("verdict_text"))
    # ---------- WA
    a1 = J(f"{root}/WA/a1.json", f"{DOCS}/WA/a1.json" if root == "runs/W" else None); ex = J(f"{root}/WA_ext/ext.json")
    if a1:
        try:
            pr = {k: x for k, x in a1["pairs"].items() if k != "orig"}
            ws = [x["units"]["pooled"]["width_ratio"] for x in pr.values()]; sc = [x["units"]["pooled"]["scores"] for x in pr.values()]
            R["WA_a1"] = dict(n_pairs=len(pr), width_min=min(w["min"] for w in ws), width_max=max(w["max"] for w in ws),
                              width_median_range=[min(w["median"] for w in ws), max(w["median"] for w in ws)],
                              S2_max=max(z["all"]["S2_count"] for z in sc), S3_max=max(z["all"]["S3_count"] for z in sc), max_rel_shift=max(z["all"]["max_rel_shift"] for z in sc),
                              top10_same=all(z["S4"]["top10_same"] for z in sc), max_pair_change=max(z["S4"]["max_pair_change"] for z in sc),
                              max_shift_points=max(x["units"]["pooled"]["mean_shift"]["max_abs_points"] for x in pr.values()),
                              pairs=[f"{x['low']} / {x['high']}" for x in pr.values()], n_unstable=sum(bool(x.get("unstable")) for x in pr.values()))
        except Exception as e: R["WA_a1"] = dict(error=repr(e))
    if ex:
        prs = [x for x in ex["pairs"] if x["id"] != "orig"]
        R["WA_ext"] = dict(n_pairs=len(prs), max_abs_gap_change=max(x["max_abs_gap_change"] for x in prs), argmax=max(prs, key=lambda x: x["max_abs_gap_change"])["id"],
                           median_gap_change_range=[min(x["median_abs_gap_change"] for x in prs), max(x["median_abs_gap_change"] for x in prs)],
                           width_ratio_median_range=[min(x["width_ratio_median"] for x in prs), max(x["width_ratio_median"] for x in prs)],
                           gap_width_ratio_frontier_median_range=[min(x["gap_width_ratio_frontier"]["median"] for x in prs), max(x["gap_width_ratio_frontier"]["median"] for x in prs)],
                           lambda_range=[min(x["common_scale_lambda"] for x in prs), max(x["common_scale_lambda"] for x in prs)],
                           n_bad_draws=sum(x["n_bad_draws"] for x in prs), scale_cv_orig=[x for x in ex["pairs"] if x["id"] == "orig"][0]["scale_cv"],
                           pairs=[dict(id=x["id"], low=x["low"], high=x["high"], width_ratio_median=x["width_ratio_median"], max_abs_gap_change=x["max_abs_gap_change"]) for x in prs],
                           crashed_2d=ex.get("crashed_2d"), n_2d_reversed=sum(bool(x["reversed"]) for x in ex.get("all_2d", [])))
    # ---------- W5
    s = J(f"{root}/W5/sensitivity.json"); vj = J(f"{root}/W5/verdict_C1.json"); jj = J(f"{root}/W5J/w5j_scores.json"); pa = J(f"{root}/W5/ppc_arms.json")
    if s:
        def sh(sc):
            if not sc: return None
            return dict(all_S1=g(sc, "all", "S1"), all_S2=g(sc, "all", "S2_count"), all_S3=g(sc, "all", "S3_count"), frontier_S2=g(sc, "frontier", "S2_count"), frontier_S3=g(sc, "frontier", "S3_count"),
                        sparse_S2=g(sc, "sparse", "S2_count"), sparse_S3=g(sc, "sparse", "S3_count"), dense_S2=g(sc, "dense", "S2_count"), dense_S3=g(sc, "dense", "S3_count"),
                        S4_top10_same=g(sc, "S4", "top10_same"), S4_max_pair_change=g(sc, "S4", "max_pair_change"), S4_pass=g(sc, "S4", "pass_"),
                        all_pass=bool(g(sc, "all", "S1_pass") and g(sc, "all", "S2_pass") and g(sc, "all", "S3_pass")), frontier_pass=bool(g(sc, "frontier", "S1_pass") and g(sc, "frontier", "S2_pass") and g(sc, "frontier", "S3_pass")),
                        all_max_rel_shift=g(sc, "all", "max_rel_shift"), frontier_max_rel_shift=g(sc, "frontier", "max_rel_shift"))
        R["W5"] = dict(verdict=g(s, "C1_verdict"), s2_limit=s.get("s2_shift"), S5_joint_flagged=s.get("S5_joint_flagged_strata"), flagged_hyperpriors=s.get("flagged_hyperpriors"),
                       noise_floor=s.get("noise_floor"), entries={k: dict(resolved=v.get("resolved"), converged=v.get("converged")) | (sh(v.get("scores")) or {}) for k, v in s["entries"].items()},
                       PR=dict(run=g(s, "PR", "run"), converged=g(s, "PR", "converged")) | (sh(g(s, "PR", "scores")) or {}))
        if jj: R["W5"]["J2"] = sh(g(jj, "scores", "J2"))
        if vj: R["W5"]["verdict_file"] = vj
        # shifts in ECI points from the saved draws
        try:
            from lib import fit as fm, sens_metrics as sm
            names = fm.load_eci(f"{root}/W2/seed12345.nc")[1]; strata = json.load(open("runs/strata.json"))
            d0 = np.load(f"{root}/W5/P0.npz")["eci"].astype(float); m0 = d0.mean(0); anc = np.array([n in sm.ANCHORS for n in names]); fr = np.array([n in set(strata["frontier"]) for n in names])
            low = (m0 < 100) & ~anc; pts = {}
            for k in ("P8", "P9", "P10", "P1", "P2", "P3", "P4", "P5", "P6", "P7", "X1", "X2"):
                f = f"{root}/W5/{k}.npz"
                if not os.path.exists(f): continue
                mk = np.load(f)["eci"].astype(float).mean(0); dd = mk - m0
                pts[k] = dict(n_below_100=int(low.sum()), mean_shift_below_100=float(dd[low].mean()), max_abs_shift=float(np.abs(dd[~anc]).max()), max_shift_model=names[int(np.argmax(np.abs(dd) * ~anc))],
                              frontier_max_abs_shift=float(np.abs(dd[fr & ~anc]).max()), frontier_mean_shift=float(dd[fr & ~anc].mean()))
            R["W5"]["points"] = pts
            R["W5"]["rank_corr_min_scored"] = min(v["all_S1"] for k, v in R["W5"]["entries"].items() if k.startswith("P") and v.get("all_S1") is not None)
        except Exception as e: R["W5"]["points_error"] = repr(e)
    if pa:
        R["W5_ppc"] = {k: dict(rejected=[t for t, pv in v["p_maxT_adjusted"].items() if pv < 0.01], p_adj={t: pv for t, pv in v["p_maxT_adjusted"].items()}) for k, v in pa.items() if isinstance(v, dict) and "p_maxT_adjusted" in v}
    return R


if __name__ == "__main__":
    out = dict(epoch=stage("runs/W"), eee=stage("runs/EEE"))
    json.dump(out, open("runs/EEE/headline.json", "w"), indent=1, default=str)
    for k in out["epoch"]:
        print("==", k); print(" E:", json.dumps(out["epoch"].get(k), default=str)[:900]); print(" X:", json.dumps(out["eee"].get(k), default=str)[:900])
