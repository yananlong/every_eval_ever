"""A3 (plan M11a, block WA; exploratory, no verdict): the W5 prior-sensitivity grid under other anchor pairs and anchor values.
Post-processing of the saved W5 posterior draws only; no sampling. Run from eci_work/v11. Writes runs/W/W5A/w5_anchor.json,
runs/W/W5A/chart_data.json and runs/W/W5A/summary.md.

Conventions (as runs/wa_w5_anchor.py and tools/wa_extend.py):
- Draws: the W5 .npz hold per-draw ECI only (float32); PR and J2 come from their .nc (eci, full 4 x 4,000 draws). Every anchored
  scale is a per-draw positive affine function of the raw capability, so re-anchoring the ECI draws equals re-anchoring the raw
  capability draws; this is checked on the thinned raw capability kept in each .nc and on the full raw capability of PR and J2.
- Pairs: the eight of anchor_pairs.json (orig + seven, incl. Full) and the two exploratory X pairs of wa_extend.py
  (X-lowGPT5 = GPT-4o mini -> GPT-5, X-lowTop = GPT-4o mini -> top model by P0 mean). Targets: W5 P0 posterior-mean ECI of the
  two anchor models (130/150 for orig).
- Scores: wa_anchor.score_vs_base around the frozen sens_metrics.score (S1 and S4 on all models; S2 and S3 with the models that
  are anchors in either anchoring removed from every stratum). Strata from runs/strata.json, s2_shift from sensitivity.json.
"""
import sys, json, time, warnings
from pathlib import Path
sys.path.insert(0, "runs"); warnings.filterwarnings("ignore")
import numpy as np, xarray as xr
from scipy.stats import spearmanr
from lib import anchors as A, sens_metrics as sm, fit as fm
import wa_anchor as W

t0 = time.time(); log = lambda *a: print(f"{time.time() - t0:7.1f}s", *a, flush=True)
W5, OUT = Path("runs/W/W5"), Path("runs/W/W5A"); OUT.mkdir(parents=True, exist_ok=True)
SENS = json.loads((W5 / "sensitivity.json").read_text()); S2 = float(SENS["s2_shift"])
J2S = json.loads(Path("runs/W/W5J/w5j_scores.json").read_text())
DEFENSIBLE = ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10"]
STRESS = ["X1", "X2"]; EXPL = ["PR", "J2"]
MOVERS = ["P8", "P9", "PR", "J2"]
STRATA = ("all", "frontier", "sparse", "dense"); CORE = ("all", "frontier", "sparse")
ORIG_LIMITS = dict(all=12, frontier=1, sparse=3, dense=9)

# ---------------- load ----------------
names = [str(x) for x in xr.open_datatree("runs/W/W2/seed12345.nc")["posterior"].to_dataset()["model"].values]
M = len(names); io = [names.index(a) for a in A.ORIG]
src = {"P0": "P0.npz", "P0b": "P0b.npz", **{k: f"{k}.npz" for k in ("P1", "P2", "P4", "P5", "P6", "P7", "P8", "X1", "X2")},
       "P9": "P9_retry3.npz", "P10": "P10_retry3.npz", "P3": "P3.npz",
       "P9_first": "P9.npz", "P10_first": "P10.npz"}   # the *_first arrays (8,000 draws per chain) are what sensitivity.json scored
D = {k: np.load(W5 / f)["eci"].astype("float64") for k, f in src.items()}
for k, nc in (("PR", W5 / "PR.nc"), ("J2", Path("runs/W/W5J/J2/J2.nc"))):
    e, nm, _ = fm.load_eci(nc); assert nm == names; D[k] = e.astype("float64"); src[k] = str(nc)
log("loaded", {k: v.shape for k, v in D.items()})
P0 = D["P0"]; m0 = P0.mean(0)
masks = W.strata_masks(names)
df_counts = A.obs_counts(names)

# ---------------- raw-capability equivalence checks ----------------
def nc_flat(path, var):
    p = xr.open_datatree(path)["posterior"].to_dataset()
    assert [str(x) for x in p["model"].values] == names
    return p[var].stack(s=("chain", "draw")).transpose("s", "model").to_numpy().astype("float64"), p.sizes["chain"], p.sizes["draw"]

