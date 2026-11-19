"""WA (plan M11a, R28): A1 re-anchoring of the W2 draws on alternative anchor pairs, A2 anchor-free standardisation.
Post-processing only (numpy; no sampling).  Run from v11/:  nice -n 19 runs/.venv/bin/python runs/wa_anchor.py
Needs runs/W/WA/anchor_pairs.json (written by wa_anchor_select.py before any result)."""
import sys, json, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
from lib import anchors as A, sens_metrics as sm

OUT = Path("runs/W/WA")
STRATA = ("all", "frontier", "sparse", "dense")
log = lambda *a: print(time.strftime("%H:%M:%S"), *a, flush=True)


def strata_masks(names, path="runs/strata.json"):
    st = json.loads(Path(path).read_text())
    return {k: np.array([n in set(st[k]) for n in names]) for k in STRATA}


def score_vs_base(dk, d0, names, masks, excl_idx, new_idx, s2_shift=sm.S2_SHIFT):
    """S1-S4 of dk against d0 through the frozen sens_metrics.score. S1 and S4 (anchors included) come from a call with the
    names as they are; S2 and S3 come from a second call in which the models in excl_idx (anchors in either anchoring) are
    removed from every stratum mask and the models in new_idx carry the names sens_metrics treats as anchors."""
    ok = ~np.isnan(dk).any(axis=1)
    dk, d0 = dk[ok], d0[ok]
    a = sm.score(dk, d0, names, masks, s2_shift)
    nb = [f"m{i}" for i in range(len(names))]
    for j, i in enumerate(new_idx[:2]): nb[i] = sm.ANCHORS[j]
    drop = np.zeros(len(names), bool); drop[[i for i in excl_idx if i not in new_idx]] = True
    mb = {k: v & ~drop for k, v in masks.items()}
    b = sm.score(dk, d0, nb, mb, s2_shift)
    out = dict(S4={k: v for k, v in a["S4"].items() if not k.startswith("p_top10")}, n_draws=int(ok.sum()))
    for s in STRATA:
        o = dict(n=b[s]["n"], S1=a[s]["S1"], S1_pass=a[s]["S1_pass"])
        for k in ("S2_count", "S2_limit", "S2_pass", "S3_count", "S3_limit", "S3_pass", "max_rel_shift", "median_width_ratio"):
            o[k] = b[s][k]
        out[s] = o
    return out


def compare(dk, d0, names, masks, excl_idx, new_idx):
    """Everything A1 and A2 report for one re-scaled draws array dk against the baseline d0 (same draw index)."""
    ok = ~np.isnan(dk).any(axis=1)
    dk, d0 = dk[ok], d0[ok]
    res = dict(scores=score_vs_base(dk, d0, names, masks, excl_idx, new_idx))
    w0, wk = A.widths(d0), A.widths(dk)
    keep = np.ones(len(names), bool); keep[list(excl_idx)] = False
    wr = wk / np.where(keep, w0, np.nan)
    wrk = wr[keep]
    lab = np.array(names)[keep]
    res["width_ratio"] = dict(median=float(np.median(wrk)), min=float(wrk.min()), max=float(wrk.max()),
                              argmin=str(lab[wrk.argmin()]), argmax=str(lab[wrk.argmax()]),
                              q05=float(np.quantile(wrk, .05)), q95=float(np.quantile(wrk, .95)),
                              **{f"median_{s}": float(np.nanmedian(wr[masks[s] & keep])) for s in STRATA})
    # frontier gaps and posterior-mean ranks
    order, g0 = A.frontier_gaps(d0)
    m0, mk = d0.mean(0), dk.mean(0)
    gk = mk[order[:-1]] - mk[order[1:]]
    res["top10"] = dict(models=[names[i] for i in order], gaps_base=g0.tolist(), gaps_k=gk.tolist(),
                        gap_ratio=(gk / g0).tolist(), max_abs_gap_change=float(np.abs(gk - g0).max()),
                        max_rel_gap_change=float((np.abs(gk - g0) / g0).max()),
                        order_k_mean_same=bool((np.argsort(-mk)[:10] == order).all()))
    r0, rk = np.argsort(np.argsort(-m0)) + 1, np.argsort(np.argsort(-mk)) + 1
    dr = np.abs(r0 - rk)
    res["mean_rank"] = dict(max_abs_change=int(dr.max()), n_changed=int((dr > 0).sum()), model_of_max=str(names[int(dr.argmax())]),
                            max_change_top20=int(dr[r0 <= 20].max()), n_changed_top20=int((dr[r0 <= 20] > 0).sum()),
                            mean_abs_change=float(dr.mean()))
    # shift of posterior means in units of baseline width, and in ECI points
    res["mean_shift"] = dict(max_abs_points=float(np.abs(mk - m0)[keep].max()), median_abs_points=float(np.median(np.abs(mk - m0)[keep])))
    return res


