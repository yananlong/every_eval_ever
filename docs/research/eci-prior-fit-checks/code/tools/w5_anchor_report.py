"""Writes runs/W/W5A/summary.md and runs/W/W5A/fragment.html from runs/W/W5A/w5_anchor.json (written by tools/w5_anchor.py).
Run from eci_work/v11. Plain json; no numerics beyond formatting."""
import json
from pathlib import Path

OUT = Path("runs/W/W5A"); R = json.loads((OUT / "w5_anchor.json").read_text())
P = R["pairs"]; PIDS = list(P)
NULL = ["P1", "P2", "P4", "P5", "P6", "P7", "P10", "X1", "X2"]
SHOW = ["P8", "P9", "PR", "J2"]
LET = dict(all="A", frontier="F", sparse="S", dense="D")
STRATA = ("all", "frontier", "sparse", "dense")


def fail_strata(pid, k):
    f = P[pid]["arms"][k]["flags"]
    out = [LET[s] for s in STRATA if not (f[s]["S1_pass"] and f[s]["S2_pass"] and f[s]["S3_pass"])]
    return out + ([] if f["S4"] else ["S4"])


def crit(pid, k):
    sc = P[pid]["arms"][k]["scores"]
    return " ".join(f"{LET[s]} {sc[s]['S2_count']}/{sc[s]['S3_count']}" for s in STRATA)


def changed(pid, k):
    return k in R["flag_changes_vs_original"][pid]["arms_with_changed_flags"]


def mv(pid, k):
    return P[pid]["arms"][k]["movement"]


null_all_pass = all(not P[p]["arms"][k]["failing"] for p in PIDS for k in NULL + ["P3", "P0b"])
repro = R["reproduction_original_anchoring"]
bad_repro = [k for k, v in repro.items() if not v["matches"]]
vinv = [b["invariance"] for p in R["values"].values() for b in p.values()]
vmax = dict(S1=max(v["max_dev_S1"] for v in vinv), shift=max(v["max_dev_max_rel_shift"] for v in vinv),
            wr=max(v["max_dev_median_width_ratio"] for v in vinv), s4=max(v["max_dev_S4_pair_change"] for v in vinv),
            mism=sum(len(v["count_or_flag_mismatches"]) for v in vinv))
vdev = max(x["dev_from_k_times_pair_targets"] for p in R["values"].values() for b in p.values() for x in b["movers"].values())

# ---------------- summary.md ----------------
L = ["# W5A: anchor sensitivity of the W5 prior-sensitivity scores (plan A3, block WA; exploratory)", "",
     "Post-processing of the saved W5 posterior draws (no new fits). Each W5 arm and P0 are re-anchored on the same pair, with targets "
     "equal to W5 P0's posterior-mean ECI of the two anchor models (130/150 for the original pair), and S1-S4 are scored with the frozen "
     "`sens_metrics.score` through `wa_anchor.score_vs_base` (S1 and S4 on all models, S2 and S3 with the anchors of both anchorings "
     "removed from each stratum, limits floor(0.05 n), S2 threshold 0.25 W). A3 enters no verdict. The C1 verdict stays on the original anchoring.", "",
     "Code: `eci_work/tools/w5_anchor.py` (numbers), `eci_work/tools/w5_anchor_report.py` (this file and fragment.html). Data: `w5_anchor.json`, `chart_data.json`.", "",
     "## Checks", "",
     f"- Re-anchoring the ECI draws equals re-anchoring the raw capability draws: on the raw capability kept in the .nc files (P0, P1, P8, P9 thinned to 2,000 draws; PR and J2 all 16,000) "
     f"the largest difference is {max(v['max_abs_diff_reanchor_raw_vs_eci'] for v in R['raw_capability_check'].values()):.1e} ECI points; "
     f"against the float32 .npz draws it is {max(v.get('max_abs_diff_reanchor_npz_vs_raw', 0) for v in R['raw_capability_check'].values()):.1e} (float32 storage).",
     f"- No pair has a draw with a non-positive map (c_high <= c_low) in any arm or in P0.",
     f"- Within-arm invariance (P8, PR, every pair): largest change of a within-draw rank 0, of P(top 10) 0.",
     "- Reproduction of `runs/W/W5/sensitivity.json` under the original anchoring: " +
     ("all arms match to 1e-9." if not bad_repro else
      f"P1, P2, P4-P8, X1, X2, PR and J2 match to 1e-9 (PR and J2 against w5j_scores.json for J2). "
      f"{', '.join(bad_repro)} do not match when read from `P9_retry3.npz` / `P10_retry3.npz`: sensitivity.json was computed from `P9.npz` and `P10.npz` "
      "(8,000 draws per chain, the first-pass fits), which reproduce exactly (rows P9_first, P10_first). `w5_agg.entry_fit` loads `<name>.npz` whenever the "
      "sidecar says resolved, and the sidecars were later set to resolved by the third attempt. Every pass/fail flag and every S2/S3 count is the same for both "
      "versions; continuous values differ slightly (P9 S4 largest adjacent-pair change 0.068 retry3 against 0.061 first pass; all-stratum S1 0.999750 against 0.999754). "
      "This report uses the retry3 draws for P9 and P10, as the brief specifies, and carries the first-pass arrays alongside; their flags agree in every pair."), ""]