raw_check = {}
lo_x = names.index("GPT-4o mini")
for k in ("P0", "P8", "P9", "P1", "PR", "J2"):
    path = {"P9": W5 / "P9_retry3.nc", "PR": W5 / "PR.nc", "J2": Path("runs/W/W5J/J2/J2.nc")}.get(k, W5 / f"{k}.nc")
    cap, nch, ndr = nc_flat(path, "capability"); ec, _, _ = nc_flat(path, "eci")
    top = int(np.argmax(m0))
    a1, _, _ = A.reanchor(cap, lo_x, top, 120.0, 170.0); a2, _, _ = A.reanchor(ec, lo_x, top, 120.0, 170.0)
    rec = dict(nc=str(path), n_draws=int(cap.shape[0]), max_abs_diff_reanchor_raw_vs_eci=float(np.nanmax(np.abs(a1 - a2))))
    # the .nc eci are the .npz eci at the thinning index (w5_agg.save_nc: linspace(0, n_draw-1, 500) per chain)
    if k not in ("PR", "J2"):
        full = D[k]; per = full.shape[0] // nch
        idx = np.concatenate([c * per + np.linspace(0, per - 1, ndr).astype(int) for c in range(nch)])
        rec["max_abs_diff_nc_eci_vs_npz"] = float(np.abs(full[idx] - ec).max())
        b1, _, _ = A.reanchor(full[idx], lo_x, top, 120.0, 170.0)
        rec["max_abs_diff_reanchor_npz_vs_raw"] = float(np.nanmax(np.abs(b1 - a1)))
    raw_check[k] = rec; del cap, ec, a1, a2
log("raw check", raw_check)

# ---------------- pairs ----------------
wa = A.jload("../../docs/research/eci-prior-fit-checks/results/W/WA/anchor_pairs.json")["pairs"]
pairs = [dict(id=p["id"], low=p["low"], high=p["high"], source="WA (M11a rule)") for p in wa]
top_name = names[int(np.argmax(m0))]
pairs += [dict(id="X-lowGPT5", low="GPT-4o mini", high="GPT-5", source="wa_extend.py (exploratory)"),
          dict(id="X-lowTop", low="GPT-4o mini", high=top_name, source="wa_extend.py (exploratory)")]
for p in pairs:
    p["il"], p["ih"] = names.index(p["low"]), names.index(p["high"])
    p["tl"], p["th"] = (130.0, 150.0) if p["id"] == "orig" else (float(m0[p["il"]]), float(m0[p["ih"]]))

below100 = np.where((m0 < 100) & ~np.isin(np.arange(M), io))[0]
fr_list = [i for i in np.argsort(-m0) if masks["frontier"][i]]          # strata.json frontier models, P0 order (original anchoring)
fr_top, fr_20 = fr_list[0], fr_list[-1]
log("below-100 models", len(below100), "frontier", len(fr_list), names[fr_top], names[fr_20], "top by P0 mean", top_name)


def score_pair(dk, d0, excl, new):
    """wa_anchor.score_vs_base, with NaN rows (non-positive maps) dropped from each fit separately so that fits of different
    draw counts (P9_first, P10_first: 32,000) can be scored; for equal counts and no NaN rows it is score_vs_base exactly."""
    if len(dk) == len(d0): return W.score_vs_base(dk, d0, names, masks, excl, new, S2)
    dk = dk[~np.isnan(dk).any(1)]; d0 = d0[~np.isnan(d0).any(1)]
    a = sm.score(dk, d0, names, masks, S2)
    nb = [f"m{i}" for i in range(M)]
    for j, i in enumerate(new[:2]): nb[i] = sm.ANCHORS[j]
    drop = np.zeros(M, bool); drop[[i for i in excl if i not in new]] = True
    b = sm.score(dk, d0, nb, {k: v & ~drop for k, v in masks.items()}, S2)
    out = dict(S4={k: v for k, v in a["S4"].items() if not k.startswith("p_top10")}, n_draws=int(len(dk)))
    for s in STRATA:
        o = dict(n=b[s]["n"], S1=a[s]["S1"], S1_pass=a[s]["S1_pass"])
        for k in ("S2_count", "S2_limit", "S2_pass", "S3_count", "S3_limit", "S3_pass", "max_rel_shift", "median_width_ratio"): o[k] = b[s][k]
        out[s] = o
    return out


