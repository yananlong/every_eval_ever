"""BSEL aggregation: runs/W/BSEL/{summary.json, summary.md, chart_data.json, fragment.html} from runs/W/BSEL/fits/*.json.
Pass/fail uses the registered S2/S3 count limits of the full strata (12/1/3/9) even when the inclusion rule removes models from a stratum;
sens_metrics' own floor(0.05 n) limits are kept beside them.  Exploratory except A4 (optional, reported, no verdict)."""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bsel_common as C

LIM = dict(all=12, frontier=1, sparse=3, dense=9)
STRATA = ("all", "frontier", "sparse", "dense")
design = json.loads((C.OUT / "design.json").read_text())
FITS = C.OUT / "fits"


def passes(sc):
    o = {}
    for s in STRATA:
        v = sc[s]
        o[s] = dict(n=v["n"], S1=round(v["S1"], 5), S1_pass=v["S1_pass"], S2_count=v["S2_count"], S2_pass=v["S2_count"] <= LIM[s], S2_pass_floor_rule=v["S2_pass"],
                    S3_count=v["S3_count"], S3_pass=v["S3_count"] <= LIM[s], S3_pass_floor_rule=v["S3_pass"], max_rel_shift=round(v["max_rel_shift"], 4),
                    median_width_ratio=round(v["median_width_ratio"], 4))
        o[s]["S1_S3_pass"] = o[s]["S1_pass"] and o[s]["S2_pass"] and o[s]["S3_pass"]
    o["S4"] = dict(top10_same=sc["S4"]["top10_same"], max_pair_change=round(sc["S4"]["max_pair_change"], 4), pass_=sc["S4"]["pass_"])
    return o


def row(f, r):
    out = dict(id=f["id"], kind=f["kind"], drop=f["drop"], n_dropped_models=len(f["dropped_models"]), dropped_models=f["dropped_models"])
    if r is None: out.update(status="missing"); return out
    if r.get("unanchored"): out.update(status="unanchored"); return out
    if "compare" not in r: out.update(status="timeout_no_draws" if r.get("timeout") else "failed", attempts=r.get("attempts")); return out
    c = r["compare"]
    out.update(status="converged" if r["resolved"] else ("timeout" if r.get("timeout") else "unconverged"), used_attempt=r["used_attempt"],
               wall_s=sum(a.get("wall", a.get("child_wall", 0)) or 0 for a in r["attempts"]), n_models=r["n_models"], n_common=c["n_common"],
               metrics=passes(c["scores"]), top10=c["top10"], frontier={k: round(v, 3) for k, v in c["frontier"].items()},
               gaps=c["gaps"], shift=c["shift"], movers=c["movers"][:5], p_top10_changes=c["p_top10_changes"][:6], anchors=r["anchors"],
               last_attempt=r["attempts"][r["used_attempt"]].get("last_attempt"))
    out["affine"] = affine(f["id"])
    return out


P0M = None
def affine(fid):
    """OLS of refit posterior-mean ECI on P0 posterior-mean ECI over common non-anchor models (full-draw means from the npz):
    slope above 1 = the scale stretched relative to the anchor gap; residual = what a linear re-map does not explain."""
    global P0M
    if P0M is None:
        p = C.load_p0(); P0M = dict(zip(p["names"], p["eci"].mean(0)))
    z = np.load(FITS / f"{fid}.npz"); names = [str(x) for x in z["names"]]; m = z["mean"]
    keep = [i for i, n in enumerate(names) if n in P0M and n not in C.ANCHORS]
    x = np.array([P0M[names[i]] for i in keep]); y = m[keep]
    b, a = np.polyfit(x, y, 1); res = y - (a + b * x)
    hi = x >= np.sort(x)[-20]
    bf, af = np.polyfit(x[hi], y[hi], 1)
    low = x < 100.0
    return dict(low_end_n=int(low.sum()), low_end_mean_shift=round(float(np.mean(y[low] - x[low])), 3), slope=round(float(b), 4), intercept=round(float(a), 3), median_abs_resid=round(float(np.median(np.abs(res))), 3), max_abs_resid=round(float(np.max(np.abs(res))), 3),
                slope_top20=round(float(bf), 4))


