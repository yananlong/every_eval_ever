"""Build runs/EEE/SUMMARY.md, runs/EEE/side_by_side.json and runs/EEE/chart_data.json from headline.json (eee_summary.py),
eci_compare.json, input/coverage.json and crosswalk/audit_result.json. Run from eci_work/v11 with plain python3.
The HTML fragment is written by eee_fragment.py from side_by_side.json."""
import json, os, csv
E = "runs/EEE"
H = json.load(open(f"{E}/headline.json")); ep, ex = H["epoch"], H["eee"]
cov = json.load(open(f"{E}/input/coverage.json")); aud = json.load(open(f"{E}/crosswalk/audit_result.json"))
cmp_ = json.load(open(f"{E}/eci_compare.json")) if os.path.exists(f"{E}/eci_compare.json") else {}


def g(d, *ks, default=None):
    for k in ks:
        if d is None: return default
        try: d = d[k]
        except (KeyError, IndexError, TypeError): return default
    return d


def f(x, nd=3):
    if x is None: return "n/a"
    if isinstance(x, bool): return "yes" if x else "no"
    if isinstance(x, int): return f"{x:,}"
    try: return f"{float(x):.{nd}f}"
    except Exception: return str(x)


def frac(a, b): return "n/a" if a is None or b is None else f"{a} of {b}"


rows = []   # (section, label, epoch, eee)
def add(sec, label, fn):
    def val(d):
        try: return fn(d)
        except Exception: return "n/a"
    rows.append((sec, label, val(ep), val(ex)))


# W2
add("W2 reproduction fit", "Seeds converged (of 3)", lambda d: f(g(d, "W2", "seeds_converged")))
add("W2 reproduction fit", "Divergences, seed 12345", lambda d: f(g(d, "W2", "divergences")))
add("W2 reproduction fit", "Max R-hat, seed 12345", lambda d: f(g(d, "W2", "max_rhat"), 4))
add("W2 reproduction fit", "Min bulk ESS / min tail ESS", lambda d: f"{g(d, 'W2', 'min_ess'):,.0f} / {float(g(d, 'W2', 'min_tail_ess')):,.0f}")
add("W2 reproduction fit", "elpd LOO (SE); p_loo", lambda d: f"{g(d, 'W2', 'elpd_loo'):,.0f} ({g(d, 'W2', 'elpd_se'):.0f}); {g(d, 'W2', 'p_loo'):.0f}")
add("W2 reproduction fit", "Largest seed-to-seed SD of a posterior-mean ECI", lambda d: f(g(d, "W2", "seed_to_seed_sd_max"), 2))
# W3
add("W3 simulation study", "G-null replicates converged", lambda d: frac(g(d, "W3", "counts", "null")[0], g(d, "W3", "counts", "null")[2]))
add("W3 simulation study", "G-null timeouts at the 60-minute cap", lambda d: f(g(d, "W3", "timeouts_null")))
add("W3 simulation study", "90% interval coverage of ECI, all models (90% CI)", lambda d: f"{g(d, 'W3', 'coverage90_all'):.3f} ({g(d, 'W3', 'coverage90_all_ci')[0]:.3f} to {g(d, 'W3', 'coverage90_all_ci')[1]:.3f})")
add("W3 simulation study", "90% interval coverage of ECI, frontier", lambda d: f(g(d, "W3", "coverage90_frontier")))
add("W3 simulation study", "90% coverage, sparse / dense models", lambda d: f"{g(d, 'W3', 'coverage90_sparse'):.3f} / {g(d, 'W3', 'coverage90_dense'):.3f}")
add("W3 simulation study", "50% interval coverage of ECI, all models", lambda d: f(g(d, "W3", "coverage50_all")))
for gen, lab in (("disp", "Noise-level check (T3) on G-disp"), ("2d", "Residual-correlation check (T2) on G-2D"), ("offset", "Lab-by-benchmark check (T5) on G-offset"), ("drift", "Time-drift check (T4) on G-drift"), ("shape", "Curve-shape check (T1) on G-shape")):
    add("W3 power", lab + ": rejections of converged fits", lambda d, gen=gen: frac(g(d, "W3", "power", gen, "n_reject"), g(d, "W3", "power", gen, "n_converged")))
