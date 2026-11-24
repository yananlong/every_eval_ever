"""PROV (provenance resampling on EEE, exploratory): shared helpers.  Run from the v11 root."""
import json, sys
from pathlib import Path
import numpy as np
RUNS = Path("runs").resolve()
if str(RUNS) not in sys.path: sys.path.insert(0, str(RUNS))
import bsel_common as B
OUT = Path("runs/EEE/PROV")
EEE_REF_NPZ, EEE_REF_NC = Path("runs/EEE/W5/P0.npz"), Path("runs/EEE/W5/P0.nc")   # deterministic EEE fit: same call, seed 12345, 4,000 draws
FIT_SEED, DRAWS, ANCHORS = B.FIT_SEED, B.DRAWS, B.ANCHORS


def load_ref(nc, npz):
    import xarray as xr
    t = xr.open_datatree(nc); p = t["posterior"].to_dataset()
    names = [str(x) for x in p["model"].values]
    cap = p["capability"].stack(s=("chain", "draw")).transpose("s", "model").to_numpy()
    lo, hi = names.index(ANCHORS[0]), names.index(ANCHORS[1])
    return dict(names=names, eci=np.load(npz)["eci"].astype("float64"), cap_low=cap[:, lo], cap_high=cap[:, hi])


def design():
    return json.loads((OUT / "design.json").read_text())


def ids():
    d = design(); return [f"{V}{k + 1:02d}" for V in "RIO" for k in range(d["n_rep"][V])]


def build_df(rid, d=None, fi=None):
    """Epoch's fit input with performance replaced in the covered cells according to replicate rid (e.g. R07)."""
    from lib import data
    d = d or design(); fi = (fi if fi is not None else data.fit_input()).copy()
    V, k = rid[0], int(rid[1:]) - 1
    v = d["variants"][V]; ch = v["choices"][k]
    val = {tuple(c): v["pool_values"][i][int(ch[i])] for i, c in enumerate(d["cells"])}
    key = list(zip(fi.Model, fi.benchmark))
    fi["performance"] = [val.get(c, e) for c, e in zip(key, fi.performance)]
    return fi
