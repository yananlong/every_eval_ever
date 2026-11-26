"""Augmented ECI input: Epoch's 2,879 rows plus each distinct EEE observation of the same cell (exploratory, beyond plan).

Rules, fixed before any fit:
  - EEE rows come from runs/EEE/crosswalk/pairs.csv, value column `norm` (Epoch's normalised scale).
  - same-upstream rows are dropped: they relay the number Epoch already holds.
  - one value per (cell, source): the highest, as in runs/EEE/PROV.
  - a value within 0.0015 of a value already kept for the cell (Epoch's first, then independent, then
    upstream-unknown, sources alphabetical) is dropped as a relay of the same number.
Sets: "all" (independent and upstream-unknown) and "ind" (independent only).
Columns added: obs_class (0 Epoch row, 1 independent, 2 upstream-unknown), obs_src, cell (index of the Epoch row)."""
import sys, json
from pathlib import Path
sys.path[:0] = ["runs/vendor/eci-public/src", "runs"]
import numpy as np, pandas as pd
from lib import data

TOL = 0.0015
OUT = Path("runs/AUG"); OUT.mkdir(parents=True, exist_ok=True)
df = data.fit_input().reset_index(drop=True)
df["obs_class"] = 0; df["obs_src"] = "Epoch"; df["cell"] = np.arange(len(df))
key = {(m, b): i for i, (m, b) in enumerate(zip(df.Model, df.benchmark))}
p = pd.read_csv("runs/EEE/crosswalk/pairs.csv")
p = p[p.source_class != "same-upstream"].copy()
p["cell"] = [key[(m, b)] for m, b in zip(p.model_group, p.eci_benchmark)]
p = p.sort_values("norm", ascending=False).drop_duplicates(["cell", "src"])
p["cls"] = p.source_class.map({"independent": 1, "upstream-unknown": 2})
assert np.allclose(p.epoch_norm, df.performance.to_numpy()[p.cell], atol=1e-6)
rep = {}
for name, classes in (("all", (1, 2)), ("ind", (1,))):
    q = p[p.cls.isin(classes)].sort_values(["cell", "cls", "src"])
    rows, dropped = [], 0
    for c, g in q.groupby("cell", sort=True):
        kept = [df.performance.iat[c]]
        for r in g.itertuples():
            if min(abs(r.norm - v) for v in kept) <= TOL: dropped += 1; continue
            kept.append(r.norm)
            row = df.iloc[c].copy(); row["performance"] = float(r.norm); row["obs_class"] = int(r.cls)
            row["obs_src"] = r.src; row["source"] = f"EEE:{r.src}"; rows.append(row)
    aug = pd.concat([df, pd.DataFrame(rows)], ignore_index=True)
    aug.to_csv(OUT / f"input_{name}.csv", index=False)
    n_obs = aug.groupby("cell").size()
    rep[name] = dict(rows=len(aug), extra_rows=len(rows), dropped_as_relay=dropped,
                     cells_with_extra=int((n_obs > 1).sum()), obs_per_cell=n_obs.value_counts().sort_index().to_dict(),
                     extra_by_class={int(k): int(v) for k, v in pd.Series([r["obs_class"] for r in rows]).value_counts().items()})
json.dump(rep, open(OUT / "input_report.json", "w"), indent=1, default=int)
print(json.dumps(rep, indent=1, default=int))
