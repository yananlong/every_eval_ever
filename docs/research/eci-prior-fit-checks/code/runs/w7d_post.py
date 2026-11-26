"""Figure and table for the W7 follow-up candidates from their pointwise tables (runs/W/W7/diag/<name>_pointwise.csv)
and sidecars: T1-T7 beside G3_ta99 (the grey band is the 90% range over G3_ta99's own 88 model-true replicates, shown
only for scale: no candidate has replicates of its own), scores at 0 per benchmark (observed, expected), and the
mean residual correlation inside each post hoc cluster. No fitting and no compilation. Usage: w7d_post.py NAME ..."""
import sys, json, warnings
sys.path[:0] = ["runs/vendor/eci-public/src", "runs"]; warnings.filterwarnings("ignore")
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np, pandas as pd
import w7d_common as c, w7_data
from lib import data, ppc_checks as ppc
CL = {"clu:oldLM": ["HellaSwag", "LAMBADA", "PIQA", "Winogrande", "TriviaQA"],
      "clu:knowQA": ["DTBench", "LMCA", "Balrog", "SimpleQA Verified", "SimpleBench", "Mystery Game Puzzles", "DeepResearch Bench"],
      "clu:math": ["MATH level 5", "OTIS Mock AIME 2024-2025", "FrontierMath-Tiers-1-3-v2-Private"]}
D = c.DIAG; names = [n for n in sys.argv[1:] if (D / f"{n}_pointwise.csv").exists()]
df, ex = w7_data.load("orig"); el = ppc.Elig(df, data.read_member(data.SCORES)); bn = el.bench_names
cal = json.loads(Path("runs/W/W7/G3_ta99_calib.json").read_text())
g3 = pd.read_csv(D / "loo_pointwise.csv"); bz = pd.read_csv(D / "bounds_by_benchmark.csv").set_index("benchmark")
fits = {"G3_ta99": dict(T=json.loads(Path("runs/W/W7/G3_ta99_ppc.json").read_text())["T"], z=g3["z"].to_numpy(), p0=None)}
for n in names:
    pw = pd.read_csv(D / f"{n}_pointwise.csv"); fits[n] = dict(T=json.loads((D / f"{n}.json").read_text())["T"], z=pw["z"].to_numpy(), p0=pw["p0"].to_numpy())
def clus(z):
    r = c.pair_r(z, el); R = c.r_matrix(r, el); out = {}
    for g, mem in CL.items():
        ix = [bn.index(m) for m in mem]; v = [R[a, b] for i, a in enumerate(ix) for b in ix[i + 1:] if not np.isnan(R[a, b])]; out[g] = float(np.mean(v))
    out["all_pairs_share_abs_r_gt_0_3"] = float((np.abs(r) > .3).mean()); out["arc_pair_r"] = float(R[bn.index("ARC-AGI"), bn.index("ARC-AGI-2")])
    out["fm_v2_pair_r"] = float(R[bn.index("FrontierMath-Tiers-1-3-v2-Private"), bn.index("FrontierMath-Tier-4-v2-Private")]); return out
tab = {n: dict(T=f["T"], clusters=clus(f["z"])) for n, f in fits.items()}
y = np.clip(df["performance"].to_numpy(float), 1e-3, 1 - 1e-3); zb = ["Mystery Game Puzzles", "FrontierMath-Tier-4-2025-07-01-Private", "Furniture Assembly", "ARC-AGI-2", "Chess Puzzles", "FrontierMath-Tier-4-v2-Private", "OTIS Mock AIME 2024-2025"]
for n, f in fits.items():
    tab[n]["zeros_expected"] = {b: (float(bz.loc[b, "exp_zeros"]) if f["p0"] is None else float(f["p0"][df["benchmark"].to_numpy() == b].sum())) for b in zb}
tab["zeros_observed"] = {b: int((y[df["benchmark"].to_numpy() == b] <= 1e-3).sum()) for b in zb}
(D / "candidates_post.json").write_text(json.dumps(tab, indent=1)); print(json.dumps(tab, indent=1)[:3000])
fig, ax = plt.subplots(1, 3, figsize=(16, 4.6)); col = ["0.35", "#4477aa", "#cc6677", "#228833", "#aa3377"]
a = ax[0]; x = np.arange(7); w = .8 / len(fits)
for j, (n, f) in enumerate(fits.items()): a.bar(x + j * w, [f["T"][k] / cal["rep_eti90"][k][1] for k in ppc.TNAMES], w, label=n, color=col[j % 5])
a.axhline(1, color="k", lw=.6); a.set_yscale("log"); a.set_xticks(x + .4); a.set_xticklabels(ppc.TNAMES); a.legend(fontsize=7)
a.set_ylabel("T / upper end of the 90% range over G3_ta99's replicates"); a.set_title("T1-T7 by fit (scale reference only: G3_ta99's own replicates)", fontsize=9)
a = ax[1]; x = np.arange(len(zb)); a.bar(x - .3, [tab["zeros_observed"][b] for b in zb], .2, color="k", label="observed")
for j, n in enumerate(fits): a.bar(x - .1 + j * .2 * 3 / max(3, len(fits)), [tab[n]["zeros_expected"][b] for b in zb], .2 * 3 / max(3, len(fits)), color=col[j % 5], label=f"expected, {n}")
a.set_xticks(x); a.set_xticklabels([c.short(b, 16) for b in zb], rotation=40, ha="right", fontsize=7); a.legend(fontsize=7); a.set_title("scores at 0: observed and expected", fontsize=9)
a = ax[2]; ks = list(CL) + ["arc_pair_r", "fm_v2_pair_r"]; x = np.arange(len(ks))
for j, n in enumerate(fits): a.bar(x + j * w, [tab[n]["clusters"][k] for k in ks], w, color=col[j % 5], label=n)
a.axhline(0, color="k", lw=.6); a.set_xticks(x + .4); a.set_xticklabels(ks, rotation=30, ha="right", fontsize=7); a.set_ylabel("mean residual correlation"); a.set_title("residual correlation inside the post hoc clusters and two lineage pairs", fontsize=9)
fig.savefig(D / "candidates_summary.png", dpi=95, bbox_inches="tight"); print("wrote candidates_summary.png", (D / "candidates_summary.png").stat().st_size // 1024, "KB")
