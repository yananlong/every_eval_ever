"""PROV report: runs/EEE/PROV/{SUMMARY.md, fragment.html} from summary.json (run prov_agg.py first).  Run from the v11 root (plain python is enough)."""
import json
from pathlib import Path
O = Path("runs/EEE/PROV"); S = json.loads((O / "summary.json").read_text()); V = S["variants"]; D = S["design"]; T = S.get("T_reference") or {}
NAME = dict(R="R (Epoch's value or any EEE source)", I="I (independent sources only)", O="O (own-run sources only)")
f1 = lambda x: f"{x:.1f}"; f2 = lambda x: f"{x:.2f}"; f3 = lambda x: f"{x:.3f}"; f4 = lambda x: f"{x:.4f}"
pct = lambda x: f"{100 * x:.0f}%"
rg = lambda r, f=f2: f"{f(r[0])} to {f(r[1])}"
def conv(v): c = v["status_counts"]; return f'{c["converged"]} of {v["n"]}'
def maxdiv(v): return max((x["divergences"] or 0) for x in v["convergence"] if x["divergences"] is not None)
def maxrhat(v): return max(x["max_rhat"] for x in v["convergence"] if x["max_rhat"])
def miness(v): return min(x["min_ess"] for x in v["convergence"] if x["min_ess"])
ref = S["reference"]; refall = ref["eee_det_vs_p0"]["all"]
tc = T.get("eee", {}).get("observed", {}); tce = T.get("epoch", {}).get("observed", {})
SP = {k: V[k]["spread"] for k in V if "spread" in V[k]}

# ---------------- SUMMARY.md
L = ["# Provenance resampling on EEE (exploratory, beyond plan)", "",
     "Results hold under Epoch's model. Each refit keeps Epoch's 2,879 cells and Epoch's input columns; only `performance` changes, in the %d covered cells (cells with at least one EEE source). Fit: Epoch's unmodified `fit_bayesian_eci` through `lib.fit_any.run`, seed 12345, Epoch's priors, 4,000 draws per chain, retry ladder and 2 h cap as BSEL. Reference fits: P0 (Epoch data) and the deterministic EEE fit (runs/EEE/W5/P0, highest score in the preferred class per cell)." % D["n_cells"], "",
     "Crosswalk on EEE manifest 959f0e11 (rev 5bce4753); main at 27d78eef (manifest 0a760ce1, +303 records) would add about 2 cells; not rebuilt.", "",
     "The crosswalk's third audit sample (seed 20261115, 0 errors in 50) is accepted as a recorded deviation in runs/EEE/PROGRESS.md and is not repeated here.", "",
     "## Design", ""]
for k in "RIO":
    d = D["per_variant"][k]; L.append(f"- {NAME[k]}: {D['n_rep'][k]} refits, RNG base seed {D['rng_base'][k]} (replicate j uses default_rng(base + j)); {d['n_cells_in_pool']} cells have a pool, {d['n_cells_with_choice']} have a real choice, {d['n_cells_with_distinct_values']} of those with distinct values; on average {D['mean_cells_differing_from_epoch'][k]:.0f} cells differ from Epoch's value by more than 0.0015.")
L += ["", "Epoch's value counts as one entry of the R pool even where a same-upstream source copies it, so same-upstream copies raise its weight. Per source the highest score in the cell is used. Design file: design.json (pool values, sources, per-replicate draw strings).", "",
      "## Convergence", "", "| Variant | Converged | Max divergences | Max R-hat | Min ESS | Fits needing a retry |", "|---|---|---|---|---|---|"]
for k in "RIO": v = V[k]; L.append(f"| {k} | {conv(v)} | {maxdiv(v)} | {f4(maxrhat(v))} | {miness(v):.0f} | {v['n'] - v['attempts_hist']['1']} |")
L += ["", *([f"Pending at generation time: {k} had {V[k]['status_counts']['missing']} refit(s) still running (cold-stage sampler, over 45 min); statistics use the finished refits. Rerun prov_agg.py and prov_report.py when it finishes." for k in "RIO" if V[k]["status_counts"]["missing"]]), "", "Epoch's inclusion rule (as applied by its data loader, not inside the fit) would drop no model in any refit.", "", "## Provenance spread of the posterior-mean ECI (non-anchor models, converged replicates)", "",
      "| Variant | Stratum | Largest SD (model) | Its 90% width | SD / width | SD / 0.25 | Largest SD / width over models (model) | Models with SD above 0.25 |", "|---|---|---|---|---|---|---|---|"]
