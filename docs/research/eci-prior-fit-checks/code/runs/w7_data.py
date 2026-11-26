"""Inputs and extras for W7 fits. data: orig | mean_all | mean_ind (augmented, one row per cell, the mean of its
distinct values) | stack_all | stack_ind (augmented, every distinct value; use with feature "cell")."""
import numpy as np, pandas as pd
from lib import data, expand


def load(kind, fam_variant="lin"):
    df0 = data.fit_input().reset_index(drop=True); ex0 = expand.extras_info(df0); ex0["fam_variant"] = fam_variant
    if kind == "orig":
        return df0, ex0
    s = kind.split("_")[1]; a = pd.read_csv(f"runs/AUG/input_{s}.csv")
    if kind.startswith("mean"):
        m = a.groupby("cell")["performance"].mean()
        df = df0.copy(); df["performance"] = m.loc[np.arange(len(df0))].to_numpy()
        return df, ex0
    a = a.drop(columns=["obs_class", "obs_src", "cell"]).assign(cell=a["cell"])
    n = a.groupby("cell").size(); pos = {c: i for i, c in enumerate(n[n > 1].index)}
    ex = expand.extras_for(a.drop(columns=["cell"]), ex0)
    ex.update(fam_variant=fam_variant, multi_idx=np.array([pos.get(c, -1) for c in a["cell"]]), n_multi=len(pos))
    return a.drop(columns=["cell"]), ex