add("W3 convergence", "G-2D replicates with a usable fit (of 20)", lambda d: f(g(d, "W3", "counts", "2d")[0]))
add("W3 convergence", "G-2D replicates that crashed in anchoring", lambda d: f(sum(1 for x in g(d, "W3", "crashed_2d") if x["anchor_error"])))
add("W3 convergence", "Converged of 20: G-offset / G-shape / G-disp / G-drift", lambda d: " / ".join(str(g(d, "W3", "counts", k)[0]) for k in ("offset", "shape", "disp", "drift")))
add("W3 positive control", "Seeds on which the control fails S1 to S4 in the all-models or frontier stratum (of 3)", lambda d: f(sum(1 for v in g(d, "W3", "positive_control").values() if v["fails_all"] or v["fails_frontier"])))
add("W3 positive control", "Seed 12345: S2 count / S3 count in all models (limit 12); frontier fails", lambda d: f"{g(d, 'W3', 'positive_control', '12345', 'all_S2')[0]} / {g(d, 'W3', 'positive_control', '12345', 'all_S3')[0]}; {'yes' if g(d, 'W3', 'positive_control', '12345', 'fails_frontier') else 'no'}")
add("W3 SBC (M13)", "Parameters flagged at the Bonferroni level (of 311)", lambda d: f(g(d, "W3", "sbc", "n_flagged")))
add("W3 gate G1", "Interpretation unqualified (all G1 conditions met)", lambda d: f(bool(g(d, "W3", "G1", "proceed"))))
# W3M
for k, lab in (("eci", "ECI (254 models)"), ("edi", "EDI (57 benchmarks)"), ("slope", "Slope (57)"), ("sigma", "Sigma (57)")):
    add("W3M rank tests (Modrak-style)", lab + ": gamma-flagged; central 90% share", lambda d, k=k: f"{g(d, 'W3M', 'rows', k, 'gamma_flagged')}; {g(d, 'W3M', 'rows', k, 'central90'):.2f}")
add("W3M rank tests (Modrak-style)", "Replicates used", lambda d: f(g(d, "W3M", "n")))
add("W3M rank tests (Modrak-style)", "Joint log-likelihood: gamma p; mean rank", lambda d: f"{g(d, 'W3M', 'rows', 'loglik_joint', 'gamma_p'):.4f}; {g(d, 'W3M', 'rows', 'loglik_joint', 'mean_u'):.2f}")
add("W3M rank tests (Modrak-style)", "Pearson dispersion: gamma p; mean rank", lambda d: f"{g(d, 'W3M', 'rows', 'pearson_overall', 'gamma_p'):.5f}; {g(d, 'W3M', 'rows', 'pearson_overall', 'mean_u'):.2f}")
# W4
add("W4 residual checks", "Converged model-true replicates in the reference", lambda d: f(g(d, "W4", "n_null")))
for t, lab in (("T1", "Curve-shape (T1)"), ("T2", "Residual-correlation (T2)"), ("T3", "Noise-level (T3)"), ("T4", "Time-drift (T4)"), ("T5", "Lab-by-benchmark (T5)"), ("T6", "Floor-and-ceiling (T6)"), ("T7", "Per-model fit (T7)")):
    add("W4 residual checks", lab + ": observed; max-T adjusted p", lambda d, t=t: f"{g(d, 'W4', 'T', t, 'obs'):.3f}; {g(d, 'W4', 'T', t, 'p_adj'):.4f}")