def per_model(fid):
    """A4: posterior-mean ECI shift of every common model against P0 (full-draw means)."""
    affine(fid) if P0M is None else None
    z = np.load(FITS / f"{fid}.npz"); names = [str(x) for x in z["names"]]
    return {n: round(float(m - P0M[n]), 3) for n, m in zip(names, z["mean"]) if n in P0M}


rows = []
for f in design["fits"]:
    p = FITS / f"{f['id']}.json"
    rows.append(row(f, json.loads(p.read_text()) if p.exists() else None))
reruns = []
for p in sorted(FITS.glob("*__s*.json")):
    j = json.loads(p.read_text()); f0 = next(f for f in design["fits"] if f["id"] == j["design_id"])
    rr = row(dict(f0, id=j["id"]), j); rr.update(kind="rerun_" + f0["kind"], design_id=j["design_id"], seed=j["seed"]); reruns.append(rr)
rows_orig = rows
fails_seed12345_only = None
best = {rr["design_id"]: dict(rr, kind=rr["kind"].replace("rerun_", ""), substitutes=rr["design_id"]) for rr in reruns if rr.get("status") == "converged"}
rows = [best[r["id"]] if r.get("status") != "converged" and r["id"] in best else r for r in rows_orig]   # converged other-seed reruns replace non-converged/timed-out records
ok = [r for r in rows if r.get("status") == "converged"]
noconv = [r for r in rows_orig if r.get("status") in ("unconverged", "timeout", "timeout_no_draws", "failed")]

# noise reference: P0b (seed 22345) against P0, same metrics
p0 = C.load_p0()
ref = C.compare(np.load("runs/W/W5/P0b.npz")["eci"].astype("float64"), p0["names"], p0)
ref_row = dict(id="P0b", kind="seed_noise", status="reference", metrics=passes(ref["scores"]), frontier={k: round(v, 3) for k, v in ref["frontier"].items()}, gaps=ref["gaps"], shift=ref["shift"], top10=ref["top10"])


def fail_counts(rs):
    o = {}
    for s in STRATA:
        o[s] = {m: int(sum(not r["metrics"][s][m + "_pass"] for r in rs)) for m in ("S1", "S2", "S3")}
        o[s]["any_S1_S3"] = int(sum(not r["metrics"][s]["S1_S3_pass"] for r in rs))
    o["S4"] = int(sum(not r["metrics"]["S4"]["pass_"] for r in rs)); o["S4a_top10_set_changed"] = int(sum(not r["metrics"]["S4"]["top10_same"] for r in rs))
    o["n"] = len(rs); return o


kinds = dict(A4=[r for r in ok if r["kind"] == "A4_lobo"], LOBO_all57=[r for r in ok if r["kind"] in ("A4_lobo", "lobo")],
             cluster=[r for r in ok if r["kind"] == "cluster"], random=[r for r in ok if r["kind"] == "random"])
fails = {k: fail_counts(v) for k, v in kinds.items()}
ok12 = [r for r in rows_orig if r.get("status") == "converged"]
fails_seed12345_only = {k: fail_counts(v) for k, v in dict(A4=[r for r in ok12 if r["kind"] == "A4_lobo"], LOBO_all57=[r for r in ok12 if r["kind"] in ("A4_lobo", "lobo")]).items()}
fails_incl_unconverged = {k: fail_counts([r for r in rows_orig if "metrics" in r and r["kind"] in kk]) for k, kk in
                          dict(LOBO_all57=("A4_lobo", "lobo"), cluster=("cluster",), random=("random",)).items()}

