"""PROV aggregation -> runs/EEE/PROV/{summary.json, chart_data.json}.  Run from the v11 root (container python).  Pass/fail limits as BSEL (12/1/3/9)."""
import json, sys
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr
sys.path.insert(0, str(Path(__file__).resolve().parent))
import prov_common as P
OUT, FITS = P.OUT, P.OUT / "fits"
LIM = dict(all=12, frontier=1, sparse=3, dense=9); STRATA = ("all", "frontier", "sparse", "dense"); SEED_SD = 0.25
D = P.design(); st = P.B.strata()
p0 = P.B.load_p0(); ee = P.load_ref(P.EEE_REF_NC, P.EEE_REF_NPZ)
names = p0["names"]; assert names == ee["names"]
M = len(names); idx = {n: i for i, n in enumerate(names)}
anchor = np.array([n in P.ANCHORS for n in names]); na = ~anchor
fmask = np.array([n in set(st["frontier"]) for n in names]); smask = {s: np.array([n in set(st[s]) for n in names]) for s in ("all", "frontier", "sparse", "dense")}
p0m, p0w = p0["eci"].mean(0), np.subtract(*np.quantile(p0["eci"], [0.95, 0.05], axis=0))
eem, eew = ee["eci"].mean(0), np.subtract(*np.quantile(ee["eci"], [0.95, 0.05], axis=0))

# model-level exposure: cells with a real choice (>= 2 distinct values in the pool) per variant
cells = [tuple(c) for c in D["cells"]]
nmulti = {}; poolrange = {}
for V in "RIO":
    v = D["variants"][V]; a = np.zeros(M); r = np.zeros(M)
    for (m, b), pv in zip(cells, v["pool_values"]):
        if len(set(pv)) > 1: a[idx[m]] += 1; r[idx[m]] += max(pv) - min(pv)
    nmulti[V], poolrange[V] = a, r
# per-model seed SD (3 W2 seeds on the EEE input) as a noise floor: ECI = 130 + 20 (cap - cap_low) / (cap_high - cap_low) per draw (Epoch's anchoring)
import xarray as xr
seedm = []
for s in (12345, 22345, 32345):
    pp = xr.open_datatree(f"runs/EEE/W2/seed{s}.nc")["posterior"].to_dataset(); nn = [str(x) for x in pp["model"].values]
    cap = pp["capability"].stack(s=("chain", "draw")).transpose("s", "model").to_numpy()[:, [nn.index(n) for n in names]]
    lo, hi = cap[:, idx[P.ANCHORS[0]]], cap[:, idx[P.ANCHORS[1]]]
    seedm.append((130.0 + 20.0 * (cap - lo[:, None]) / (hi - lo)[:, None]).mean(0))
seed_sd_model = np.std(np.array(seedm), axis=0, ddof=1)


def passes(sc):
    o = {}
    for s in STRATA:
        v = sc[s]
        o[s] = dict(n=v["n"], S1=v["S1"], S1_pass=v["S1_pass"], S2_count=v["S2_count"], S2_pass=v["S2_count"] <= LIM[s], S3_count=v["S3_count"], S3_pass=v["S3_count"] <= LIM[s],
                    max_rel_shift=v["max_rel_shift"], median_width_ratio=v["median_width_ratio"])
        o[s]["S1_S3_pass"] = o[s]["S1_pass"] and o[s]["S2_pass"] and o[s]["S3_pass"]
    o["S4"] = dict(top10_same=sc["S4"]["top10_same"], max_pair_change=sc["S4"]["max_pair_change"], pass_=sc["S4"]["pass_"]); return o


def fail_counts(rs, key):
    o = {s: {m: int(sum(not r[key][s][m + "_pass"] for r in rs)) for m in ("S1", "S2", "S3")} for s in STRATA}
    for s in STRATA: o[s]["any_S1_S3"] = int(sum(not r[key][s]["S1_S3_pass"] for r in rs))
    o["S4"] = int(sum(not r[key]["S4"]["pass_"] for r in rs)); o["S4a_top10_set_changed"] = int(sum(not r[key]["S4"]["top10_same"] for r in rs)); o["n"] = len(rs); return o


def rng_(x): return [float(np.min(x)), float(np.max(x))] if len(x) else None