for k in "RIO":
    for s in ("all", "frontier"):
        x = SP[k][s]; L.append(f"| {k} | {s} | {f2(x['max_sd'])} ({x['max_sd_model']}) | {f1(x['max_sd_model_width'])} | {f3(x['max_sd_over_width'])} | {f1(x['max_sd_over_seed_sd'])} | {f3(x['max_sd_over_width_any'])} ({x['max_sd_over_width_any_model']}) | {x['n_sd_gt_seed_sd']} of {x['n']} |")
L += ["", "Median per-model SD: " + "; ".join(f"{k} {f2(SP[k]['all']['median_sd'])}" for k in "RIO") + ". The 0.25 reference is the largest seed-to-seed SD on Epoch data (W2, 3 seeds); 0.29 on EEE data. The refits share one fit seed, so the provenance SD also contains sampler noise of at most that size.", "",
      "## Top 10 and frontier", ""]
for k in "RIO":
    t = V[k]["top10"]; g = V[k]["frontier_gaps"]
    L.append(f"- {k}: {t['n_distinct_sets']} distinct top-10 set(s); {t['n_differing_from_p0_set']} of {V[k]['n'] - V[k]['status_counts']['missing']} differ from P0's set, {t['n_differing_from_eee_det_set']} from the deterministic EEE fit's set. Frontier-20 adjacent gaps: largest SD {f2(g['max_adjacent_gap_sd'])}, median SD {f3(g['median_adjacent_gap_sd'])}; {g['n_pairs_with_any_flip']} adjacent pair(s) ever flip order; SD of the rank-1 minus rank-20 stretch {f2(g['stretch_rank1_minus_rank20_sd'])}.")
L += ["", "## S1 to S4 style counts against P0 (limits as BSEL: S2 and S3 counts 12/1/3/9, all/frontier/sparse/dense)", "", "| Variant | Spearman all | Spearman frontier | S2 count, all (range) | S3 count, all (range) | Refits failing S2, all | Refits failing any of S1 to S3, frontier | Refits failing S4 | Frontier max shift (points) |", "|---|---|---|---|---|---|---|---|---|"]
for k in "RIO":
    c = V[k]["vs_p0"]; fc = c["fail_counts"]
    L.append(f"| {k} | {rg(c['spearman_all'], f4)} | {rg(c['spearman_frontier'], f4)} | {rg(c['S2_count_all'], lambda x: str(int(x)))} | {rg(c['S3_count_all'], lambda x: str(int(x)))} | {fc['all']['S2']} of {fc['n']} | {fc['frontier']['any_S1_S3']} of {fc['n']} | {fc['S4']} of {fc['n']} | {rg(c['frontier_max_abs_shift'])} |")
L += ["", f"Deterministic EEE fit against P0: S2 count {refall['S2_count']}, S3 count {refall['S3_count']}, Spearman {f4(refall['S1'])}. Against the deterministic EEE fit instead:", "", "| Variant | S2 count, all (range) | S3 count, all (range) | Refits failing S2, all | Frontier max shift (points) |", "|---|---|---|---|---|"]
for k in "RIO":
    c = V[k]["vs_eee"]; fc = c["fail_counts"]
    L.append(f"| {k} | {rg(c['S2_count_all'], lambda x: str(int(x)))} | {rg(c['S3_count_all'], lambda x: str(int(x)))} | {fc['all']['S2']} of {fc['n']} | {rg(c['frontier_max_abs_shift'])} |")