lobo = sorted([r for r in rows if r["kind"] in ("A4_lobo", "lobo") and "metrics" in r], key=lambda r: -r["frontier"]["max_abs_shift"])
lobo_tab = [dict(benchmark=r["drop"][0], id=r["id"], status=r["status"], n_dropped_models=r["n_dropped_models"], frontier_max_abs_shift=r["frontier"]["max_abs_shift"],
                 frontier_max_rel_shift=r["frontier"]["max_rel_shift"], frontier_mean_signed_shift=r["frontier"]["mean_signed_shift"], stretch_change=r["frontier"]["stretch_change"],
                 frontier_median_abs_gap_change=round(r["gaps"]["frontier"]["median_abs_gap_change"], 4), frontier_max_abs_gap_change=round(r["gaps"]["frontier"]["max_abs_gap_change"], 4),
                 all_median_abs_gap_change=round(r["gaps"]["all"]["median_abs_gap_change"], 4), all_max_abs_shift=round(r["shift"]["max_abs_all"], 3),
                 top10_set_same=r["top10"]["set_same"], top10_order_same=r["top10"]["order_same"], entered=r["top10"]["entered"], left=r["top10"]["left"],
                 S_fail=[f"{m}:{s}" for s in STRATA for m in ("S1", "S2", "S3") if not r["metrics"][s][m + "_pass"]] + ([] if r["metrics"]["S4"]["pass_"] else ["S4"]))
            for r in lobo]

a4 = []
for r in [r for r in rows if r["kind"] == "A4_lobo" and "metrics" in r]:
    an = r["anchors"]; a4.append(dict(benchmark=r["drop"][0], status=r["status"], dropped_models=r["dropped_models"],
        cap_low_change=round(an["refit"]["cap_low_mean"] - an["p0"]["cap_low_mean"], 4), cap_high_change=round(an["refit"]["cap_high_mean"] - an["p0"]["cap_high_mean"], 4),
        spread_p0=round(an["p0"]["spread_mean"], 4), spread_refit=round(an["refit"]["spread_mean"], 4), spread_ratio=round(an["refit"]["spread_mean"] / an["p0"]["spread_mean"], 4),
        b_ratio=round(an["refit"]["b_mean"] / an["p0"]["b_mean"], 4), b_cv_p0=round(an["p0"]["b_sd_over_mean"], 4), b_cv_refit=round(an["refit"]["b_sd_over_mean"], 4),
        eci_shift_median_abs=round(r["shift"]["median_abs_all"], 3), eci_shift_max_abs=round(r["shift"]["max_abs_all"], 3), eci_shift_mean_signed=round(r["shift"]["mean_signed_all"], 3),
        median_width_ratio=round(r["shift"]["median_width_ratio_all"], 4), spearman_shift_vs_p0eci=round(r["shift"]["spearman_shift_vs_p0eci"], 3),
        top_mover=r["movers"][0], metrics=r["metrics"], per_model_shift=per_model(r["id"])))


def quint_summary(rs):
    q = np.array([[x["median_abs_shift"] for x in r["shift"]["by_p0_quintile"]] for r in rs]); qr = np.array([[x["median_rel_shift"] for x in r["shift"]["by_p0_quintile"]] for r in rs])
    wr = np.array([[x["median_width_ratio"] for x in r["shift"]["by_p0_quintile"]] for r in rs])
    return dict(median_over_refits_of_median_abs_shift=np.round(np.median(q, 0), 3).tolist(), max_over_refits_of_median_abs_shift=np.round(np.max(q, 0), 3).tolist(),
                median_over_refits_of_median_rel_shift=np.round(np.median(qr, 0), 4).tolist(), median_over_refits_of_median_width_ratio=np.round(np.median(wr, 0), 4).tolist(),
                p0_eci_ranges=[x["p0_eci_range"] for x in rs[0]["shift"]["by_p0_quintile"]] if rs else None)


low_vs_frontier = {k: quint_summary(v) for k, v in kinds.items() if v}
low_vs_frontier["P0b_seed_noise"] = quint_summary([ref_row])

model_moves = {}
for r in ok:
    for m in r["movers"]: model_moves.setdefault(m["model"], []).append((r["id"], round(m["shift"], 2)))
