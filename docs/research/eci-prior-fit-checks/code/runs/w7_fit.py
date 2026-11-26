"""One W7 fit (runs/w7_models.py) through Epoch's fit function. Usage:
  w7_fit.py --name G5 --features dev,fam,f1r,skew [--fam-variant lin] [--data orig] [--target-accept 0.95] [--fold k]
--fold k: the W4 K-fold training fit of fold k (runs/W/W4/folds.csv) on Epoch's data, held-out log density over 500
thinned draws written to <outdir>/kfold/<name>_fold<k>.npz, as runs/w6x_fit_family.py does (the fold trace stays in memory, runs/w7_memfit.py)."""
import sys, argparse, warnings
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); warnings.filterwarnings("ignore")
import w7_models as w7, w7_data
from lib import models, fit as fitmod
ap = argparse.ArgumentParser()
ap.add_argument("--name", required=True); ap.add_argument("--features", required=True); ap.add_argument("--fam-variant", default="lin")
ap.add_argument("--data", default="orig"); ap.add_argument("--target-accept", type=float, default=0.95); ap.add_argument("--seed", type=int, default=12345)
ap.add_argument("--outdir", default="runs/W/W7"); ap.add_argument("--fold", type=int, default=None)
a = ap.parse_args()
w7.install()
import eci.bayesian as eb
_orig = eb.fit_bayesian_eci
eb.fit_bayesian_eci = lambda *x, **k: _orig(*x, **{**k, "target_accept": a.target_accept})
df, ex = w7_data.load(a.data, a.fam_variant)
spec = models.Spec(tuple(f for f in a.features.split(",") if f))
code = [Path(__file__), Path(__file__).parent / "w7_models.py", Path(__file__).parent / "w7_data.py", Path(__file__).parent / "w6x_family.py"]
if a.fold is None:
    side, _ = fitmod.fit(a.name, Path(a.outdir), df, spec=spec, seed=a.seed, ex=ex, loglik=(a.data == "orig"), extra_code=code)
    print("DONE", a.name, side["converged"], side["started_from"], side["last_attempt"], side["wall_seconds"], flush=True)
else:
    import numpy as np, pandas as pd, xarray as xr, pymc as pm
    from scipy.special import logsumexp
    from lib import expand
    assert a.data == "orig"
    out = Path(a.outdir)
    def ex_of(sub):
        e = expand.extras_for(sub, ex); e["fam_variant"] = a.fam_variant; return e
    fold = pd.read_csv("runs/W/W4/folds.csv")["fold"].to_numpy()
    train = df[fold != a.fold].reset_index(drop=True); held = df[fold == a.fold]; held_rows = np.where(fold == a.fold)[0]
    ev = pd.concat([train, held]).reset_index(drop=True)
    import w7_memfit   # the fold trace stays in memory; only the npz is written
    side, t = w7_memfit.fit_mem(train, spec, a.seed, ex_of(train))
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