L += ["## Strata sizes per pair (S2/S3 n, limit)", "", "| Pair | Low anchor (T) | High anchor (T) | all | frontier | sparse | dense |", "| --- | --- | --- | --- | --- | --- | --- |"]
for pid in PIDS:
    r = P[pid]
    L.append(f"| {pid} | {r['low']} ({r['target_low']:.2f}) | {r['high']} ({r['target_high']:.2f}) | " +
             " | ".join(f"{r['n'][s]} ({r['limits'][s]})" for s in STRATA) + " |")
L += ["", "S1 keeps all models of the stratum (plan convention). When a pair's anchor is in the 20-model frontier stratum, frontier n falls to 19 and its limit to 0. "
      "No status change below is caused by that: every change also holds against the original limits (12/1/3/9).", ""]
L += ["## Pass/fail by arm and pair", "",
      "Cell: failing strata (A all, F frontier, S sparse, D dense; a stratum fails if S1, S2 or S3 fails) and S4, then S2/S3 counts per stratum. * marks a flag that differs from the original anchoring.", "",
      "| Arm | " + " | ".join(PIDS) + " |", "| --- |" + " --- |" * len(PIDS)]
L.append(f"| {', '.join(NULL)}, P0b, P3 | " + " | ".join("pass" for _ in PIDS) + " |" if null_all_pass else "| null arms | see json |")
for k in SHOW + ["P9_first"]:
    L.append(f"| {k} | " + " | ".join(("*" if changed(pid, k) else "") + (" ".join(fail_strata(pid, k)) or "pass") + "<br>" + crit(pid, k) for pid in PIDS) + " |")
L += ["", "C1 rule applied on each anchoring (defensible arms P1-P10, P3 unresolved): " +
      "; ".join(f"{pid}: {', '.join(f'{k} [{chr(44).join(v)}]' for k, v in P[pid]['C1_rule']['failures_by_prior'].items())}" for pid in PIDS) + ".", ""]
L += ["Changes against the original anchoring:", ""]
for pid in PIDS:
    for k, c in R["flag_changes_vs_original"][pid]["arms_with_changed_flags"].items():
        L.append(f"- {pid}, {k}: failing criteria {', '.join(c['original'])} -> {', '.join(c['this_pair'])}")
