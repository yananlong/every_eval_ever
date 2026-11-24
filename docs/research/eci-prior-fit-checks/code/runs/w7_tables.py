"""Markdown tables for runs/W/W7/SUMMARY.md from the W7 json outputs (fit sidecars, *_ppc.json, *_calib.json,
*_kfold.json, aug_compare.json). Usage: w7_tables.py FIT_NAME ... (fits scored on Epoch's data)"""
import sys, json
from pathlib import Path

W = Path("runs/W/W7"); T = ["T1", "T2", "T3", "T4", "T5", "T6", "T7"]
js = lambda p: json.loads(Path(p).read_text()) if Path(p).exists() else None
names = sys.argv[1:]
print("| Fit | Features | Converged | Stage | Wall (min) | Div. | max R-hat | min ESS bulk | LOO delta vs F0 (SE) | k_share | K-fold trigger |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
for n in names:
    s = js(W / f"{n}.json"); p = js(W / f"{n}_ppc.json")
    if s is None: print(f"| {n} | | no sidecar | | | | | | | | |"); continue
    la = s["last_attempt"]; row = f"| {n} | {','.join(s['args']['spec'][0])} | {s['converged']} | {la['stage']} | {s['wall_seconds'] / 60:.0f} | {la['divergences']} | {la['max_rhat']:.3f} | {la['min_ess']:.0f} |"
    if p and "loo" in p:
        l = p["loo"]; row += f" {l['delta_vs_F0']:+.1f} ({l['se']:.1f}) | {l['k_share']:.4f} | {l['kfold_trigger']} |"
    else: row += " | | |"
    print(row)
print()
print("| Fit | " + " | ".join(T) + " | T2 max abs r | share abs r > 0.3 | LOO-PIT KS |")
print("|---|" + "---|" * (len(T) + 3))
for n in ["validate/f0_seed12345"] + names:
    p = js(W / f"{n}_ppc.json")
    if not p: continue
    lab = "F0" if n.startswith("validate") else n
    pit = p.get("loo_pit", {}).get("ks_distance")
    print(f"| {lab} | " + " | ".join(f"{p['T'][k]:.3f}" for k in T) + f" | {p['T2_extras']['max_abs_r']:.2f} | {p['T2_extras']['share_abs_r_gt_0_3']:.2f} | {'' if pit is None else f'{pit:.3f}'} |")
print()
print("Approximate max-T adjusted p against F0's model-true replicates (not the calibrated p):")
print("| Fit | " + " | ".join(T) + " |"); print("|---|" + "---|" * len(T))
for n in ["validate/f0_seed12345"] + names:
    p = js(W / f"{n}_ppc.json")
    if not p: continue
    a = p["approx_vs_F0_replicates"]; lab = "F0" if n.startswith("validate") else n
    print(f"| {lab} | " + " | ".join(f"{a[k]['p_adjusted']:.4f}" for k in T) + " |")
print()
for n in names:
    c = js(W / f"{n}_calib.json")
    if not c: continue
    print(f"Calibration of {n}: {c['converged']} of {c['R_planned']} model-true replicates converged ({c['finished']} finished)")
    print("| T | observed | replicate 90% interval | p unadjusted | p max-T adjusted |"); print("|---|---|---|---|---|")
    for k in T:
        m = c["max_t"][k]; e = c["rep_eti90"][k]
        print(f"| {k} | {m['observed']:.3f} | {e[0]:.3f} to {e[1]:.3f} | {m['p_unadjusted']:.4f} | {m['p_adjusted']:.4f} |")
    print()
for n in names:
    k = js(W / f"{n}_kfold.json")
    if k: print(f"K-fold {n}: {k}")
for n in names:
    p = js(W / f"{n}_ppc.json")
    if not p: continue
    print(f"\nLocalisation, {n}:")
    for key in ("T1_top", "T2_top", "T2_top_r", "T5_top"):
        print(f"  {key}: " + "; ".join(f"{x['item']} {x['value']:.2f}" for x in p.get(key, [])[:5]))