def flags(sc):
    f = {s: {k: bool(sc[s][k]) for k in ("S1_pass", "S2_pass", "S3_pass")} for s in STRATA}
    f["S4"] = bool(sc["S4"]["pass_"]); return f


def failing(f, strata=STRATA):
    out = [f"{s}:{k[:2]}" for s in strata for k in ("S1_pass", "S2_pass", "S3_pass") if not f[s][k]]
    return out + ([] if f["S4"] else ["S4"])


def c1_fail_strata(sc):
    """The C1 rule's per-prior failure list (w5_sensitivity.py step 6): strata among all/frontier/sparse failing S1-S3, plus S4."""
    f = [s for s in CORE if not (sc[s]["S1_pass"] and sc[s]["S2_pass"] and sc[s]["S3_pass"])]
    return f + ([] if sc["S4"]["pass_"] else ["S4"])


def fixed_limit_flags(sc):
    """S2/S3 judged against the original-anchoring limits (12/1/3/9) instead of floor(0.05 n) of the reduced stratum."""
    return {s: dict(S2=sc[s]["S2_count"] <= ORIG_LIMITS[s], S3=sc[s]["S3_count"] <= ORIG_LIMITS[s]) for s in STRATA}


def s1_excl(dk, d0, excl):
    """S1 with the anchors of both anchorings removed from each stratum (robustness column; the plan's S1 keeps them)."""
    mk, m_0 = dk.mean(0), d0.mean(0); keep = ~np.isin(np.arange(M), excl)
    return {s: float(spearmanr(mk[masks[s] & keep], m_0[masks[s] & keep]).statistic) for s in STRATA}


def movement(dk, d0, excl):
    """Point quantities for a mover arm against P0 on one anchoring (both re-anchored the same way)."""
    mk, mb = dk.mean(0), d0.mean(0); sh = mk - mb
    keep = np.array([i for i in range(M) if i not in excl])
    low = np.array([i for i in below100 if i not in excl]); fr = np.array([i for i in fr_list if i not in excl])
    w0 = A.widths(d0)
    iu = np.triu_indices(len(keep), 1); dg = (sh[keep][:, None] - sh[keep][None, :])[iu]
    ifr = np.triu_indices(len(fr), 1); dgf = (sh[fr][:, None] - sh[fr][None, :])[ifr]
    lowset = np.isin(keep, low); frset = np.isin(keep, fr)
    A_, B_ = np.meshgrid(np.arange(len(keep)), np.arange(len(keep)), indexing="ij"); A_, B_ = A_[iu], B_[iu]
    lf = (lowset[A_] & frset[B_]) | (frset[A_] & lowset[B_]); ll = lowset[A_] & lowset[B_]
    absdg = np.abs(dg)
    big = absdg > 2.0
    gap_p0 = mb[fr_top] - mb[fr_20]; gap_k = mk[fr_top] - mk[fr_20]
    return dict(
        low_end=dict(n=int(len(low)), mean_shift=float(sh[low].mean()), min_shift=float(sh[low].min()), max_shift=float(sh[low].max()),
                     mean_shift_in_P0_widths=float((sh[low] / w0[low]).mean()), p0_mean_eci_range=[float(mb[low].min()), float(mb[low].max())]),
        frontier=dict(n=int(len(fr)), mean_shift=float(sh[fr].mean()), max_abs_shift=float(np.abs(sh[fr]).max()),
                      top_minus_20th_p0=float(gap_p0), top_minus_20th_arm=float(gap_k), stretch_points=float(gap_k - gap_p0),
                      stretch_ratio=float(gap_k / gap_p0)),
        gaps=dict(n_pairs_all=int(len(dg)), median_abs_change_all=float(np.median(absdg)), max_abs_change_all=float(absdg.max()),
                  n_pairs_frontier=int(len(dgf)), median_abs_change_frontier=float(np.median(np.abs(dgf))), max_abs_change_frontier=float(np.abs(dgf).max()),
                  median_abs_change_low_low=float(np.median(absdg[ll])), median_abs_change_low_frontier=float(np.median(absdg[lf])),
                  max_abs_change_low_frontier=float(absdg[lf].max()),
                  n_pairs_change_gt2=int(big.sum()), share_gt2_involving_low_end=float((big & (lowset[A_] | lowset[B_])).sum() / max(big.sum(), 1)),
                  share_gt2_involving_frontier=float((big & (frset[A_] | frset[B_])).sum() / max(big.sum(), 1))),
        max_abs_shift_model=names[int(keep[np.argmax(np.abs(sh[keep]))])], max_abs_shift=float(np.abs(sh[keep]).max()))