def load(rid):
    j = json.loads((FITS / f"{rid}.json").read_text()) if (FITS / f"{rid}.json").exists() else None
    if j is None: return dict(id=rid, status="missing")
    if "compare" not in j: return dict(id=rid, status="timeout_no_draws" if j.get("timeout") else "failed", attempts=j["attempts"])
    z = np.load(FITS / f"{rid}.npz"); assert [str(x) for x in z["names"]] == names
    la = j["attempts"][j["used_attempt"]]["last_attempt"]
    r = dict(id=rid, status="converged" if j["resolved"] else ("timeout" if j.get("timeout") else "unconverged"), n_attempts=len(j["attempts"]), used_attempt=j["used_attempt"],
             wall_s=float(sum(a.get("wall", 0) or 0 for a in j["attempts"])), last_attempt=la, models_failing_inclusion_rule=j["models_failing_inclusion_rule"], n_models=j["n_models"],
             mean=z["mean"], w=z["q95"] - z["q05"], lo=z["q05"], hi=z["q95"], diff=z["diff_mean"] if "diff_mean" in z else None, bench=[str(x) for x in z["bench_names"]] if "bench_names" in z else None,
             vs_p0=passes(j["compare"]["scores"]), vs_eee=passes(j["compare_eee"]["scores"]), T=j["T"],
             top10_p0=j["compare"]["top10"], top10_eee=j["compare_eee"]["top10"], gaps_p0=j["compare"]["gaps"], gaps_eee=j["compare_eee"]["gaps"],
             frontier_p0=j["compare"]["frontier"], frontier_eee=j["compare_eee"]["frontier"], shift_p0=j["compare"]["shift"], shift_eee=j["compare_eee"]["shift"],
             design=D["variants"][rid[0]]["rep_summary"][int(rid[1:]) - 1])
    return r


R = {V: [load(f"{V}{k + 1:02d}") for k in range(D["n_rep"][V])] for V in "RIO"}
summary = dict(note="Exploratory provenance resampling on EEE, under Epoch's model. Every refit: Epoch's 2,879 cells, only performance changes in the 688 covered cells; fit seed 12345, Epoch's unmodified priors, draws 4,000 per chain.",
               design=dict(n_cells=len(cells), per_variant={V: {k: D["variants"][V][k] for k in ("n_cells_in_pool", "n_cells_with_choice", "n_cells_with_distinct_values")} for V in "RIO"},
                           n_rep=D["n_rep"], rng_base=D["rng_base"], mean_cells_differing_from_epoch={V: float(np.mean([x["n_cells_differing_from_epoch_gt_0015"] for x in D["variants"][V]["rep_summary"]])) for V in "RIO"}),
               variants={}, T_reference=json.loads((OUT / "tcheck.json").read_text()) if (OUT / "tcheck.json").exists() else None)