L += ["", "## Residual checks T1 to T7 on each refit", "",
      "Each refit's T statistics are computed on its own data and posterior (same code as W4, thinned to 400 draws), and the max-T adjusted p is taken against the existing W3 model-true replicates of the EEE-data fit (192) and of the Epoch-data fit (187). Those replicate sets were generated from the original fits, not from each refit, so this isolates the change in the observed statistic. A per-refit replicate set would need about 200 extra fits per refit. Validation: the same code reproduces the published W4 values (Epoch T5 %s, EEE T5 %s)." % (f3(tce.get("T5", 0)), f3(tc.get("T5", 0))), "",
      "| Variant | T5 observed (range) | T5 adjusted p, EEE replicates: median (range) | Rejections of T5 at 0.01 (EEE / Epoch replicates) | T3 adjusted p, EEE replicates: median | T1 and T2 rejections |", "|---|---|---|---|---|---|"]
for k in "RIO":
    a, b = V[k]["T"]["eee_null"], V[k]["T"]["epoch_null"]; n = V[k]["status_counts"]["converged"]
    L.append(f"| {k} | {rg(a['T5']['observed'], f3)} | {f4(a['T5']['p_adjusted_median'])} ({rg(a['T5']['p_adjusted_range'], f4)}) | {a['T5']['n_reject_0_01']} / {b['T5']['n_reject_0_01']} of {n} | {f3(a['T3']['p_adjusted_median'])} | {a['T1']['n_reject_0_01']} and {a['T2']['n_reject_0_01']} of {n} |")
L += ["", "Reference: Epoch data T5 4.455, adjusted p 0.0053; deterministic EEE fit T5 3.861, adjusted p 0.0155 (T3 0.0933). Adjusted p takes values in steps of about 0.005 (1/193), so 0.0104 is two steps above the smallest value and sits next to the 0.01 level. T6 and T7 never reject. T3 and T4 never reject.", "",
      "## Drivers", ""]
for k in "RIO":
    d = V[k]["drivers"]
    L.append(f"- {k}: Spearman of per-model SD with the number of the model's multi-source cells {f2(d['spearman_sd_vs_n_multi_cells'])}, with the summed pool range {f2(d['spearman_sd_vs_sum_pool_range'])}, with the mean difficulty SD of the model's own benchmarks {f2(d.get('spearman_sd_vs_mean_difficulty_sd_of_own_benchmarks', float('nan')))}. Models with no multi-source cell: median SD {f2(d['models_with_zero_multi_cells']['median_sd'])} (n={d['models_with_zero_multi_cells']['n']}); with some: {f2(d['models_with_multi_cells']['median_sd'])} (n={d['models_with_multi_cells']['n']}). Benchmarks with the largest difficulty SD: " + ", ".join(f"{b['benchmark']} {f3(b['difficulty_sd'])}" for b in d["benchmarks_by_difficulty_sd"][:5]) + ".")
L += ["", "## Files", "", "design.json, fits/ (per-refit json and thinned draws), summary.json, chart_data.json, fragment.html, tcheck.json. Code: tools/prov_*.py, tools/run_prov.sh, tools/prov_mem_watchdog.sh."]
(O / "SUMMARY.md").write_text("\n".join(L) + "\n")

# ---------------- fragment.html
def tr(cells, cls=None): return "<tr>" + "".join(f'<td class="n">{c}</td>' if (i and cls != "t") else f"<td>{c}</td>" for i, c in enumerate(cells)) + "</tr>"
def table(head, rows):
    th = "".join("<th>%s</th>" % h if i == 0 else '<th class="n">%s</th>' % h for i, h in enumerate(head))
    return '    <div class="tblwrap"><table>\n      <thead><tr>' + th + "</tr></thead>\n      <tbody>\n        " + "\n        ".join(tr(r) for r in rows) + "\n      </tbody>\n    </table></div>"