# ---------------- 1. reproduction under the original anchoring ----------------
repro = {}
ref = {k: SENS["entries"][k]["scores"] for k in SENS["entries"] if SENS["entries"][k]["resolved"]}
ref["PR"] = SENS["PR"]["scores"]; ref["J2"] = J2S["scores"]["J2"]
ref["P9_first"] = ref["P9"]; ref["P10_first"] = ref["P10"]
for k, sc_ref in ref.items():
    sc = sm.score(D[k], P0, names, masks, S2)
    diffs = []
    for s in STRATA:
        for f in ("n", "S1", "S1_pass", "S2_count", "S2_limit", "S2_pass", "S3_count", "S3_limit", "S3_pass", "max_rel_shift", "median_width_ratio"):
            a, b = sc[s][f], sc_ref[s][f]
            if (isinstance(a, float) and abs(a - b) > 1e-9) or (not isinstance(a, float) and a != b): diffs.append(f"{s}.{f}: {a} vs {b}")
    for f in ("top10_same", "max_pair_change", "pass_"):
        a, b = sc["S4"][f], sc_ref["S4"][f]
        if (isinstance(a, float) and abs(a - b) > 1e-9) or (not isinstance(a, float) and a != b): diffs.append(f"S4.{f}: {a} vs {b}")
    repro[k] = dict(matches=not diffs, mismatches=diffs)
log("reproduction", {k: v["matches"] for k, v in repro.items()})

# ---------------- 2. anchor identity, 3. anchor values (identity fixed); one worker per pair ----------------
ARMS = DEFENSIBLE + STRESS + EXPL + ["P0b", "P9_first", "P10_first"]
VALSETS = [(100.0, 150.0), (0.0, 100.0), (130.0, 140.0)]