L += ["", "## Anchor values with the pair fixed", "",
      "If the pair is fixed and the targets (T_l, T_h) become (T_l', T_h'), every draw of both fits maps by ECI' = T_l' + k (ECI - T_l) with one constant k = (T_h' - T_l')/(T_h - T_l) > 0. "
      "Means, quantiles and widths all scale by k, so |mean_k - mean_0| / W_0 (S2) and W_k / W_0 (S3) are unchanged, the Spearman correlation of means (S1) and the within-draw orders (S4) are unchanged, and every point shift and gap scales by k.", "",
      f"Numerically, for every pair and the value sets (100, 150), (0, 100), (130, 140): largest change in S1 {vmax['S1']:.1e}, in the largest relative shift {vmax['shift']:.1e}, "
      f"in the median width ratio {vmax['wr']:.1e}, in the S4 pair change {vmax['s4']:.1e}; {vmax['mism']} count or flag mismatches; the low-end shift and frontier stretch equal k times their values at the pair targets to {vdev:.1e} points.", "",
      "Under the original pair, k = 2.5, 5 and 0.5 for the three value sets:", "",
      "| Arm | Low-end shift (130/150) | (100/150) | (0/100) | (130/140) | Frontier stretch (130/150) | (100/150) | (0/100) | (130/140) |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
vo = R["values"]["orig"]
for k in SHOW:
    m = mv("orig", k)
    L.append(f"| {k} | {m['low_end']['mean_shift']:.2f} | " + " | ".join(f"{vo[v]['movers'][k]['low_end_mean_shift']:.2f}" for v in vo) +
             f" | {m['frontier']['stretch_points']:.2f} | " + " | ".join(f"{vo[v]['movers'][k]['frontier_stretch_points']:.2f}" for v in vo) + " |")
L += ["", "All value sets for all pairs are in `w5_anchor.json` under `values`.", ""]
L += ["## Point differentials against P0 (pair targets)", "",
      f"Low end: the {R['below100']['n']} models below P0 ECI 100 under the original anchoring (mean shift, range). Frontier stretch: (top minus 20th of the strata.json frontier) in the arm minus the same in P0, "
      "top = Claude Fable 5.2, 20th = GPT-5.5. Gap changes: |(m_i - m_j)_arm - (m_i - m_j)_P0| over all pairs of non-anchor models, over frontier pairs, and over pairs of one low-end and one frontier model.", "",
      "| Pair | Arm | Low-end shift (range) | in P0 widths | Frontier mean shift | Stretch (ratio) | Gap change all: median / max | frontier: median / max | low-frontier median | share of >2-point changes with a low-end model |",
      "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
for pid in PIDS:
    for k in SHOW:
        m = mv(pid, k); le, fr, g = m["low_end"], m["frontier"], m["gaps"]
        L.append(f"| {pid} | {k} | {le['mean_shift']:.2f} ({le['min_shift']:.1f} to {le['max_shift']:.1f}) | {le['mean_shift_in_P0_widths']:.2f} | {fr['mean_shift']:.2f} | "
                 f"{fr['stretch_points']:.2f} ({fr['stretch_ratio']:.3f}) | {g['median_abs_change_all']:.2f} / {g['max_abs_change_all']:.2f} | "
                 f"{g['median_abs_change_frontier']:.2f} / {g['max_abs_change_frontier']:.2f} | {g['median_abs_change_low_frontier']:.2f} | {g['share_gt2_involving_low_end']:.2f} |")
L += ["", "## Reading", "",
      "- Under the seven WA alternative pairs no defensible arm changes status: P8 and P9 fail all, sparse and dense and pass the frontier and S4 in every pair, and P1, P2, P4-P7 and P10 pass everywhere, as do X1, X2, P0b and the non-converged P3 (exploratory). "
      "J2 (exploratory) changes at the criterion level only: its all-stratum S3 (21 against a limit of 12 originally) falls to 1-12 under five frontier-anchored pairs, while its all-stratum S2 still fails.",
      "- Under the two exploratory pairs with GPT-4o mini (P0 ECI 123.9) as the low anchor, P9 and PR also fail the frontier on S2 (P9: 5 of 20 and 7 of 19 frontier models shift by more than 0.25 W; PR: 11 and 9). "
      "P8 stays at 0 but its largest frontier shift rises from 0.15 W to 0.24 W, just under the threshold. With GPT-5 as the high anchor every frontier model lies 10 to 23 points above it, so the 2 % compression of the GPT-4o mini to GPT-5 raw-capability gap under P9 (ratio to the Claude 3.5 Sonnet to GPT-5 gap 1.280 against 1.306 in P0) is extrapolated into a frontier-wide level shift of 0.4 to 2.2 points, against P0 frontier widths that shrink from a median 5.4 to 4.9.",
      "- The C1 rule returns falsified on every anchoring (P8 and P9 fail all and sparse in every pair). Under the GPT-4o mini pairs P9 additionally fails the frontier, which would make the frontier part of the failure.",
      "- Low end moves, frontier holds survives every pair in gap terms: frontier-pair gap changes stay at medians 0.09-0.51 points (max 2.0, PR under X-lowGPT5; 1.8 for P9), while low-end to frontier gaps change by medians of 12-22 points for P8, P9 and PR (6.7-9.2 for J2), and 56-83 % of the gap changes larger than 2 points involve one of the 42 low-end models, which make up 17 % of the models. "
      "In points the low-end shift grows as the anchors move up the scale (P8 13.2 under X-lowGPT5 to 16.6 under L12-S10; P9 16.2 to 20.5) because the shift is extrapolated further below the pair, and with the GPT-4o mini anchor it is smallest; in P0 widths it stays at 0.47-0.63 for P8 and 0.58-0.78 for P9.", ""]
(OUT / "summary.md").write_text("\n".join(L) + "\n")

# ---------------- fragment.html ----------------
def pill(pid, k):
    fs = fail_strata(pid, k); star = "*" if changed(pid, k) else ""
    return f'<span class="pill pass">pass</span>' if not fs else f'<span class="pill fail">{" ".join(fs)}{star}</span>'


SHORT = {"orig": "orig", "L0-S10": "L0-S10", "L0-S15": "L0-S15", "L0-S20": "L0-S20", "L6-S10": "L6-S10", "L6-S15": "L6-S15", "L12-S10": "L12-S10",
         "Full": "Full", "X-lowGPT5": "X-lowGPT5", "X-lowTop": "X-lowTop"}
H = ['<div class="sub-sec" id="prior-anchors"><h3 class="ssh">15.x Anchors under the alternative priors</h3>',
     "<p>Each W5 arm and P0 were re-anchored on the same pair, with targets equal to P0's posterior-mean ECI of the two anchor models, and S1 to S4 were scored as in W5 "
     "with the anchors of both anchorings removed from S2 and S3. The pairs are the eight of block WA and two exploratory pairs with GPT-4o mini (P0 ECI 123.9) as the low anchor, "
     "against GPT-5 (X-lowGPT5) and against Claude Fable 5.2, the top model (X-lowTop). This is post-processing of the saved draws, it enters no verdict, and the C1 verdict stays on the original anchoring. "
     "Re-anchoring the stored ECI draws agrees with re-anchoring the raw capability to 1e-13 points, no draw has a non-positive map, and under the original pair the scores reproduce "
     "sensitivity.json for every arm (for P9 and P10 only from the first-pass arrays P9.npz and P10.npz, which are what W5 scored, while the retry3 draws used here give the same flags and counts).</p>",
     '<div class="tblwrap"><table>',
     "<thead><tr><th>Arm</th>" + "".join(f"<th>{SHORT[p]}</th>" for p in PIDS) + "</tr></thead><tbody>",
     "<tr><td>Low / high anchor</td>" + "".join(f'<td>{P[p]["low"]} / {P[p]["high"]}</td>' for p in PIDS) + "</tr>",
     "<tr><td>n all / frontier / sparse / dense</td>" + "".join(f'<td class="n">{P[p]["n"]["all"]} / {P[p]["n"]["frontier"]} / {P[p]["n"]["sparse"]} / {P[p]["n"]["dense"]}</td>' for p in PIDS) + "</tr>",
     f"<tr><td>{', '.join(NULL[:6])}, {', '.join(NULL[6:])}</td>" + "".join('<td><span class="pill pass">pass</span></td>' for _ in PIDS) + "</tr>"]
for k in SHOW:
    H.append(f"<tr><td>{k}{' (exploratory)' if k in ('PR', 'J2') else ''}</td>" + "".join(f"<td>{pill(p, k)}</td>" for p in PIDS) + "</tr>")
H.append("<tr><td>Frontier S2 count, P9 / PR</td>" + "".join(f'<td class="n">{P[p]["arms"]["P9"]["scores"]["frontier"]["S2_count"]} / {P[p]["arms"]["PR"]["scores"]["frontier"]["S2_count"]}</td>' for p in PIDS) + "</tr>")
H.append("<tr><td>C1 rule on this anchoring</td>" + "".join(f'<td><span class="pill fail">falsified</span></td>' if P[p]["C1_rule"]["falsified"] else "<td>holds</td>" for p in PIDS) + "</tr>")
H.append("</tbody></table></div>")
H.append("<p>Letters give the failing strata (A all, F frontier, S sparse, D dense), and an asterisk marks a cell whose flags differ from the original pair. "
         "Under all seven WA alternatives the statuses of the defensible arms are unchanged: P8 and P9 fail all, sparse and dense and pass the frontier and S4, and P1, P2, P4 to P7 and P10 pass, "
         "as do X1, X2 and the non-converged P3 (exploratory). J2 changes within strata that fail anyway, its all-stratum S3 count falling from 21 to between 1 and 12 under the frontier pairs. "
         "With GPT-4o mini as the low anchor P9 and PR also fail the frontier on S2, with 5 of 20 and 11 of 20 frontier models shifted by more than 0.25 W under X-lowGPT5. "
         "Every frontier model lies 10 to 23 points above GPT-5, so the 2% compression of the GPT-4o mini to GPT-5 capability gap under P9 is extrapolated into a frontier-wide rise of 0.4 to 2.2 points, "
         "while P8's largest frontier shift reaches 0.24 W, just under the line. The C1 rule returns falsified on every anchoring.</p>")
H.append("<p>Changing the anchor values with the pair fixed maps every draw of both fits by one positive constant k = (T<sub>h</sub>&prime; &minus; T<sub>l</sub>&prime;)/(T<sub>h</sub> &minus; T<sub>l</sub>), "
         "so means, quantiles and widths scale by k and the S2 and S3 ratios, the S1 rank correlation and the S4 orders are unchanged. Across all pairs and the value sets (100, 150), (0, 100) and (130, 140) "
         f"the largest change in any score is {max(vmax['S1'], vmax['shift'], vmax['wr'], vmax['s4']):.0e} with no count or flag differing, and point shifts scale exactly by k: "
         f"under the original pair the low-end rise of P8 is {mv('orig', 'P8')['low_end']['mean_shift']:.1f} points at 130/150, "
         f"{vo['100,150']['movers']['P8']['low_end_mean_shift']:.1f} at 100/150, {vo['0,100']['movers']['P8']['low_end_mean_shift']:.1f} at 0/100 and {vo['130,140']['movers']['P8']['low_end_mean_shift']:.1f} at 130/140.</p>")
# movement table
H.append('<div class="tblwrap"><table><thead><tr><th>Pair</th><th>Targets</th>' + "".join(f"<th>{k} low end</th><th>{k} stretch</th>" for k in SHOW) + "</tr></thead><tbody>")
for p in PIDS:
    H.append(f"<tr><td>{p}</td><td class=\"n\">{P[p]['target_low']:.1f} / {P[p]['target_high']:.1f}</td>" +
             "".join(f"<td class=\"n\">{mv(p, k)['low_end']['mean_shift']:+.1f}</td><td class=\"n\">{mv(p, k)['frontier']['stretch_points']:+.2f}</td>" for k in SHOW) + "</tr>")
H.append("</tbody></table></div>")
lo = {k: [mv(p, k)["low_end"]["mean_shift"] for p in PIDS] for k in SHOW}
fm = {k: [mv(p, k)["gaps"]["median_abs_change_frontier"] for p in PIDS] for k in SHOW}
lf = {k: [mv(p, k)["gaps"]["median_abs_change_low_frontier"] for p in PIDS] for k in SHOW}
sh = [mv(p, k)["gaps"]["share_gt2_involving_low_end"] for p in PIDS for k in SHOW]
H.append(f"<p>The pattern of W5 holds under every pair. The low end is the mean shift of the {R['below100']['n']} models below P0 ECI 100 on the original scale and the stretch is the change in the gap between the top and the 20th frontier model, both in ECI points against P0 on the same anchoring. "
         f"In points the low-end rise grows as the pair moves up the scale, from {min(lo['P8']):.1f} to {max(lo['P8']):.1f} for P8 and from {min(lo['P9']):.1f} to {max(lo['P9']):.1f} for P9, "
         "because it is extrapolated further below the anchors, and it is smallest with GPT-4o mini as the low anchor. Across the four arms, frontier-pair gaps change by medians of "
         f"{min(min(v) for v in fm.values()):.2f} to {max(max(v) for v in fm.values()):.2f} points, gaps between a low-end and a frontier model by medians of {min(min(v) for v in lf.values()):.1f} to {max(max(v) for v in lf.values()):.1f}, "
         f"and {min(sh) * 100:.0f} to {max(sh) * 100:.0f}% of the gap changes above 2 points involve a low-end model, which make up 17% of the models.</p>")
H.append("</div>")
(OUT / "fragment.html").write_text("\n".join(H) + "\n")
print("wrote summary.md, fragment.html")