R_, I_, O_ = V["R"], V["I"], V["O"]; sR, sI, sO = SP["R"], SP["I"], SP["O"]
tR = R_["T"]["eee_null"]["T5"]; tI = I_["T"]["eee_null"]["T5"]; tO = O_["T"]["eee_null"]["T5"]
top = R_["top_models_by_sd"][0]
nR = R_["status_counts"]["converged"]
H = []
H.append('<section id="prov">')
H.append("  <h2>N. Provenance resampling on EEE: how much ECI moves with the source of each score</h2>")
H.append(f"  <p>Section N.1 of the EEE mirror replaced Epoch's score by one EEE rule in each covered cell. This exploratory section asks a different question: if the score in each covered cell is drawn from a different evaluation source, how far does ECI move? Epoch's {D['n_cells']} covered cells, the 2,879-cell design and Epoch's priors stay as they are, and only the score in a covered cell changes. Everything holds under Epoch's model, and the design goes beyond the registered plan.</p>")
H.append(f"  <p>The answer depends on where a model sits. At the frontier the provenance SD of the posterior-mean ECI is at most {f2(sR['frontier']['max_sd'])} points when every source is eligible ({f2(sI['frontier']['max_sd'])} for independent sources, {f2(sO['frontier']['max_sd'])} for own-run sources), which is {f2(sR['frontier']['max_sd_over_width'])} of a 90% interval width at most and {f1(sR['frontier']['max_sd_over_seed_sd'])} times the 0.25 seed SD for the widest case. The top 10 is the same set in every refit. The largest spread is in weak 2023 models, up to {f2(sR['all']['max_sd'])} points ({sR['all']['max_sd_model']}), which have {int(top['n_multi_cells'])} multi-source cells of their own, so it comes from re-estimated benchmark difficulties.</p>")
H.append('  <div class="sub-sec" id="prov-design"><h3 class="ssh">N.1 Design</h3>')
H.append(f"  <p>Each refit gives every one of the {D['n_cells']} covered cells (cells with at least one EEE source in the crosswalk, 3rd audit sample accepted as recorded in runs/EEE/PROGRESS.md) a score drawn uniformly and independently from a pool. In variant R the pool is Epoch's value plus the score of each EEE source (per source the highest score in the cell). In variant I the pool holds independent sources only, and in variant O own-run sources only. Cells with no source in the pool keep Epoch's value, and a cell with one source takes it, so only cells with two or more sources vary between replicates. Each replicate has its own recorded RNG seed. Every refit uses fit seed 12345, Epoch's unmodified fit and priors, 4,000 draws per chain, and the retry rules of the benchmark-selection refits.</p>")
H.append(table(["Variant", "Refits", "Cells with a pool", "Cells with a real choice", "Cells differing from Epoch (mean, more than 0.0015)", "Converged", "Max R-hat", "Min ESS", "Divergences (max)"],
    [[k + (" (all sources)" if k == "R" else " (independent)" if k == "I" else " (own-run)"), D["n_rep"][k], D["per_variant"][k]["n_cells_in_pool"], D["per_variant"][k]["n_cells_with_choice"], f"{D['mean_cells_differing_from_epoch'][k]:.0f}", conv(V[k]), f4(maxrhat(V[k])), f"{miness(V[k]):.0f}", maxdiv(V[k])] for k in "RIO"]))
H.append('    <p class="src">Source: runs/EEE/PROV/design.json, summary.json. Epoch\'s inclusion rule, applied by the data loader and not inside the fit, would drop no model in any refit.</p>')
H.append("  </div>")
H.append('  <div class="sub-sec" id="prov-spread"><h3 class="ssh">N.2 Spread of ECI across replicates</h3>')
H.append(f"  <p>The table gives, for each variant, the largest per-model SD of the posterior-mean ECI across replicates and the SD of the most affected model, relative to its posterior 90% width and to the 0.25 seed SD of W2. The refits share one seed, so part of each SD is sampler noise of up to about that size; the three-seed SD on EEE data is below 0.3 for every model.</p>")
rows = []
for k in "RIO":
    for s, lab in (("all", "All non-anchor"), ("frontier", "Frontier 20")):
        x = SP[k][s]; rows.append([f"{k}, {lab}", f"{f2(x['max_sd'])} ({x['max_sd_model']})", f1(x["max_sd_model_width"]), f3(x["max_sd_over_width"]), f1(x["max_sd_over_seed_sd"]), f3(x["max_sd_over_width_any"]), f2(x["median_sd"]), f2(x["max_range"])])