def do_pair(p):
    il, ih, tl, th = p["il"], p["ih"], p["tl"], p["th"]
    excl = sorted(set(io) | {il, ih}); new = [il, ih]
    base, _, bad0 = A.reanchor(P0, il, ih, tl, th)
    rec = dict(low=p["low"], high=p["high"], target_low=tl, target_high=th, source=p["source"],
               low_obs=int(df_counts[il]), high_obs=int(df_counts[ih]), p0_nonpositive_draws=bad0,
               excluded_from_S2_S3=[names[i] for i in excl], arms={})
    for k in ARMS:
        dk, _, bad = A.reanchor(D[k], il, ih, tl, th)
        sc = score_pair(dk, base, excl, new)
        r = dict(nonpositive_draws=bad, scores=sc, flags=flags(sc), failing=failing(flags(sc)), c1_fail_strata=c1_fail_strata(sc),
                 fixed_limit=fixed_limit_flags(sc), S1_anchors_excluded=s1_excl(dk, base, excl))
        if k in MOVERS: r["movement"] = movement(dk, base, excl)
        if k in ("P8", "PR"):   # within-arm invariance of draw ranks and P(top 10) (positive affine per draw)
            ok = ~np.isnan(dk).any(1)
            r["invariance"] = dict(max_abs_rank_diff=int(np.abs(A.rank_matrix(D[k][ok]) - A.rank_matrix(dk[ok])).max()),
                                   max_abs_ptop10_diff=float(np.abs(A.top10_p(D[k][ok]) - A.top10_p(dk[ok])).max()))
        rec["arms"][k] = r
        del dk
    rec["n"] = {s: rec["arms"]["P8"]["scores"][s]["n"] for s in STRATA}
    rec["limits"] = {s: rec["arms"]["P8"]["scores"][s]["S2_limit"] for s in STRATA}
    # C1 rule applied on this anchoring (descriptive; the verdict stays on the original anchoring)
    fails = {k: rec["arms"][k]["c1_fail_strata"] for k in DEFENSIBLE if k != "P3" and rec["arms"][k]["c1_fail_strata"]}
    sens = [k for k, f in fails.items() if any(x in ("all", "frontier", "S4") for x in f)]
    rec["C1_rule"] = dict(failures_by_prior=fails, sensitive_priors=sens, falsified=bool(sens),
                          frontier_or_S4_failures=[k for k, f in fails.items() if any(x in ("frontier", "S4") for x in f)])
    print(f"{time.time() - t0:7.1f}s pair", p["id"], p["low"], "->", p["high"], "n", rec["n"], "C1", rec["C1_rule"], flush=True)
    ref_base = base
    out = {}
    for tl2, th2 in VALSETS:
        k_rel = (th2 - tl2) / (th - tl)
        base2, _, _ = A.reanchor(P0, il, ih, tl2, th2)
        dev = dict(max_dev_S1=0.0, max_dev_max_rel_shift=0.0, max_dev_median_width_ratio=0.0, max_dev_S4_pair_change=0.0,
                   count_or_flag_mismatches=[])
        mv = {}
        for k in ARMS:
            dk, _, _ = A.reanchor(D[k], il, ih, tl2, th2)
            sc = score_pair(dk, base2, excl, new); sr = rec["arms"][k]["scores"]
            for s in STRATA:
                dev["max_dev_S1"] = max(dev["max_dev_S1"], abs(sc[s]["S1"] - sr[s]["S1"]))
                dev["max_dev_max_rel_shift"] = max(dev["max_dev_max_rel_shift"], abs(sc[s]["max_rel_shift"] - sr[s]["max_rel_shift"]))
                dev["max_dev_median_width_ratio"] = max(dev["max_dev_median_width_ratio"], abs(sc[s]["median_width_ratio"] - sr[s]["median_width_ratio"]))
                for f in ("S1_pass", "S2_count", "S2_pass", "S3_count", "S3_pass"):
                    if sc[s][f] != sr[s][f]: dev["count_or_flag_mismatches"].append(f"{k}.{s}.{f}")
            dev["max_dev_S4_pair_change"] = max(dev["max_dev_S4_pair_change"], abs(sc["S4"]["max_pair_change"] - sr["S4"]["max_pair_change"]))
            if sc["S4"]["pass_"] != sr["S4"]["pass_"] or sc["S4"]["top10_same"] != sr["S4"]["top10_same"]: dev["count_or_flag_mismatches"].append(f"{k}.S4")
            if k in MOVERS:
                m = movement(dk, base2, excl); m_ref = rec["arms"][k]["movement"]
                mv[k] = dict(low_end_mean_shift=m["low_end"]["mean_shift"], low_end_range=[m["low_end"]["min_shift"], m["low_end"]["max_shift"]],
                             frontier_stretch_points=m["frontier"]["stretch_points"], frontier_stretch_ratio=m["frontier"]["stretch_ratio"],
                             gap_median_abs_change_all=m["gaps"]["median_abs_change_all"], gap_max_abs_change_all=m["gaps"]["max_abs_change_all"],
                             dev_from_k_times_pair_targets=float(max(abs(m["low_end"]["mean_shift"] - k_rel * m_ref["low_end"]["mean_shift"]),
                                                                    abs(m["frontier"]["stretch_points"] - k_rel * m_ref["frontier"]["stretch_points"]))))
            del dk
        dev["max_dev_affine_map_of_P0"] = float(np.nanmax(np.abs(base2 - (tl2 + k_rel * (ref_base - tl)))))
        out[f"{tl2:g},{th2:g}"] = dict(factor_vs_pair_targets=k_rel, factor_vs_orig_20=(th2 - tl2) / 20.0, invariance=dev, movers=mv)
    print(f"{time.time() - t0:7.1f}s values", p["id"], {v: (o["invariance"]["max_dev_S1"], len(o["invariance"]["count_or_flag_mismatches"])) for v, o in out.items()}, flush=True)
    return p["id"], rec, out


import multiprocessing as mp
with mp.get_context("fork").Pool(5) as pool:
    got = pool.map(do_pair, pairs, chunksize=1)
