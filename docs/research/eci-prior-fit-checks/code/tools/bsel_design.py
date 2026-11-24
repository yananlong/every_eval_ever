"""BSEL design: every refit's id, kind and dropped benchmarks, with the inclusion-rule outcome, written to runs/W/BSEL/design.json.
Random subsets: numpy default_rng(20261121), 20 draws of round(0.2 * 57) = 11 benchmarks without replacement from the alphabetically
sorted benchmark list (one rng, drawn in order R01..R20)."""
import json, re
import numpy as np
import bsel_common as C
from lib import data

df = data.fit_input()
benches = sorted(df["benchmark"].unique())
assert len(benches) == 57 and df["Model"].nunique() == 256
full_sub, full_drop = C.subset(df, [])
assert len(full_sub) == len(df) and not full_drop, "inclusion rule does not reproduce the fit input"
slug = lambda b: re.sub(r"[^A-Za-z0-9]+", "_", b).strip("_")
fits = []
for b in C.A4: fits.append(dict(id=f"A4_{slug(b)}", kind="A4_lobo", drop=[b]))
for b in benches:
    if b not in C.A4: fits.append(dict(id=f"LOBO_{slug(b)}", kind="lobo", drop=[b]))
for k, v in C.CLUSTERS.items(): fits.append(dict(id=k, kind="cluster", drop=list(v)))
F = sorted(json.loads(open("runs/W/W4d/step1.json").read())["F"])
assert len(F) == 16
fits.append(dict(id="C_F16", kind="cluster", drop=F))
rng = np.random.default_rng(C.RNG_SEED); k = int(round(C.RANDOM_FRAC * len(benches)))
for r in range(C.N_RANDOM):
    pick = sorted(rng.choice(len(benches), size=k, replace=False).tolist())
    fits.append(dict(id=f"R{r + 1:02d}", kind="random", drop=[benches[i] for i in pick]))
assert len({f["id"] for f in fits}) == len(fits)
for f in fits:
    sub, dropped = C.subset(df, f["drop"])
    f.update(n_rows=int(len(sub)), n_models=int(sub["Model"].nunique()), n_benchmarks=int(sub["benchmark"].nunique()), dropped_models=dropped,
             anchors_present=[a for a in C.ANCHORS if a in set(sub["Model"])])
    f["unanchored"] = len(f["anchors_present"]) < 2
C.OUT.mkdir(parents=True, exist_ok=True)
(C.OUT / "design.json").write_text(json.dumps(dict(rng_seed=C.RNG_SEED, random_k=k, benchmarks=benches, F=F, clusters=C.CLUSTERS, fits=fits), indent=1))
print(len(fits), "fits;", sum(f["unanchored"] for f in fits), "unanchored")
for f in fits: print(f["id"], f["n_models"], f["n_benchmarks"], len(f["dropped_models"]), "UNANCHORED" if f["unanchored"] else "")