chart = dict(models=[], rank_freq={}, T={})
topfreq = {}
for V in "RIO":
    rs = R[V]; ok = [r for r in rs if r["status"] == "converged"]
    sv = dict(n=len(rs), status_counts={s: sum(r["status"] == s for r in rs) for s in ("converged", "unconverged", "timeout", "timeout_no_draws", "failed", "missing")},
              attempts_hist={str(k): sum(r.get("n_attempts") == k for r in rs) for k in (1, 2, 3)},
              convergence=[dict(id=r["id"], status=r["status"], n_attempts=r.get("n_attempts"), divergences=(r.get("last_attempt") or {}).get("divergences"), max_rhat=(r.get("last_attempt") or {}).get("max_rhat"),
                                min_ess=(r.get("last_attempt") or {}).get("min_ess"), stage=(r.get("last_attempt") or {}).get("stage"), wall_s=r.get("wall_s")) for r in rs],
              inclusion_rule_models_dropped=dict(refits_with_any=sum(bool(r.get("models_failing_inclusion_rule")) for r in rs if "models_failing_inclusion_rule" in r),
                                                 models=sorted({m for r in rs for m in r.get("models_failing_inclusion_rule", [])})))
    if ok:
        mu = np.array([r["mean"] for r in ok]); W = np.array([r["w"] for r in ok]); wbar = W.mean(0)
        sd = mu.std(0, ddof=1) if len(ok) > 1 else np.zeros(M); rg = mu.max(0) - mu.min(0)
        def blk(mask):
            m = mask & na; i = np.where(m)[0]; j = i[np.argmax(sd[i])]
            return dict(n=int(m.sum()), max_sd=float(sd[j]), max_sd_model=names[j], max_sd_model_width=float(wbar[j]), max_sd_over_width=float(sd[j] / wbar[j]), max_sd_over_seed_sd=float(sd[j] / SEED_SD),
                        median_sd=float(np.median(sd[i])), mean_sd=float(sd[i].mean()), max_range=float(rg[i].max()), max_range_model=names[i[np.argmax(rg[i])]],
                        max_sd_over_width_any=float((sd[i] / wbar[i]).max()), max_sd_over_width_any_model=names[i[np.argmax(sd[i] / wbar[i])]], median_sd_over_width=float(np.median(sd[i] / wbar[i])),
                        n_sd_gt_seed_sd=int((sd[i] > SEED_SD).sum()), n_sd_gt_0_1_width=int((sd[i] / wbar[i] > 0.1).sum()), n_sd_gt_0_25_width=int((sd[i] / wbar[i] > 0.25).sum()))
        sv["spread"] = {s: blk(smask[s]) for s in STRATA}
        order = np.argsort(-sd * na)[:15]
        sv["top_models_by_sd"] = [dict(model=names[i], sd=float(sd[i]), range=float(rg[i]), width=float(wbar[i]), sd_over_width=float(sd[i] / wbar[i]), p0_eci=float(p0m[i]), n_multi_cells=int(nmulti[V][i]),
                                         seed_sd_eee=None if seed_sd_model is None else float(seed_sd_model[i]), frontier=bool(fmask[i])) for i in order]
        if seed_sd_model is not None:
            ex = np.sqrt(np.maximum(sd ** 2 - seed_sd_model ** 2, 0)); sv["excess_over_seed_noise"] = dict(max_excess_sd=float(ex[na].max()), max_excess_model=names[int(np.argmax(ex * na))],
                    median_ratio_sd_to_seed_sd=float(np.median((sd / np.maximum(seed_sd_model, 1e-9))[na])))
        # drivers
        sv["drivers"] = dict(spearman_sd_vs_n_multi_cells=float(spearmanr(sd[na], nmulti[V][na]).statistic), spearman_sd_vs_sum_pool_range=float(spearmanr(sd[na], poolrange[V][na]).statistic),
                             spearman_sd_vs_p0_eci=float(spearmanr(sd[na], p0m[na]).statistic), spearman_sd_over_width_vs_n_multi=float(spearmanr((sd / wbar)[na], nmulti[V][na]).statistic),
                             models_with_zero_multi_cells=dict(n=int((na & (nmulti[V] == 0)).sum()), median_sd=float(np.median(sd[na & (nmulti[V] == 0)])) if (na & (nmulti[V] == 0)).any() else None),
                             models_with_multi_cells=dict(n=int((na & (nmulti[V] > 0)).sum()), median_sd=float(np.median(sd[na & (nmulti[V] > 0)])) if (na & (nmulti[V] > 0)).any() else None))
        if all(r["diff"] is not None for r in ok):
            dm = np.array([r["diff"] for r in ok]); bn = ok[0]["bench"]; dsd = dm.std(0, ddof=1)
            nm_b = {b: 0 for b in bn}; rg_b = {b: 0.0 for b in bn}
            for (m, b), pv in zip(cells, D["variants"][V]["pool_values"]):
                if len(set(pv)) > 1: nm_b[b] += 1; rg_b[b] += max(pv) - min(pv)
            nbv = np.array([nm_b[b] for b in bn]); rgb = np.array([rg_b[b] for b in bn])
            # model exposure to re-estimated difficulty: mean difficulty SD over the benchmarks of its rows
            import pandas as pd
            from lib import data
            fi = data.fit_input(); bsd = dict(zip(bn, dsd)); expo = fi.assign(d=fi.benchmark.map(bsd)).groupby("Model").d.mean().reindex(names).to_numpy()
            sv["drivers"].update(spearman_sd_vs_mean_difficulty_sd_of_own_benchmarks=float(spearmanr(sd[na], expo[na]).statistic),
                                 benchmarks_by_difficulty_sd=[dict(benchmark=bn[i], difficulty_sd=float(dsd[i]), difficulty_mean=float(dm[:, i].mean()), n_multi_cells=int(nbv[i]), sum_pool_range=float(rgb[i])) for i in np.argsort(-dsd)[:12]],
                                 spearman_benchmark_difficulty_sd_vs_n_multi=float(spearmanr(dsd, nbv).statistic), spearman_benchmark_difficulty_sd_vs_sum_pool_range=float(spearmanr(dsd, rgb).statistic))
        # top 10
        t10 = [tuple(names[i] for i in np.argsort(-r["mean"])[:10]) for r in ok]; sets = [frozenset(t) for t in t10]
        base_p0 = frozenset(names[i] for i in np.argsort(-p0m)[:10]); base_e = frozenset(names[i] for i in np.argsort(-eem)[:10])
        from collections import Counter
        cs = Counter(sets); modal = cs.most_common(1)[0][0]
        rank = np.array([np.argsort(np.argsort(-r["mean"])) for r in ok])      # (rep, model) 0-based rank
        union = sorted({m for t in t10 for m in t} | set(base_p0) | set(base_e), key=lambda m: -eem[idx[m]])
        rf = {m: [int((rank[:, idx[m]] == k).sum()) for k in range(10)] for m in union}
        topfreq[V] = dict(order=[m for m in union], n=len(ok), freq=rf)
        sv["top10"] = dict(n_distinct_sets=len(cs), n_differing_from_p0_set=int(sum(s != base_p0 for s in sets)), n_differing_from_eee_det_set=int(sum(s != base_e for s in sets)),
                           n_differing_from_modal_set=int(sum(s != modal for s in sets)), modal_set_share=cs[modal] / len(ok), p0_set=sorted(base_p0), eee_det_set=sorted(base_e),
                           models_entering=Counter(m for s in sets for m in s - base_e).most_common(), models_leaving=Counter(m for s in sets for m in base_e - s).most_common(),
                           n_order_identical_to_eee_det=int(sum(list(t) == [names[i] for i in np.argsort(-eem)[:10]] for t in t10)),
                           rank_frequencies={m: dict(ranks_1_to_10=rf[m], outside_top10=len(ok) - sum(rf[m])) for m in union})
        # frontier gaps: 20 frontier models, ordered by the EEE-det posterior mean
        fi_ = [idx[n] for n in sorted(st["frontier"], key=lambda n: -eem[idx[n]])]
        g = mu[:, fi_[:-1]] - mu[:, fi_[1:]]; g_e = eem[fi_[:-1]] - eem[fi_[1:]]; g_0 = p0m[fi_[:-1]] - p0m[fi_[1:]]
        flip = (g < 0).mean(0)
        sv["frontier_gaps"] = dict(order=[names[i] for i in fi_], adjacent_gap_eee_det=g_e.tolist(), adjacent_gap_p0=g_0.tolist(), adjacent_gap_mean=g.mean(0).tolist(), adjacent_gap_sd=g.std(0, ddof=1).tolist(),
                                   max_adjacent_gap_sd=float(g.std(0, ddof=1).max()), median_adjacent_gap_sd=float(np.median(g.std(0, ddof=1))), order_flip_share_per_adjacent_pair=flip.tolist(), max_flip_share=float(flip.max()),
                                   n_pairs_with_any_flip=int((flip > 0).sum()),
                                   stretch_rank1_minus_rank20_sd=float(np.std([np.sort(r["mean"])[::-1][0] - np.sort(r["mean"])[::-1][19] for r in ok], ddof=1)),
                                   stretch_eee_det=float(np.sort(eem)[::-1][0] - np.sort(eem)[::-1][19]))
        # comparisons
        for key, lab in (("vs_p0", "p0"), ("vs_eee", "eee")):
            kk = "frontier_" + lab; ks = "shift_" + lab
            sv[key] = dict(fail_counts=fail_counts(ok, key),
                           spearman_all=rng_([r[key]["all"]["S1"] for r in ok]), spearman_frontier=rng_([r[key]["frontier"]["S1"] for r in ok]),
                           S2_count_all=rng_([r[key]["all"]["S2_count"] for r in ok]), S2_count_frontier=rng_([r[key]["frontier"]["S2_count"] for r in ok]),
                           S3_count_all=rng_([r[key]["all"]["S3_count"] for r in ok]), S3_count_frontier=rng_([r[key]["frontier"]["S3_count"] for r in ok]),
                           S3_count_all_median=float(np.median([r[key]["all"]["S3_count"] for r in ok])), S2_count_all_median=float(np.median([r[key]["all"]["S2_count"] for r in ok])),
                           max_pair_change_S4=rng_([r[key]["S4"]["max_pair_change"] for r in ok]),
                           frontier_max_abs_shift=rng_([r[kk]["max_abs_shift"] for r in ok]), frontier_max_rel_shift=rng_([r[kk]["max_rel_shift"] for r in ok]),
                           frontier_median_abs_gap_change=rng_([r["gaps_" + lab]["frontier"]["median_abs_gap_change"] for r in ok]), frontier_max_abs_gap_change=rng_([r["gaps_" + lab]["frontier"]["max_abs_gap_change"] for r in ok]),
                           all_median_abs_shift=rng_([r[ks]["median_abs_all"] for r in ok]), all_max_abs_shift=rng_([r[ks]["max_abs_all"] for r in ok]), all_mean_signed_shift=rng_([r[ks]["mean_signed_all"] for r in ok]),
                           top10_set_same_count=int(sum(r["top10_" + lab]["set_same"] for r in ok)))
        # T checks
        Tn = {}
        for lab in ("eee_null", "epoch_null"):
            Tn[lab] = {t: dict(observed=rng_([r["T"]["observed"][t] for r in ok]), observed_median=float(np.median([r["T"]["observed"][t] for r in ok])),
                               p_adjusted_median=float(np.median([r["T"]["p"][lab][t]["p_adjusted"] for r in ok])), p_adjusted_range=rng_([r["T"]["p"][lab][t]["p_adjusted"] for r in ok]),
                               n_reject_0_01=int(sum(r["T"]["p"][lab][t]["p_adjusted"] < 0.01 for r in ok)), n_adj_p_lt_0_05=int(sum(r["T"]["p"][lab][t]["p_adjusted"] < 0.05 for r in ok))) for t in ("T1", "T2", "T3", "T4", "T5", "T6", "T7")}
            Tn[lab]["R"] = ok[0]["T"]["p"][lab]["R"]
        sv["T"] = Tn
        sv["T5_by_replicate"] = [dict(id=r["id"], T5=r["T"]["observed"]["T5"], p_adj_eee_null=r["T"]["p"]["eee_null"]["T5"]["p_adjusted"], p_adj_epoch_null=r["T"]["p"]["epoch_null"]["T5"]["p_adjusted"],
                                      T3=r["T"]["observed"]["T3"], T3_p_adj_eee_null=r["T"]["p"]["eee_null"]["T3"]["p_adjusted"]) for r in ok]
        sv["T5_adj_p_eee_null_vs_cells_differing"] = float(spearmanr([r["T"]["observed"]["T5"] for r in ok], [r["design"]["n_cells_differing_from_epoch_gt_0015"] for r in ok]).statistic)
        for i in range(M):
            chart["models"].append(dict(variant=V, model=names[i], sd=float(sd[i]), range=float(rg[i]), width=float(wbar[i]), p0_eci=float(p0m[i]), eee_eci=float(eem[i]), n_multi=int(nmulti[V][i]),
                                        frontier=bool(fmask[i]), anchor=bool(anchor[i]), mean=float(mu[:, i].mean())))
        chart["T"][V] = [dict(id=r["id"], T5=r["T"]["observed"]["T5"], T3=r["T"]["observed"]["T3"], p5_eee=r["T"]["p"]["eee_null"]["T5"]["p_adjusted"], p5_epoch=r["T"]["p"]["epoch_null"]["T5"]["p_adjusted"]) for r in ok]
    summary["variants"][V] = sv
summary["reference"] = dict(p0_top10=[names[i] for i in np.argsort(-p0m)[:10]], eee_det_top10=[names[i] for i in np.argsort(-eem)[:10]], seed_sd_max_epoch=SEED_SD, seed_sd_max_eee=0.29,
                            eee_det_vs_p0=None)
# deterministic EEE fit vs P0 with the same metrics
c = P.B.compare(ee["eci"], names, p0); summary["reference"]["eee_det_vs_p0"] = passes(c["scores"])
summary["reference"]["eee_det_vs_p0_top10"] = dict(set_same=c["top10"]["set_same"], order_same=c["top10"]["order_same"])
chart["rank_freq"] = topfreq
(OUT / "summary.json").write_text(json.dumps(summary, indent=1, default=str)); (OUT / "chart_data.json").write_text(json.dumps(chart, separators=(",", ":"), default=str))
print(json.dumps({V: dict(status=summary["variants"][V]["status_counts"], spread=summary["variants"][V].get("spread", {}).get("all")) for V in "RIO"}, indent=1, default=str)[:3000])