res_pairs = {pid: rec for pid, rec, _ in got}; values = {pid: out for pid, _, out in got}

# flag changes vs orig
changes = {}
for pid, rec in res_pairs.items():
    ch = {}
    for k in ARMS:
        f0, fk = res_pairs["orig"]["arms"][k]["flags"], rec["arms"][k]["flags"]
        if f0 != fk:
            # attribute: does the change vanish when S2/S3 are judged against the original limits?
            fl = rec["arms"][k]["fixed_limit"]; fl0 = res_pairs["orig"]["arms"][k]["fixed_limit"]
            ch[k] = dict(original=failing(f0), this_pair=failing(fk), same_under_original_limits=bool(fl == fl0 and f0["S4"] == fk["S4"]
                         and all(f0[s]["S1_pass"] == fk[s]["S1_pass"] for s in STRATA)))
    c1_0 = {k: res_pairs["orig"]["arms"][k]["c1_fail_strata"] for k in ARMS}
    c1_k = {k: rec["arms"][k]["c1_fail_strata"] for k in ARMS}
    changes[pid] = dict(arms_with_changed_flags=ch, n_changed=len(ch),
                        c1_status_changes={k: dict(original=c1_0[k], this_pair=c1_k[k]) for k in ARMS if c1_0[k] != c1_k[k]})
log("changes", {k: (v["n_changed"], list(v["c1_status_changes"])) for k, v in changes.items()})

# ---------------- 4. P3 (non-converged; exploratory) ----------------
p3 = {pid: dict(failing=rec["arms"]["P3"]["failing"], c1_fail_strata=rec["arms"]["P3"]["c1_fail_strata"]) for pid, rec in res_pairs.items()}

R = dict(note="A3 (plan M11a), exploratory: enters no verdict; the C1 verdict stays on the original anchoring. Post-processing of W5 draws only.",
         inputs=src, s2_shift=S2, n_draws={k: int(v.shape[0]) for k, v in D.items()}, raw_capability_check=raw_check,
         reproduction_original_anchoring=repro, below100=dict(n=int(len(below100)), models=[names[i] for i in below100]),
         frontier_models_p0_order=[names[i] for i in fr_list], pairs=res_pairs, flag_changes_vs_original=changes,
         values=values, P3_exploratory=p3,
         value_invariance_argument="With the pair fixed, target values (T_l', T_h') replace (T_l, T_h) by ECI' = T_l' + k (ECI - T_l) in every draw of "
                                   "both fits, k = (T_h' - T_l')/(T_h - T_l) > 0 a constant; means, quantiles and widths map by the same k, so the "
                                   "S2 ratio |dmean|/W0 and the S3 ratio Wk/W0 are unchanged, Spearman of means (S1) and within-draw orders (S4) are unchanged.")
(OUT / "w5_anchor.json").write_text(json.dumps(R, indent=1, default=float) + "\n")

# chart data: per pair, mover low-end mean shift and frontier stretch (pair targets), plus per-model shifts in W units
cd = dict(description="Per anchor pair (targets = W5 P0 posterior means), for P8, P9, PR, J2 against P0 re-anchored the same way: mean shift of the "
                      "models below P0 ECI 100 (original anchoring), frontier stretch (top minus 20th of the strata.json frontier), median |gap change| "
                      "over frontier pairs and over all pairs (ECI points).",
          pairs=[dict(id=pid, low=r["low"], high=r["high"], tl=round(r["target_low"], 2), th=round(r["target_high"], 2),
                      arms={k: dict(low_end_mean_shift=round(r["arms"][k]["movement"]["low_end"]["mean_shift"], 2),
                                    frontier_stretch=round(r["arms"][k]["movement"]["frontier"]["stretch_points"], 2),
                                    gap_med_all=round(r["arms"][k]["movement"]["gaps"]["median_abs_change_all"], 2),
                                    gap_med_frontier=round(r["arms"][k]["movement"]["gaps"]["median_abs_change_frontier"], 2)) for k in MOVERS})
                 for pid, r in res_pairs.items()])
(OUT / "chart_data.json").write_text(json.dumps(cd, indent=1) + "\n")
log("wrote", OUT)
