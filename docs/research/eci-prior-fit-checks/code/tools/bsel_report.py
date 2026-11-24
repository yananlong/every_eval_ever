"""BSEL tables for summary.md and fragment.html, generated from runs/W/BSEL/summary.json (prints markdown and writes the HTML table to
runs/W/BSEL/_table.html for pasting into the fragment)."""
import json
from pathlib import Path

S = json.loads(Path("runs/W/BSEL/summary.json").read_text())
STR = ("all", "frontier", "sparse", "dense")
rows = {r["id"]: r for r in S["clusters"] + S["random"]}
lobo = {x["id"]: x for x in S["lobo_ranked_by_frontier_max_shift"]}
full = {}
for r in json.loads(Path("runs/W/BSEL/chart_data.json").read_text())["refits"]: full[r["id"]] = r


SUB = {r["design_id"]: r["id"] for r in S["reruns_other_seed"] if r.get("status") == "converged"}
def best(k): return full[SUB[k]] if k in SUB and full[k].get("status") != "converged" else full[k]


def s13(r, s):
    m = r["S"][s]; return f"{m['S1']:.3f}/{m['S2']}/{m['S3']}" + ("" if m["pass_"] else "*")


def md_row(name, r):
    if "S" not in r: return f"| {name} | {r.get('status')} |" + " |" * 9
    return (f"| {name} | {r['n_dropped_models']} | " + " | ".join(s13(r, s) for s in STR) +
            f" | {'pass' if r['S4']['pass_'] else 'fail'} ({r['S4']['max_pair_change']:.2f}) | {r['frontier_max_abs_shift']:.2f} | {r['stretch_change']:+.2f} | "
            f"{r.get('affine_slope') or float('nan'):.3f} | {r.get('low_end_mean_shift') if r.get('low_end_mean_shift') is not None else float('nan'):+.1f} | {'same' if not r['top10_entered'] else ', '.join(r['top10_entered']) + ' in'} |")


hdr = ("| Refit | Models dropped | all S1/S2/S3 | frontier | sparse | dense | S4 (max pair change) | Frontier max abs shift | Stretch change (rank 1 - rank 20) | Scale slope | Low-end mean shift | Top-10 set |\n"
       "|---|---|---|---|---|---|---|---|---|---|---|---|")
print(hdr)
print(md_row("P0b (seed noise)", full["P0b"]))
for k, r in full.items():
    if k != "P0b" and (r["kind"] in ("A4_lobo", "cluster", "random") or r["kind"].startswith("rerun_")): print(md_row(k + (" (non-converged)" if r.get("status") not in ("converged", None) else ""), r))
print()
print("| LOBO benchmark | Models dropped | Frontier max abs shift | Frontier median abs gap change | Stretch change | Fails |\n|---|---|---|---|---|---|")
for x in S["lobo_ranked_by_frontier_max_shift"]:
    print(f"| {x['benchmark']}{' (A4)' if x['id'].startswith('A4_') else ''} | {x['n_dropped_models']} | {x['frontier_max_abs_shift']:.2f} | {x['frontier_median_abs_gap_change']:.2f} | {x['stretch_change']:+.2f} | {', '.join(x['S_fail']) or '-'} |")
print()
print("| A4 benchmark | Models dropped | Anchor spread ratio | Scale b ratio | b CV P0 / refit | Median abs shift | Max abs shift (model) | Spearman(shift, P0 ECI) |\n|---|---|---|---|---|---|---|---|")
for a in S["A4"]:
    print(f"| {a['benchmark']} | {len(a['dropped_models'])} | {a['spread_ratio']:.3f} | {a['b_ratio']:.3f} | {a['b_cv_p0']:.3f} / {a['b_cv_refit']:.3f} | {a['eci_shift_median_abs']:.2f} | {a['eci_shift_max_abs']:.2f} ({a['top_mover']['model']}) | {a['spearman_shift_vs_p0eci']:+.2f} |")

# ---- HTML table: grouped rows
def pill(ok, txt=None): return f'<span class="pill {"pass" if ok else "fail"}">{txt or ("pass" if ok else "fail")}</span>'
def grp(ids):
    rs = [full[i] for i in ids if "S" in full[i]]
    return rs
H = ['<div class="tblwrap"><table>', '<thead><tr><th>Refit</th><th>Fits</th><th>S1-S3 all</th><th>S1-S3 frontier</th><th>S1-S3 sparse</th><th>S4</th>'
     '<th>Top-10 set changed</th><th>Frontier max |&Delta;| (ECI)</th><th>Stretch change, rank 1 to 20</th><th>Low-end mean shift</th></tr></thead><tbody>']
def rng(v, f="{:.2f}"): return f.format(min(v)) if len(v) == 1 else (f.format(min(v)) + " to " + f.format(max(v)))
def line(name, rs):
    n = len(rs)
    def cnt(s): k = sum(r["S"][s]["pass_"] for r in rs); return pill(k == n, f"{k} of {n}") if n > 1 else pill(k == 1)
    k4 = sum(r["S4"]["pass_"] for r in rs); ch = sum(bool(r["top10_entered"]) for r in rs)
    sl = [r["low_end_mean_shift"] for r in rs if r.get("low_end_mean_shift") is not None]
    H.append(f"<tr><td>{name}</td><td class=\"n\">{n}</td><td>{cnt('all')}</td><td>{cnt('frontier')}</td><td>{cnt('sparse')}</td>"
             f"<td>{pill(k4 == n, f'{k4} of {n}') if n > 1 else pill(k4 == 1)}</td><td class=\"n\">{ch}</td>"
             f"<td class=\"n\">{rng([r['frontier_max_abs_shift'] for r in rs])}</td><td class=\"n\">{rng([r['stretch_change'] for r in rs], '{:+.2f}')}</td>"
             f"<td class=\"n\">{rng(sl, '{:+.1f}') if sl else '-'}</td></tr>")
line("P0b, second seed (noise)", [full["P0b"]])
a4 = [k for k in full if full[k]["kind"] == "A4_lobo"]
for k in a4:
    r = best(k); bn = next(f["drop"][0] for f in json.loads(Path("runs/W/BSEL/design.json").read_text())["fits"] if f["id"] == k)
    if "S" in r: line("A4: " + bn + ("" if r["id"] == k else " (seed 22345)") + ("" if r["status"] == "converged" else " (not converged)"), [r])
line("Other 49 LOBO (exploratory)", [r for r in [best(k) for k in full if full[k]["kind"] == "lobo"] if r.get("status") == "converged"])
names = dict(C_FM="FrontierMath, 4 tiers", C_ARC="ARC-AGI and ARC-AGI-2", C_OTIS_LMCA="OTIS Mock AIME and LMCA", C_OLD="HellaSwag, PIQA, Winogrande, TriviaQA, GSM8K", C_F16="All 16 of F")
for k, v in names.items():
    if "S" in full[k]: line(v, [full[k]])
line("Random 20% drops", grp([k for k in full if full[k]["kind"] == "random"]))
H.append("</tbody></table></div>")
Path("runs/W/BSEL/_table.html").write_text("\n".join(H))
