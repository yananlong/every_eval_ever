"""W3P (M13, optional): posterior SBC (Sailynoja, Schmitt, Burkner & Vehtari 2025, arXiv:2502.03279), run after W5.

For replicate r = 0..N-1: take one joint draw theta' from the W2 seed-12345 posterior (position floor(r S / N)), simulate y_sim from it on the real cell
list, refit Epoch's model on y_obs and y_sim together (every cell appears twice), and rank theta' among 400 draws of that refit. The refit's prior
is then the posterior given y_obs that theta' came from, so the ranks are uniform when sampler and model are right (the W3 refit on y_sim alone is not).
Test quantities, thinning and tests are those of lib/sbc_modrak.py; the log-likelihood is that of the augmented data. Resumable; run from the v11 directory.

  usage:  runs/.venv/bin/python runs/w5_posterior_sbc.py [--n 100]          fits (about 5 minutes each, 4 cores)
                  runs/.venv/bin/python runs/w5_posterior_sbc.py --summarise        ranks and figures from the finished replicates (no sampling)
Exploratory; gates nothing.
"""
import sys, json, time, argparse, warnings, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
warnings.filterwarnings("ignore")
import numpy as np, xarray as xr
from lib import data, generators as G, sbc_modrak as sm_

OUT = Path("runs/W/W3P"); W2 = Path("runs/W/W2")
EPS = 1e-3
GEN = "psbc"                                   # simulate() treats an unknown generator name as G-null; the name only seeds the noise
log = lambda *a: print(time.strftime("%H:%M:%S"), *a, flush=True)


def setup():
    df = data.fit_input(); scores = data.read_member(data.SCORES); pat = G.Pattern(df, scores)
    post = xr.open_datatree(W2 / "seed12345.nc")["posterior"].to_dataset()
    names = [str(x) for x in post["model"].values]
    keys = ["capability", "difficulty", "slope", "sigma", "tau_alpha", "sigma_median", "tau_sigma"]
    pooled = {v: post[v].stack(s=("chain", "draw")).transpose("s", ...).to_numpy() for v in keys}
    return df, pat, pooled, names


def run_rep(r, n, df, pat, pooled, low, high, force=False):
    from lib import fit as fitmod, fit_any                     # imported here: these load PyMC
    js = OUT / "rep" / f"{GEN}_{r}.json"; nc = OUT / "rep" / f"{GEN}_{r}.nc"
    S = pooled["capability"].shape[0]; pos = int(np.floor(r * S / n)); seed = G.seed_of(GEN, r)
    want = dict(r=r, n=n, seed=seed, position=pos, input_sha256=fitmod.input_digest(df))
    if js.exists() and nc.exists() and not force:
        old = json.loads(js.read_text())
        if all(old.get(k) == v for k, v in want.items()): return old
    theta = {k: pooled[k][pos] for k in ("capability", "difficulty", "slope", "sigma")}
    truth = dict(theta, **{h: pooled[h][pos] for h in ("tau_alpha", "sigma_median", "tau_sigma")})
    y, _ = G.simulate(GEN, r, theta, pat)
    df_aug = sm_.augment(df, y)
    d, warns, wall = fit_any.run(df_aug, seed)
    ok, last = fitmod.verdict(d["attempts"])
    th = fit_any.thin_post(d["trace"])
    assert th["capability"].shape[1] == len(pooled["capability"][0]), "augmented fit changed the model ordering"
    yc = np.clip(np.concatenate([df["performance"].to_numpy(float), y]), EPS, 1 - EPS)
    mi, bi = np.concatenate([pat.mi, pat.mi]), np.concatenate([pat.bi, pat.bi])
    rng = np.random.default_rng(G.seed_of("modrak:" + GEN, r))
    ranks = sm_.replicate_ranks(th, truth, yc, mi, bi, pat.K, low, high, rng)
    ds = xr.Dataset({k: (("draw",) + tuple(f"{k}_d{i}" for i in range(v.ndim - 1)), v) for k, v in th.items()})
    tmp = OUT / "rep" / f".{GEN}_{r}.nc.tmp"; ds.to_netcdf(tmp); os.replace(tmp, nc)
    side = dict(want, converged=ok, last_attempt=last, attempts=d["attempts"], started_from=d["started_from"], warnings=warns, wall_seconds=round(wall, 1),
                ranks={c: dict(names=v["names"], u=v["u"].tolist(), stride=v["stride"].tolist(), ess=v["ess"].tolist()) for c, v in ranks.items()})
    tmp = js.with_suffix(".json.tmp"); tmp.write_text(json.dumps(side, indent=1, default=str)); os.replace(tmp, js)
    return side


def summarise(n):
    reps = []
    for p in sorted((OUT / "rep").glob(f"{GEN}_*.json"), key=lambda p: int(p.stem.split("_")[1])):
        j = json.loads(p.read_text())
        if j["converged"]: reps.append(j)
    if not reps: log("no converged replicates"); return
    per = [{c: dict(names=v["names"], u=np.array(v["u"]), stride=np.array(v["stride"]), ess=np.array(v["ess"])) for c, v in j["ranks"].items()} for j in reps]
    res, figU = sm_.aggregate(per)
    import w3_modrak as w3m
    w3m._figure(OUT, GEN, figU, len(per))
    meta = dict(interim=len(reps) < n, n_converged=len(reps), n_planned=n, mean_wall_seconds=float(np.mean([j["wall_seconds"] for j in reps])),
                note="posterior SBC: truth from the W2 posterior, refit on y_obs and y_sim; uniform ranks expected; exploratory, gates nothing")
    (OUT / "posterior_sbc.json").write_text(json.dumps(dict(meta=meta, results={GEN: dict(n_replicates=len(reps), quantities=res)}), indent=1, default=float))
    w3m._summary(OUT, dict(meta, counts={GEN: dict(used=len(reps), planned=n)}, thinning=True, written=time.strftime("%Y-%m-%d %H:%M:%S"), caveat=meta["note"]), {GEN: dict(n_replicates=len(reps), quantities=res)})
    log("summarised", len(reps), "replicates")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=100); ap.add_argument("--summarise", action="store_true"); ap.add_argument("--force", action="store_true")
    a = ap.parse_args(); (OUT / "rep").mkdir(parents=True, exist_ok=True)
    if not a.summarise:
        df, pat, pooled, names = setup(); low, high = names.index("Claude 3.5 Sonnet"), names.index("GPT-5")
        for r in range(a.n):
            x = run_rep(r, a.n, df, pat, pooled, low, high, a.force)
            log("psbc", r, "converged", x["converged"], x["started_from"], f"{x['wall_seconds']}s")
    summarise(a.n)
