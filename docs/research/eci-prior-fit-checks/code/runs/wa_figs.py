"""WA figures from a1.json (and the W2 draws for the scatter). Post-processing only."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from lib import anchors as A
OUT = Path("runs/W/WA")
a1 = json.loads((OUT / "a1.json").read_text()); pairs = [k for k in a1["pairs"] if k != "orig"]
INK, MUTED, BLUE, GRID = "#1f2933", "#6b7280", "#2a6fb0", "#e5e7eb"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK, "axes.spines.top": False, "axes.spines.right": False})

fig, ax = plt.subplots(figsize=(7.2, 3.8), dpi=130)
for y, k in enumerate(pairs[::-1]):
    w = a1["pairs"][k]["units"]["pooled"]["width_ratio"]
    ax.plot([w["min"], w["max"]], [y, y], color=BLUE, lw=1, alpha=.55)
    ax.plot([w["q05"], w["q95"]], [y, y], color=BLUE, lw=4, solid_capstyle="round")
    ax.plot(w["median"], y, "o", color="white", mec=INK, ms=6, zorder=3)
    for s in ("seed12345", "seed22345", "seed32345"):
        ax.plot(a1["pairs"][k]["units"][s]["width_ratio"]["median"], y - .22, "|", color=MUTED, ms=5)
ax.axvspan(.8, 1.25, color=GRID, zorder=0); ax.axvline(1, color=MUTED, lw=.8)
ax.set_yticks(range(len(pairs))); ax.set_yticklabels([f"{k}: {a1['pairs'][k]['low']} / {a1['pairs'][k]['high']}" for k in pairs[::-1]], fontsize=7.5)
ax.set_xlabel("90% interval width, alternative anchors / original anchors (non-anchor models)")
ax.set_title("Width ratio across anchor pairs: thin line min to max, thick 5th to 95th percentile,\ncircle median (pooled seeds), ticks per-seed medians; grey band 0.8 to 1.25", fontsize=8.5, loc="left", color=INK)
fig.tight_layout(); fig.savefig(OUT / "fig_width_ratios.png"); plt.close(fig)

# invariance figure
E = np.vstack([A.load_seed(s)[0] for s in A.SEEDS]); names = A.load_seed(A.SEEDS[0])[2]
k = "L12-S10"; p = json.loads((OUT / "anchor_pairs.json").read_text())["pairs"]; p = [q for q in p if q["id"] == k][0]
Ek = A.reanchor(E, p["low_idx"], p["high_idx"], p["target_low"], p["target_high"])[0]
P0, P1 = A.p_matrix(E), A.p_matrix(Ek)
iu = np.triu_indices(len(names), 1); rng = np.random.default_rng(1); sel = rng.choice(len(iu[0]), 20000, replace=False)
fig, (a, b) = plt.subplots(1, 2, figsize=(7.4, 3.5), dpi=130)
a.scatter(P0[iu][sel], P1[iu][sel], s=2, color=BLUE, alpha=.4, rasterized=True); a.plot([0, 1], [0, 1], color=INK, lw=.6)
a.set_xlabel("P(i > j), original anchors"); a.set_ylabel(f"P(i > j), pair {k}")
a.set_title(f"All 32,640 pairs: max abs difference {np.abs(P0 - P1).max():.1e}\n(20,000 shown)", fontsize=8.5, loc="left")
gap = [a1["pairs"][q]["units"]["pooled"]["top10"]["max_abs_gap_change"] for q in pairs]
b.barh(range(len(pairs)), gap[::-1] if False else gap, color=BLUE, height=.55); b.set_yticks(range(len(pairs))); b.set_yticklabels(pairs, fontsize=8); b.invert_yaxis()
for i, v in enumerate(gap): b.text(v, i, f" {v:.3f}", va="center", fontsize=7.5, color=INK)
b.set_xlabel("largest change in a top-10 adjacent gap (ECI points)"); b.set_xlim(0, max(gap) * 1.3)
b.set_title("What can change: top-10 gaps\n(ranks, P(i>j), P(top 10): 0 for every pair)", fontsize=8.5, loc="left")
fig.tight_layout(); fig.savefig(OUT / "fig_invariance.png"); plt.close(fig)
print("max pij diff", np.abs(P0 - P1).max())
