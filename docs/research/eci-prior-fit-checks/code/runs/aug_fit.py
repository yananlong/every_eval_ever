"""One fit on an augmented input (runs/AUG/input_{set}.csv). --model base: Epoch's unmodified builder and fit
(spec None, as P0). --model cell: runs/aug_model.py through Epoch's fit function. Usage: aug_fit.py --set all --model cell"""
import sys, argparse, warnings
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
warnings.filterwarnings("ignore")
import pandas as pd
import aug_model
from lib import models, fit as fitmod
ap = argparse.ArgumentParser(); ap.add_argument("--set", choices=("all", "ind"), required=True)
ap.add_argument("--model", choices=("base", "cell", "mean"), required=True); ap.add_argument("--seed", type=int, default=12345); ap.add_argument("--target-accept", type=float, default=0.95)
a = ap.parse_args()
if a.target_accept != 0.95:   # fallback 1 as in runs/w6x_fit_family.py: pass target acceptance through Epoch's fit
    import eci.bayesian as eb
    _orig = eb.fit_bayesian_eci
    eb.fit_bayesian_eci = lambda *x, **k: _orig(*x, **{**k, "target_accept": a.target_accept})
df = pd.read_csv(f"runs/AUG/input_{a.set}.csv")
name = f"AUG_{a.model}_{a.set}" + ("" if a.target_accept == 0.95 else "_ta99"); out = Path("runs/AUG")
if a.model == "mean":   # one row per cell: the mean of its distinct values, Epoch's row otherwise unchanged
    m = df.groupby("cell")["performance"].mean()
    df = df[df.obs_class == 0].sort_values("cell").reset_index(drop=True); df["performance"] = m.loc[df.cell].to_numpy()
    side, _ = fitmod.fit(name, out, df, spec=None, seed=a.seed)
elif a.model == "base":
    side, _ = fitmod.fit(name, out, df, spec=None, seed=a.seed)
else:
    aug_model.install()
    ex = dict(cell=df["cell"].to_numpy(), obs_class=df["obs_class"].to_numpy())
    side, _ = fitmod.fit(name, out, df, spec=models.Spec(("cell",)), seed=a.seed, ex=ex, loglik=False,
                         extra_code=[Path(__file__), Path(__file__).parent / "aug_model.py"])
print("DONE", name, side["converged"], side["started_from"], side["last_attempt"], side["wall_seconds"], flush=True)
