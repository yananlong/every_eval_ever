"""Pre-declared selection of alternative anchor pairs (plan M11a, R28). Reads W2 posterior means and counts only; computes no A1 result."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
from lib import anchors as A

OUT = Path("runs/W/WA"); OUT.mkdir(parents=True, exist_ok=True)
E, C, names = [], [], None
for s in A.SEEDS:
    e, c, n = A.load_seed(s); E.append(e); C.append(c); names = names or n
    assert n == names
E, C = np.vstack(E), np.vstack(C)
counts = A.obs_counts(names)
ok, sd, med = A.eligible(names, counts, C)
mean = E.mean(0)
pairs, drops, n_el = A.select_pairs(names, mean, ok)
for p in pairs:
    if True:
        for k in ("low", "high"):
            i = p[k + "_idx"]; p[k + "_obs"] = int(counts[i]); p[k + "_capability_sd"] = float(sd[i]); p[k + "_p0_mean_eci"] = float(mean[i])
            p[k + "_eligible"] = bool(ok[i])
        p["p0_gap"] = p["high_p0_mean_eci"] - p["low_p0_mean_eci"]
doc = dict(rule=dict(min_obs=A.MIN_OBS, sd_rule="pooled-seed posterior SD of raw capability <= median over all 256 models", median_sd=med, min_gap_eci=A.MIN_GAP,
                     n_eligible=n_el, low_positions=list(A.LOW_POS), min_spans=list(A.SPANS)), n_models=len(names), pairs=pairs, dropped=drops)
(OUT / "anchor_pairs.json").write_text(json.dumps(doc, indent=1) + "\n")
print("eligible", n_el, "median sd", med, "dropped", drops)
for p in pairs:
    print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in p.items() if k not in ("low_idx", "high_idx", "note")})
