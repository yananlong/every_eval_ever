"""Score the W5-J fits (J1, J2) with S1-S4 against P0 and compare them with P0 and PR: frontier and all-model shifts, interval widths,
top-10 rank changes. Reads runs/W/W5/P0.npz and runs/W/W5/PR.nc (from w5_sensitivity.py) and runs/W/W5J/<variant>/<variant>.nc.
Writes runs/W/W5J/w5j_scores.json and summary.md. Run from the v11 root after the fits exist."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
from lib import fit as fitmod, sens_metrics as sm

OUT = Path("runs/W/W5J"); W5 = Path("runs/W/W5")
VARIANTS = [v for v in ("J1", "J2") if (OUT / v / f"{v}.nc").exists()]


def short(sc):
    return {k: {a: b for a, b in v.items() if not a.startswith("p_top10")} for k, v in sc.items() if isinstance(v, dict)}


def main():
    d0 = np.load(W5 / "P0.npz")["eci"].astype("float64")
    fits = {v: fitmod.load_eci(OUT / v / f"{v}.nc") for v in VARIANTS}
    if (W5 / "PR.nc").exists(): fits["PR"] = fitmod.load_eci(W5 / "PR.nc")
    names = next(iter(fits.values()))[1]
    strata = json.loads(Path("runs/strata.json").read_text())
    masks = {k: np.array([n in set(strata[k]) for n in names]) for k in ("all", "frontier", "sparse", "dense")}
    anchor = np.array([n in sm.ANCHORS for n in names]); s0 = sm.summarise(d0); r0 = np.argsort(-s0["mean"])
    R = dict(scores={}, compare={}, side={})
    for k, (dk, _, _) in fits.items():
        assert dk.shape[1] == d0.shape[1]
        R["scores"][k] = short(sm.score(dk, d0, names, masks, 0.25)); sk = sm.summarise(dk); rk = np.argsort(-sk["mean"]); c = {}
        for sname, m in masks.items():
            na = m & ~anchor; diff = sk["mean"][na] - s0["mean"][na]
            c[sname] = dict(n=int(na.sum()), mean_abs_diff=float(np.abs(diff).mean()), max_abs_diff=float(np.abs(diff).max()), mean_diff=float(diff.mean()),
                            median_width_P0=float(np.median(s0["width"][na])), median_width=float(np.median(sk["width"][na])), median_width_ratio=float(np.median(sk["width"][na] / s0["width"][na])))
        c["top10"] = dict(same_set=bool(set(r0[:10]) == set(rk[:10])), same_order=bool((r0[:10] == rk[:10]).all()), entered=[names[i] for i in set(rk[:10]) - set(r0[:10])], left=[names[i] for i in set(r0[:10]) - set(rk[:10])],
                          order_k=[names[i] for i in rk[:10]], order_P0=[names[i] for i in r0[:10]],
                          rank_change_of_P0_top10=[int(np.where(rk == i)[0][0]) - j for j, i in enumerate(r0[:10])])
        R["compare"][k] = c
        p = OUT / k / f"{k}.json" if k != "PR" else W5 / "PR.json"
        if p.exists(): sd = json.loads(p.read_text()); R["side"][k] = {a: sd.get(a) for a in ("converged", "last_attempt", "wall_seconds", "min_bfmi", "min_tail_ess")}
    (OUT / "w5j_scores.json").write_text(json.dumps(R, indent=1, default=str))
    L = ["# W5-J summary: normalised Jeffreys priors J1 and J2 against P0, beside PR (exploratory, outside C1)", "",
         "Fits at the W5 settings of the PR entry (4 chains, 4,000 draws per chain, target acceptance 0.95, seed 12345). S1-S4 are scored against P0 as for a grid entry.", ""]
    L += ["## Fit status", "", "| Fit | Converged | Last attempt |", "| --- | --- | --- |"] + [f"| {k} | {v.get('converged')} | {v.get('last_attempt')} |" for k, v in R["side"].items()] + [""]
    L += ["## S1-S4 against P0", "", "| Fit | Stratum | S1 Spearman | S2 count (limit) | S3 count (limit) | S4 pass |", "| --- | --- | --- | --- | --- | --- |"]
    for k, sc in R["scores"].items():
        for s in ("all", "frontier", "sparse", "dense"):
            x = sc[s]; L.append(f"| {k} | {s} | {x['S1']:.4f} | {x['S2_count']} ({x['S2_limit']}) | {x['S3_count']} ({x['S3_limit']}) | {sc['S4']['pass_'] if s == 'all' else ''} |")
    L += ["", "## ECI shift and interval width against P0 (non-anchor models)", "", "| Fit | Stratum | Mean absolute shift | Largest absolute shift | Median 90% width, P0 | Median 90% width | Median width ratio |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for k, c in R["compare"].items():
        for s in ("all", "frontier"):
            x = c[s]; L.append(f"| {k} | {s} | {x['mean_abs_diff']:.3f} | {x['max_abs_diff']:.3f} | {x['median_width_P0']:.2f} | {x['median_width']:.2f} | {x['median_width_ratio']:.3f} |")
    L += ["", "## Top 10", ""]
    for k, c in R["compare"].items():
        t = c["top10"]; L.append(f"- {k}: same set as P0: {t['same_set']}; same order: {t['same_order']}; entered: {', '.join(t['entered']) or 'none'}; left: {', '.join(t['left']) or 'none'}; rank change of each P0 top-10 model (P0 order): {t['rank_change_of_P0_top10']}.")
    (OUT / "summary.md").write_text("\n".join(L) + "\n"); print("\n".join(L))


if __name__ == "__main__":
    main()