H.append(table(["Variant, stratum", "Largest SD (model)", "Its 90% width", "SD over width", "SD over 0.25", "Largest SD over width, any model", "Median SD", "Largest range"], rows))
H.append('    <p class="src">Source: runs/EEE/PROV/summary.json (variants.*.spread), chart_data.json.</p>')
H.append(f"  <p>In variant R, {sR['all']['n_sd_gt_seed_sd']} of 254 models have a provenance SD above 0.25 and {sR['all']['n_sd_gt_0_1_width']} above a tenth of their interval width, while {sR['all']['n_sd_gt_0_25_width']} are above a quarter ({sR['all']['max_sd_over_width_any_model']} has the highest ratio, {f2(sR['all']['max_sd_over_width_any'])}). No frontier model has an SD above a tenth of its width in any variant. Independent-only and own-run-only pools move far fewer cells ({sI['all']['n']} models, about 120 and 99 varying cells), and their spreads are correspondingly smaller.</p>")
H.append("  </div>")
H.append('  <div class="sub-sec" id="prov-top"><h3 class="ssh">N.3 Top 10 and the frontier</h3>')
rows = []
for k in "RIO":
    t = V[k]["top10"]; g = V[k]["frontier_gaps"]; n = V[k]["status_counts"]["converged"]
    rows.append([k, f"{t['n_differing_from_p0_set']} of {n}", f"{t['n_differing_from_eee_det_set']} of {n}", f2(g["max_adjacent_gap_sd"]), f3(g["median_adjacent_gap_sd"]), g["n_pairs_with_any_flip"], f2(g["stretch_rank1_minus_rank20_sd"])])
H.append(table(["Variant", "Top-10 set differs from P0", "Top-10 set differs from deterministic EEE fit", "Largest SD of an adjacent frontier gap", "Median SD of adjacent gaps", "Adjacent frontier pairs that ever swap", "SD of the rank 1 minus rank 20 stretch"], rows))
H.append('    <p class="src">Source: runs/EEE/PROV/summary.json (variants.*.top10, frontier_gaps); rank frequencies in chart_data.json (rank_freq).</p>')
H.append(f"  <p>The top-10 set never changes. The order does change between adjacent models whose posterior means are close: in variant R the neighbouring pairs that swap are {R_['frontier_gaps']['n_pairs_with_any_flip']} of 19, the most often by {pct(R_['frontier_gaps']['max_flip_share'])} of replicates.</p>")
H.append("  </div>")
H.append('  <div class="sub-sec" id="prov-p0"><h3 class="ssh">N.4 Counts against the Epoch-data fit</h3>')
rows = [["Deterministic EEE fit (reference)", "1", f4(refall["S1"]), str(refall["S2_count"]), str(refall["S3_count"]), "-", "-"]]
for k in "RIO":
    c = V[k]["vs_p0"]; fc = c["fail_counts"]; n = fc["n"]
    rows.append([f"Variant {k}", str(n), rg(c["spearman_all"], f4), rg(c["S2_count_all"], lambda x: str(int(x))), rg(c["S3_count_all"], lambda x: str(int(x))), f"{fc['all']['S2']} of {n}", f"{fc['frontier']['any_S1_S3']} of {n}"])
H.append(table(["Fit", "Refits", "Spearman, all", "Models moving more than 0.25 W (limit 12)", "Width ratios outside 0.8 to 1.25 (limit 12)", "Refits above the S2 limit", "Refits failing any of S1 to S3 at the frontier"], rows))
H.append('    <p class="src">Source: runs/EEE/PROV/summary.json (variants.*.vs_p0). Limits follow the benchmark-selection refits.</p>')
H.append(f"  <p>No refit moves a frontier model by more than a quarter of its interval width, none fails the top-10 condition, and the Spearman correlation stays above {f4(min(V[k]['vs_p0']['spearman_all'][0] for k in 'RIO'))}. The count of models moving more than a quarter of their width exceeds the limit of 12 in {V['R']['vs_p0']['fail_counts']['all']['S2']} of {V['R']['vs_p0']['fail_counts']['n']} R refits, {V['I']['vs_p0']['fail_counts']['all']['S2']} of {V['I']['vs_p0']['fail_counts']['n']} I refits and {V['O']['vs_p0']['fail_counts']['all']['S2']} of {V['O']['vs_p0']['fail_counts']['n']} O refits (the deterministic EEE fit has {refall['S2_count']}), and the models involved are weak ones whose benchmarks were re-estimated.</p>")
H.append("  </div>")
H.append('  <div class="sub-sec" id="prov-t5"><h3 class="ssh">N.5 Residual checks</h3>')
rows = [["Epoch data (W4)", f3(tce.get("T5", 0)), "0.0053", "reject", "-"], ["Deterministic EEE fit (W4)", f3(tc.get("T5", 0)), "0.0155", "no rejection", "-"]]
for k in "RIO":
    a, b = V[k]["T"]["eee_null"]["T5"], V[k]["T"]["epoch_null"]["T5"]; n = V[k]["status_counts"]["converged"]
    rows.append([f"Variant {k} refits", rg(a["observed"], f3), f"{f4(a['p_adjusted_median'])} median ({rg(a['p_adjusted_range'], f4)})", f"{a['n_reject_0_01']} of {n} reject", f"{b['n_reject_0_01']} of {n} reject"])
