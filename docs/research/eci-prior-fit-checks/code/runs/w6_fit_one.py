"""One W6 fit in its own process (so the plan's 60-minute cap can be enforced): a candidate on the real data, a K-fold training fold,
or one reduced-SBC replicate."""
import sys, json, argparse, time, warnings, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, xarray as xr, pymc as pm
from scipy.special import logsumexp
import eci.bayesian as eb
from lib import data, models, fit as fitmod, fit_any, expand, sbc, generators as G

ap = argparse.ArgumentParser()
ap.add_argument("--name", required=True); ap.add_argument("--features", default=""); ap.add_argument("--prior", default="epoch")
ap.add_argument("--seed", type=int, default=12345); ap.add_argument("--target-accept", type=float, default=0.95)
ap.add_argument("--cap4000", action="store_true"); ap.add_argument("--fold", type=int, default=None)
ap.add_argument("--sbc", type=int, default=None); ap.add_argument("--n-reps", type=int, default=30); ap.add_argument("--src", default=None)
ap.add_argument("--outdir", default="runs/W/W6")
a = ap.parse_args()
spec = models.Spec(tuple(f for f in a.features.split(",") if f), a.prior)
df = data.fit_input(); ex_full = expand.extras_info(df)
out = Path(a.outdir); out.mkdir(parents=True, exist_ok=True)
if a.cap4000:   # F1: the plan's ladder stops at 4,000 draws per chain; the cold stage is not part of it
    eb._DENSE_DRAWS = (1000, 4000); eb._COLD_DRAWS = (1000, 1000)


def run_fit(name, d, ex, seed, loglik):
    import types
    t0 = time.time()
    # fit.fit uses the default target_accept; pass ours through the module's fit_bayesian_eci wrapper
    orig = eb.fit_bayesian_eci
    eb.fit_bayesian_eci = lambda *x, **k: orig(*x, **{**k, "target_accept": a.target_accept})
    try:
        return fitmod.fit(name, out, d, spec=spec, seed=seed, ex=ex, loglik=loglik, extra_code=[Path(__file__).parent / "lib/expand.py"])
    finally:
        eb.fit_bayesian_eci = orig


if a.fold is None and a.sbc is None:
    side, _ = run_fit(a.name, df, ex_full, a.seed, True)
    print("DONE", a.name, side["converged"], side["started_from"], side["last_attempt"], side["wall_seconds"], flush=True)
elif a.fold is not None:
    fold = pd.read_csv("runs/W/W4/folds.csv")["fold"].to_numpy()
    train = df[fold != a.fold].reset_index(drop=True); held = df[fold == a.fold]; held_rows = np.where(fold == a.fold)[0]
    ev = pd.concat([train, held]).reset_index(drop=True)
    side, _ = run_fit(f"{a.name}_fold{a.fold}", train, expand.extras_for(train, ex_full), a.seed, False)
    t = xr.open_datatree(out / f"{a.name}_fold{a.fold}.nc")
    post = t["posterior"].to_dataset(); post = post.isel(draw=np.linspace(0, post.sizes["draw"] - 1, 500).astype(int))
    m = models.build_model(ev, spec, ex=expand.extras_for(ev, ex_full))
    thin = xr.DataTree.from_dict({"posterior": post})
    with m:
        pm.compute_log_likelihood(thin, extend_inferencedata=True, progressbar=False)
    ll = thin["log_likelihood"].to_dataset()["obs"].stack(s=("chain", "draw")).transpose("s", "obs_dim_0").to_numpy()[:, len(train):]
    logd = logsumexp(ll, axis=0) - np.log(ll.shape[0])
    d = out / "kfold"; d.mkdir(exist_ok=True)
    np.savez(d / f"{a.name}_fold{a.fold}.npz", rows=held_rows, logd=logd, converged=side["converged"])
    print("DONE", a.name, "fold", a.fold, side["converged"], side["started_from"], len(logd), flush=True)
else:   # reduced SBC replicate
    src = xr.open_datatree(a.src); post = src["posterior"].to_dataset()
    names = [str(x) for x in post["model"].values]
    P = {v: post[v].stack(s=("chain", "draw")).transpose("s", ...).to_numpy() for v in post.data_vars if v not in ("eci", "kappa", "loading") and "chain" in post[v].dims}
    S = P["capability"].shape[0]; pos = int(np.floor(a.sbc * S / a.n_reps))
    seed = G.seed_of(f"sbc_{a.name}", a.sbc); rng = np.random.default_rng(seed)
    src_spec = spec
    y = expand.simulate(src_spec, P, pos, df, ex_full, rng)
    dfr = df.copy(); dfr["performance"] = y
    d, warns, wall = fit_any.run(dfr, seed, spec=spec, ex=ex_full, target_accept=a.target_accept)
    ok, last = fitmod.verdict(d["attempts"])
    th = fit_any.thin_post(d["trace"], 400, names=("capability",))
    low, high = names.index("Claude 3.5 Sonnet"), names.index("GPT-5")
    te, _ = sbc.truth_anchored(P["capability"][pos], P["difficulty"][pos], low, high)
    de, _d = sbc.anchored(th["capability"], P["difficulty"][pos][None, :].repeat(400, 0), low, high)
    u = sbc.u_value(de, te)
    sd = out / "sbc"; sd.mkdir(exist_ok=True)
    fit_any.atomic_json(sd / f"{a.name}_{a.sbc}.json", dict(name=a.name, r=a.sbc, seed=seed, position=pos, converged=ok, last_attempt=last, started_from=d["started_from"], wall=round(wall, 1), u_eci=u.tolist()))
    print("DONE sbc", a.name, a.sbc, ok, flush=True)