def main():
    doc = A.jload(OUT / "anchor_pairs.json")
    pairs = doc["pairs"]
    E, C = [], []
    names = None
    for s in A.SEEDS:
        e, c, n = A.load_seed(s)
        names = names or n; assert n == names
        E.append(e); C.append(c)
    E, C = np.vstack(E), np.vstack(C)
    nd = E.shape[0] // len(A.SEEDS)
    sl = [slice(k * nd, (k + 1) * nd) for k in range(len(A.SEEDS))]
    masks = strata_masks(names)
    io = [names.index(a) for a in A.ORIG]
    # --- what the stored draws are: anchored (eci) and raw (capability)
    chk = dict(eci_anchor_values=[[float(E[:, i].min()), float(E[:, i].max())] for i in io],
               eci_stored_vs_recomputed_from_capability_max_abs=float(np.abs(A.reanchor(C, io[0], io[1], 130.0, 150.0)[0] - E).max()),
               capability_range=[float(C.min()), float(C.max())],
               pooled_p0_mean_eci_of_anchors=[float(E[:, i].mean()) for i in io])
    log("stored draws", chk)
    units = {"pooled": slice(0, E.shape[0])} | {f"seed{s}": sl[k] for k, s in enumerate(A.SEEDS)}
    # baseline P_ij matrices computed once per unit
    base_cache = {}
    def base(u):
        if u not in base_cache:
            d0 = E[units[u]]; base_cache[u] = (A.rank_matrix(d0), A.p_matrix(d0), A.top10_p(d0))
        return base_cache[u]
    a1 = dict(pairs={}, stored_draw_checks=chk, s2_shift=sm.S2_SHIFT)
    for p in pairs:
        i_lo, i_hi, tl, th = p["low_idx"], p["high_idx"], p["target_low"], p["target_high"]
        log("pair", p["id"], p["low"], "/", p["high"])
        Ek, b_e, bad = A.reanchor(E, i_lo, i_hi, tl, th)
        Ck, b_c, bad_c = A.reanchor(C, i_lo, i_hi, tl, th)       # same map from the raw capability
        rec = dict(low=p["low"], high=p["high"], target_low=tl, target_high=th, n_nonpositive_spread_draws=bad,
                   unstable=bool(bad > 0), from_eci_vs_from_capability_max_abs=float(np.nanmax(np.abs(Ek - Ck))))
        # scale factor of the raw-to-ECI map for this pair, against the original pair
        bo = 20.0 / (C[:, io[1]] - C[:, io[0]])
        rec["scale_factor"] = dict(mean=float(np.nanmean(b_c)), cv=float(np.nanstd(b_c) / np.nanmean(b_c)), cv_original=float(bo.std() / bo.mean()),
                                   corr_with_original_log_b=float(np.corrcoef(np.log(b_c[~np.isnan(b_c)]), np.log(bo[~np.isnan(b_c)]))[0, 1]))
        aw = A.widths(Ek[~np.isnan(Ek).any(axis=1)]); w0 = A.widths(E)
        rec["anchor_widths_pooled"] = dict(original_anchors_under_this_pair=[float(aw[i]) for i in io], new_anchors_under_original=[float(w0[i_lo]), float(w0[i_hi])])
        excl = sorted(set(io) | {i_lo, i_hi}); new = [i_lo, i_hi]
        rec["units"] = {}
        for u, sli in units.items():
            d0, dk = E[sli], Ek[sli]
            r0, P0, T0 = base(u)
            ok = ~np.isnan(dk).any(axis=1)
            if ok.all():
                inv = dict(n_draws=int(ok.sum()), max_abs_rank_diff=int(np.abs(r0 - A.rank_matrix(dk)).max()),
                           n_rank_mismatch_draws=int((r0 != A.rank_matrix(dk)).any(axis=1).sum()),
                           max_abs_pij_diff=float(np.abs(P0 - A.p_matrix(dk)).max()), max_abs_ptop10_diff=float(np.abs(T0 - A.top10_p(dk)).max()))
            else:
                inv = A.invariance(d0, dk)
            r = compare(dk, d0, names, masks, excl, new) if p["id"] != "orig" else dict(scores=None)
            r["invariance"] = inv
            if p["id"] == "orig": r["max_abs_diff_vs_stored_eci"] = float(np.abs(dk - d0).max())
            rec["units"][u] = r
        a1["pairs"][p["id"]] = rec
    # ---- A2: anchor-free standardisation
    log("A2")
    pm = E.mean(0); q1, q3 = np.quantile(pm, [.25, .75])
    refs = {"zscore": (float(pm.mean()), float(pm.std(ddof=1))), "robust_median_iqr": (float(np.median(pm)), float((q3 - q1) / 1.349))}
    a2 = dict(reference_constants={k: dict(center=v[0], scale=v[1]) for k, v in refs.items()}, variants={})
    for vn, robust in (("zscore", False), ("robust_median_iqr", True)):
        mean_ref, sd_ref = refs[vn]
        Z = A.zscore(C, robust=robust)
        Zfrom_E = A.zscore(E, robust=robust)
        X = mean_ref + sd_ref * Z                           # ECI-equivalent units
        v = dict(z_from_eci_vs_from_capability_max_abs=float(np.abs(Z - Zfrom_E).max()), units={})
        for u, sli in units.items():
            d0, dx, dz = E[sli], X[sli], Z[sli]
            r0, P0, T0 = base(u)
            r = compare(dx, d0, names, masks, list(io), [])
            r["invariance"] = dict(n_draws=int(dx.shape[0]), max_abs_rank_diff=int(np.abs(r0 - A.rank_matrix(dx)).max()),
                                   max_abs_pij_diff=float(np.abs(P0 - A.p_matrix(dx)).max()), max_abs_ptop10_diff=float(np.abs(T0 - A.top10_p(dx)).max()))
            sw = A.widths(dz)
            r["anchors_in_z_units"] = {n: dict(mean=float(dz[:, i].mean()), width90=float(sw[i]), width90_eci_equiv=float(sd_ref * sw[i]),
                                              sd_to_width_note="width in z units; ECI-equivalent = sd_ref * z-width")
                                       for n, i in zip(A.ORIG, io)}
            r["median_width_z_units_nonanchor"] = float(np.median(np.delete(sw, io)))
            v["units"][u] = r
        a2["variants"][vn] = v
    (OUT / "a1.json").write_text(json.dumps(a1, indent=1) + "\n")
    (OUT / "a2.json").write_text(json.dumps(a2, indent=1) + "\n")
    log("done")


if __name__ == "__main__":
    main()