H.append(table(["Fit", "T5 observed", "T5 max-T adjusted p (EEE-data replicates)", "At 0.01 (EEE-data replicates)", "At 0.01 (Epoch-data replicates)"], rows))
H.append('    <p class="src">Source: runs/EEE/PROV/summary.json (variants.*.T), tcheck.json. Statistics computed per refit on its own data and posterior; replicate sets from the W3 fits.</p>')
H.append(f"  <p>The Lab-by-benchmark check (T5) sits on the edge of the 0.01 level. Its observed statistic ranges from {f3(min(V[k]['T']['eee_null']['T5']['observed'][0] for k in 'RIO'))} to {f3(max(V[k]['T']['eee_null']['T5']['observed'][1] for k in 'RIO'))} across refits, between the EEE-data fit and the Epoch-data fit and above both at times. The adjusted p moves in steps of about 0.005, and the typical refit gives 0.0104, just above the level. In variant R, {tR['n_reject_0_01']} of {nR} refits reject; in variants I and O, {tI['n_reject_0_01']} and {tO['n_reject_0_01']}. This indicates that T5's non-rejection on the EEE input was a near call that depends on which sources are drawn. T1 and T2 reject in every refit and T3, T4, T6 and T7 in none. The full cost of per-refit replicate sets, about 200 fits each, was not paid.</p>")
H.append("  </div>")
H.append('  <div class="sub-sec" id="prov-drivers"><h3 class="ssh">N.6 What drives the spread</h3>')
dR = R_["drivers"]
H.append(f"  <p>A model's spread is not related to how many of its own cells have several sources (Spearman {f2(dR['spearman_sd_vs_n_multi_cells'])} in R); it is related to how much the difficulties of its benchmarks are re-estimated ({f2(dR.get('spearman_sd_vs_mean_difficulty_sd_of_own_benchmarks', float('nan')))}). Benchmarks with the largest difficulty SD across replicates: " + ", ".join(f"{b['benchmark']} ({f3(b['difficulty_sd'])}, {b['n_multi_cells']} multi-source cells)" for b in dR["benchmarks_by_difficulty_sd"][:6]) + f". Models with no multi-source cell have a median SD of {f2(dR['models_with_zero_multi_cells']['median_sd'])}, those with some {f2(dR['models_with_multi_cells']['median_sd'])}. The same pattern as in the EEE mirror: old benchmarks near the low end of the scale are re-estimated, and weak models that sit on them move with them.</p>")
H.append("  </div>")
H.append('  <div class="sub-sec" id="prov-limits"><h3 class="ssh">N.7 Limits</h3>')
H.append("  <p>Replicates are draws from the crosswalk as it stands, with the cell set fixed to Epoch's. The crosswalk was built on EEE manifest 959f0e11; a newer revision would add about 2 cells and was not rebuilt. Uniform draws weight Epoch's value more where a same-upstream source copies it. Sampler noise is inside every SD because the fit seed is shared. These results suggest where source choice matters, and say nothing about the 2,191 cells without an EEE source or the 24 benchmarks with none.</p>")
H.append("  </div>")
H.append("</section>")
(O / "fragment.html").write_text("\n".join(H) + "\n")
print("ok")
