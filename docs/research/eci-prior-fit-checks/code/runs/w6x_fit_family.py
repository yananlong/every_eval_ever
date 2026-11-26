"""One fit of the exploratory family candidate (runs/w6x_family.py) on the real data or a W4 K-fold training fold.
Same sampler path, sidecar and log-likelihood as runs/w6_fit_one.py. Usage:
  w6x_fit_family.py --name FX_both --variant both [--features dev] [--fold k]"""
import sys, argparse, warnings
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, xarray as xr, pymc as pm
from scipy.special import logsumexp
import w6x_family as fx
from lib import data, models, fit as fitmod, expand

ap = argparse.ArgumentParser()
ap.add_argument("--name", required=True); ap.add_argument("--variant", choices=("tag", "lin", "both"), required=True)
ap.add_argument("--features", default=""); ap.add_argument("--seed", type=int, default=12345)
ap.add_argument("--fold", type=int, default=None); ap.add_argument("--target-accept", type=float, default=0.95); ap.add_argument("--outdir", default="runs/W/W6X")
a = ap.parse_args()
fx.install()
import eci.bayesian as eb   # pass target acceptance through, as runs/w6_fit_one.py does (M14 fallback 1 uses 0.99)
_orig = eb.fit_bayesian_eci
eb.fit_bayesian_eci = lambda *x, **k: _orig(*x, **{**k, "target_accept": a.target_accept})
spec = models.Spec(("fam",) + tuple(f for f in a.features.split(",") if f), "epoch")
df = data.fit_input(); ex_full = expand.extras_info(df); ex_full["fam_variant"] = a.variant
out = Path(a.outdir); out.mkdir(parents=True, exist_ok=True)
code = [Path(__file__), Path(__file__).parent / "w6x_family.py", Path(__file__).parent / "lib/expand.py"]


def ex_of(sub):
    e = expand.extras_for(sub, ex_full); e["fam_variant"] = a.variant; return e


if a.fold is None:
    side, _ = fitmod.fit(a.name, out, df, spec=spec, seed=a.seed, ex=ex_full, loglik=True, extra_code=code)
    print("DONE", a.name, side["converged"], side["started_from"], side["last_attempt"], side["wall_seconds"], flush=True)
else:
    fold = pd.read_csv("runs/W/W4/folds.csv")["fold"].to_numpy()
    train = df[fold != a.fold].reset_index(drop=True); held = df[fold == a.fold]; held_rows = np.where(fold == a.fold)[0]
    ev = pd.concat([train, held]).reset_index(drop=True)
    side, _ = fitmod.fit(f"{a.name}_fold{a.fold}", out, train, spec=spec, seed=a.seed, ex=ex_of(train), loglik=False, extra_code=code)
    t = xr.open_datatree(out / f"{a.name}_fold{a.fold}.nc")
    post = t["posterior"].to_dataset(); post = post.isel(draw=np.linspace(0, post.sizes["draw"] - 1, 500).astype(int))
    m = models.build_model(ev, spec, ex=ex_of(ev))
    thin = xr.DataTree.from_dict({"posterior": post})
    with m:
        pm.compute_log_likelihood(thin, extend_inferencedata=True, progressbar=False)
    ll = thin["log_likelihood"].to_dataset()["obs"].stack(s=("chain", "draw")).transpose("s", "obs_dim_0").to_numpy()[:, len(train):]
    logd = logsumexp(ll, axis=0) - np.log(ll.shape[0])
    d = out / "kfold"; d.mkdir(exist_ok=True)
    np.savez(d / f"{a.name}_fold{a.fold}.npz", rows=held_rows, logd=logd, converged=side["converged"])
    print("DONE", a.name, "fold", a.fold, side["converged"], side["started_from"], len(logd), flush=True)
