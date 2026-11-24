"""PROV design: provenance resampling on the EEE crosswalk.  Writes runs/EEE/PROV/design.json (covered cells only).
Variants: R (50): pool = {Epoch's value} + each EEE source's score (per source: highest score in the cell), uniform draw per cell;
I (20): pool = independent sources only; O (20): pool = src_kind own-run only.  Cells with an empty pool keep Epoch's value; a one-element pool takes it.
Replicate k of variant V uses numpy default_rng(BASE[V] + k); cells are visited in the fixed order of the cell list; draw = rng.integers(len(pool))."""
import json, hashlib, sys, os
import numpy as np, pandas as pd
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from eee_xwalk_lib import XW
from lib import data
OUT = Path("runs/EEE/PROV"); OUT.mkdir(parents=True, exist_ok=True)
# freeze check, as eee_build_input.py
fr = json.load(open(XW + "/crosswalk_freeze.json"))
for f, h in fr["maps_sha256"].items():
    assert hashlib.sha256(open(XW + "/" + f, "rb").read()).hexdigest() == h, f"{f} changed after the audit"
aud = json.load(open(XW + "/audit_result.json")); assert aud["final_passed"]
BASE = dict(R=2026112100, I=2026112200, O=2026112300); NREP = dict(R=50, I=20, O=20)
fi = data.fit_input()
epoch = {(m, b): float(v) for m, b, v in zip(fi.Model, fi.benchmark, fi.performance)}
p = pd.read_csv(XW + "/pairs.csv")
assert all((m, b) in epoch for m, b in zip(p.model_group, p.eci_benchmark))
cells = sorted(set(zip(p.model_group, p.eci_benchmark)))
def pools(sel):
    q = p[sel].sort_values(["model_group", "eci_benchmark", "src", "norm"], ascending=[True, True, True, False])
    q = q.groupby(["model_group", "eci_benchmark", "src"], as_index=False).head(1)      # per source: highest score
    out = {}
    for (m, b), g in q.groupby(["model_group", "eci_benchmark"]):
        out[(m, b)] = [(r.src, r.src_kind, r.source_class, float(r.norm)) for r in g.itertuples()]
    return out
P = dict(R=pools(p.index == p.index), I=pools(p.source_class == "independent"), O=pools(p.src_kind == "own-run"))
design = dict(note="Provenance resampling on EEE (exploratory). Cells: 688 covered cells; all other cells keep Epoch's value. pool[i] = values in draw order "
              "(R: Epoch's value first, then sources sorted by name; I and O: sources only); choices[k][i] = index drawn.",
              fit_seed=12345, draws=4000, rng_base=BASE, n_rep=NREP, cells=[list(c) for c in cells], epoch_value=[epoch[c] for c in cells], variants={})
for V in "RIO":
    pool_vals, pool_src, nv = [], [], 0
    for c in cells:
        s = P[V].get(c, [])
        if V == "R": vals, names = [epoch[c]] + [x[3] for x in s], ["EPOCH"] + [x[0] for x in s]
        else: vals, names = [x[3] for x in s], [x[0] for x in s]
        if not vals: vals, names = [epoch[c]], ["EPOCH"]               # empty pool: keep Epoch's value
        pool_vals.append([round(v, 6) for v in vals]); pool_src.append(names); nv += len(vals) > 1 and len(set(vals)) > 1
    ch, summ = [], []
    for k in range(NREP[V]):
        rng = np.random.default_rng(BASE[V] + k + 1)
        idx = [int(rng.integers(len(v))) for v in pool_vals]
        ch.append("".join(map(lambda i: str(i), idx)))                   # pool sizes are at most 7, one digit each
        val = np.array([pool_vals[i][j] for i, j in enumerate(idx)]); ep = np.array([epoch[c] for c in cells])
        summ.append(dict(n_cells_differing_from_epoch_gt_0015=int((np.abs(val - ep) > 0.0015).sum()), mean_signed_diff=float((val - ep).mean())))
    assert max(len(v) for v in pool_vals) <= 9
    design["variants"][V] = dict(n_cells_in_pool=int(sum(len(s) > 0 for s in P[V].values())), n_cells_with_choice=int(sum(len(v) > 1 for v in pool_vals)),
                                  n_cells_with_distinct_values=int(nv), pool_values=pool_vals, pool_sources=pool_src, choices=ch, rep_summary=summ)
    print(V, "cells with pool", design["variants"][V]["n_cells_in_pool"], "choice cells", design["variants"][V]["n_cells_with_choice"], "distinct-valued", nv)
(OUT / "design.json").write_text(json.dumps(design, separators=(",", ":")))
print("bytes", os.path.getsize(OUT / "design.json"), "cells", len(cells))