add("W4 residual checks", "Checks rejected at 0.01 family-wise", lambda d: ", ".join(g(d, "W4", "rejected")) or "none")
add("W4 residual checks", "T2: SDs above the mean of the model-true replicates", lambda d: f(g(d, "W4", "T2_sd_above_null_mean"), 1))
add("W4 marginal fit", "Held-out 90% coverage (rows)", lambda d: f"{g(d, 'W4', 'heldout_coverage'):.3f} ({g(d, 'W4', 'n_heldout'):,})")
add("W4 marginal fit", "LOO 90% coverage", lambda d: f(g(d, "W4", "loo_coverage90")))
add("W4 marginal fit", "Benchmarks flagged (of tested)", lambda d: frac(len(g(d, "W4", "flagged")), g(d, "W4", "n_benchmarks_tested")))
add("W4 localisation", "Benchmark pairs with q > 3.84 (share); median q", lambda d: f"{g(d, 'W4_loc', 'T2_share_q_gt_3.84'):.2f}; {g(d, 'W4_loc', 'T2_median_q'):.2f}")
add("W4 localisation", "Developer-by-benchmark cells with |t| > 2 (share)", lambda d: f(g(d, "W4_loc", "T5_share_abs_t_gt_2"), 2))
add("W4 localisation", "Benchmarks in the localisation set F (limit 10)", lambda d: f(g(d, "W4d", "n_F")))
add("W4 localisation", "Rows deleted with F (of 2,879)", lambda d: f(g(d, "W4d", "rows_deleted")))
for t in ("T1", "T2", "T5"):
    add("W4 localisation", f"{t} after deleting F: unadjusted p", lambda d, t=t: f(g(d, "W4d", "after", t, "p_unadjusted_deleted"), 4))
add("W4 verdict", "Model-adequacy claim (C2)", lambda d: g(d, "C2", "verdict") or "n/a")
# anchors
add("Anchors", "Largest change in a posterior-mean gap over the alternative anchor pairs (points)", lambda d: f(g(d, "WA_ext", "max_abs_gap_change"), 2))
add("Anchors", "Median per-model interval-width ratio, range over pairs", lambda d: f"{g(d, 'WA_ext', 'width_ratio_median_range')[0]:.2f} to {g(d, 'WA_ext', 'width_ratio_median_range')[1]:.2f}")
add("Anchors", "Uncertainty of gaps between frontier models, median ratio, range over pairs", lambda d: f"{g(d, 'WA_ext', 'gap_width_ratio_frontier_median_range')[0]:.2f} to {g(d, 'WA_ext', 'gap_width_ratio_frontier_median_range')[1]:.2f}")
add("Anchors", "Common change of unit, range over pairs", lambda d: f"{g(d, 'WA_ext', 'lambda_range')[0]:.3f} to {g(d, 'WA_ext', 'lambda_range')[1]:.3f}")
add("Anchors", "Per-model interval-width ratio, min to max over the pre-declared pairs", lambda d: f"{g(d, 'WA_a1', 'width_min'):.2f} to {g(d, 'WA_a1', 'width_max'):.2f}")
add("Anchors", "Largest shift of a posterior-mean ECI over the pre-declared pairs (points); models moved by more than 0.25 W", lambda d: f"{g(d, 'WA_a1', 'max_shift_points'):.2f}; {g(d, 'WA_a1', 'S2_max')}")
add("Anchors", "Within-draw rankings and P(i>j) changed by re-anchoring (largest change)", lambda d: f(g(d, "WA_a1", "max_pair_change"), 3))
# W5
add("W5 prior sensitivity", "Verdict label; unresolved priors", lambda d: f"{g(d, 'W5', 'verdict', 'verdict')}; {', '.join(g(d, 'W5', 'verdict', 'unresolved')) or 'none'}")
add("W5 prior sensitivity", "Priors failing S1 to S4 (strata)", lambda d: "; ".join(f"{k} ({', '.join(v)})" for k, v in g(d, "W5", "verdict", "failures_by_prior").items()) or "none")
for k in ("P8", "P9"):
    add("W5 prior sensitivity", f"{k}: models moved by more than 0.25 W, all models (limit 12); frontier (limit 1)", lambda d, k=k: f"{g(d, 'W5', 'entries', k, 'all_S2')}; {g(d, 'W5', 'entries', k, 'frontier_S2')}")
    add("W5 prior sensitivity", f"{k}: interval-width ratio outside 0.8 to 1.25, all models (limit 12)", lambda d, k=k: f(g(d, "W5", "entries", k, "all_S3")))
    add("W5 prior sensitivity", f"{k}: mean shift of models below ECI 100 (count); largest shift; largest frontier shift (points)", lambda d, k=k: f"{g(d, 'W5', 'points', k, 'mean_shift_below_100'):+.1f} ({g(d, 'W5', 'points', k, 'n_below_100')}); {g(d, 'W5', 'points', k, 'max_abs_shift'):.1f}; {g(d, 'W5', 'points', k, 'frontier_max_abs_shift'):.1f}")
