"""Pre-fit one W4 held-out fold with exactly the call w4_ppc.py makes, so w4_ppc.py skips it via the sidecar match. Usage: w4_prefit_fold.py <f>"""
import sys, warnings
from pathlib import Path
sys.path.insert(0, "runs"); warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from lib import data, fit as fitmod
f = int(sys.argv[1]); OUT = Path("runs/W/W4")
df = data.fit_input(); fold = pd.read_csv(OUT / "folds.csv")["fold"].to_numpy()
train = df[fold != f].reset_index(drop=True)
side, _ = fitmod.fit(f"fold{f}", OUT, train, spec=None, seed=12345 + f, evaluate=False)
print("fold", f, "converged", side["converged"], "wall", side["wall_seconds"], flush=True)