frequent_movers = sorted(([k, len(v), v[:6]] for k, v in model_moves.items()), key=lambda x: -x[1])[:15]
top10_entries = {}
for r in ok:
    for n in r["top10"]["entered"]: top10_entries.setdefault(n, []).append(r["id"])
top10_exits = {}
for r in ok:
    for n in r["top10"]["left"]: top10_exits.setdefault(n, []).append(r["id"])

walls = [r["wall_s"] for r in rows if "wall_s" in r]
summary = dict(note="Exploratory benchmark-selection sensitivity under Epoch's model; A4 is the plan's optional item (reported, no verdict). Baseline P0 (W5).",
               limits_used=LIM, n_fits=len(rows), status_counts_seed12345={s: sum(r.get("status") == s for r in rows_orig) for s in ("converged", "unconverged", "timeout", "timeout_no_draws", "failed", "unanchored", "missing")},
               unconverged=[dict(id=r["id"], status=r["status"], last_attempt=r.get("last_attempt")) for r in noconv],
               fit_wall_s=dict(median=float(np.median(walls)) if walls else None, max=float(np.max(walls)) if walls else None, total=float(np.sum(walls)) if walls else None),
               fail_counts_converged=fails, fail_counts_converged_seed12345_only=fails_seed12345_only, substituted_by_rerun=sorted(best), fail_counts_incl_unconverged=fails_incl_unconverged, P0b_reference=ref_row, A4=a4, lobo_ranked_by_frontier_max_shift=lobo_tab,
               reruns_other_seed=reruns, clusters=[r for r in rows if r["kind"] == "cluster"], random=[r for r in rows if r["kind"] == "random"], low_vs_frontier=low_vs_frontier,
               frequent_large_movers=frequent_movers, top10_entries=top10_entries, top10_exits=top10_exits, design=dict(rng_seed=design["rng_seed"], random_k=design["random_k"], F=design["F"], clusters=design["clusters"]))
(C.OUT / "summary.json").write_text(json.dumps(summary, indent=1, default=str))

chart = dict(description="BSEL chart data. refits: one entry per refit. lobo: per benchmark (57).",
             refits=[dict(id=r["id"], kind=r["kind"], status=r.get("status"), n_dropped_models=r.get("n_dropped_models", 0),
                          **({} if "metrics" not in r else dict(
                              S={s: dict(S1=r["metrics"][s]["S1"], S2=r["metrics"][s]["S2_count"], S3=r["metrics"][s]["S3_count"], pass_=r["metrics"][s]["S1_S3_pass"]) for s in STRATA},
                              S4=r["metrics"]["S4"], stretch_p0=r["frontier"]["stretch_rank1_minus_rank20_p0"], stretch=r["frontier"]["stretch_rank1_minus_rank20_k"],
                              stretch_change=r["frontier"]["stretch_change"], frontier_max_abs_shift=r["frontier"]["max_abs_shift"],
                              affine_slope=r.get("affine", {}).get("slope"), low_end_mean_shift=r.get("affine", {}).get("low_end_mean_shift"), affine_slope_top20=r.get("affine", {}).get("slope_top20"), top10_entered=r["top10"]["entered"], top10_left=r["top10"]["left"], top10_order_same=r["top10"]["order_same"],
                              quintile_median_abs_shift=[round(x["median_abs_shift"], 3) for x in r["shift"]["by_p0_quintile"]]))) for r in rows_orig + reruns + [ref_row]],
             lobo=[dict(benchmark=x["benchmark"], frontier_max_abs_shift=round(x["frontier_max_abs_shift"], 3), frontier_median_abs_gap_change=x["frontier_median_abs_gap_change"],
                        stretch_change=round(x["stretch_change"], 3), n_dropped_models=x["n_dropped_models"], a4=x["id"].startswith("A4_")) for x in lobo_tab])
(C.OUT / "chart_data.json").write_text(json.dumps(chart, indent=0, default=str))
print(json.dumps(dict(status=summary["status_counts_seed12345"], fails=fails, wall=summary["fit_wall_s"]), indent=1))