add("W5 prior sensitivity", "Smallest rank correlation with the baseline over P1 to P10", lambda d: f(g(d, "W5", "rank_corr_min_scored"), 4))
add("W5 prior sensitivity", "Top 10 unchanged under every resolved prior P1 to P10", lambda d: f(all(v.get("S4_top10_same") for k, v in g(d, "W5", "entries").items() if k.startswith("P") and v.get("S4_top10_same") is not None)))
add("W5 prior sensitivity", "Hyperprior and noise priors (P1, P2, P4 to P7, P10) with any S2 or S3 count above 0", lambda d: f(sum(1 for k in ("P1", "P2", "P4", "P5", "P6", "P7", "P10") if (g(d, "W5", "entries", k, "all_S2") or 0) + (g(d, "W5", "entries", k, "all_S3") or 0) > 0)))
add("W5 prior sensitivity", "S5 power-scaling screen flags", lambda d: f(len(g(d, "W5", "S5_joint_flagged") or []) + len(g(d, "W5", "flagged_hyperpriors") or [])))
add("W5 prior sensitivity", "Reference prior PR: S2 / S3 counts, all models", lambda d: f"{g(d, 'W5', 'PR', 'all_S2')} / {g(d, 'W5', 'PR', 'all_S3')}")
add("W5 prior sensitivity", "Jeffreys prior J2: S2 / S3 counts, all models", lambda d: f"{g(d, 'W5', 'J2', 'all_S2')} / {g(d, 'W5', 'J2', 'all_S3')}" if g(d, 'W5', 'J2') else "unresolved (2 h cap)")
add("W5 prior sensitivity", "Prior arms on which T1, T2 and T5 all reject (of arms checked)", lambda d: frac(sum(1 for v in g(d, "W5_ppc").values() if all(t in v["rejected"] for t in ("T1", "T2", "T5"))), len(g(d, "W5_ppc"))))

add("W5 prior sensitivity", "Prior arms on which T1 and T2 both reject (of arms checked)", lambda d: frac(sum(1 for v in g(d, "W5_ppc").values() if all(t in v["rejected"] for t in ("T1", "T2"))), len(g(d, "W5_ppc"))))
add("W5 prior sensitivity", "T5 max-T adjusted p across the prior arms, range", lambda d: f"{min(v['p_adj']['T5'] for v in g(d, 'W5_ppc').values()):.4f} to {max(v['p_adj']['T5'] for v in g(d, 'W5_ppc').values()):.4f}")
json.dump(dict(rows=rows, coverage=cov, audit=aud, eci=cmp_), open(f"{E}/side_by_side.json", "w"), indent=1, default=str)
if __name__ == "__main__":
    sec = None
    for s, l, a, b in rows:
        if s != sec: print("##", s); sec = s
        print(f"  {l[:95]:95} | {a[:42]:42} | {b}")
