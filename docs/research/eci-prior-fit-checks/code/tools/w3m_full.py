"""W3M full rerun: Modrak/ECDF rank tests on the 180 converged null replicates (32 W3 originals + 148 W4d refits). CPU only; does not modify runs/lib or w3_modrak.py."""
import sys, json, time, argparse, warnings
from pathlib import Path
from multiprocessing import Pool
V11 = Path(__file__).resolve().parents[1] / "v11"; RUNS = V11 / "runs"
sys.path.insert(0, str(RUNS)); warnings.filterwarnings("ignore")
import numpy as np
import w3_modrak as wm
from lib import sbc_modrak as sm_

W3 = RUNS / "W/W3"; W4 = RUNS / "W/W4d/null_refit"; OUT = RUNS / "W/W3M_full"
G_ = {}

def reps():
    L = []
    for src, d in (("W3", W3 / "rep"), ("W4d_refit", W4 / "rep")):
        for p in d.glob("null_*.json"):
            r = int(p.stem.split("_")[1]); j = json.loads(p.read_text())
            if j.get("converged") and (d / f"null_{r}.nc").exists() and (W3 / "truth" / f"null_{r}.npz").exists(): L.append((r, src, str(d / f"null_{r}.nc")))
    return sorted(L)

def init():
    import xarray as xr
    from lib import data, generators as G
    df = data.fit_input(); scores = data.read_member(data.SCORES); G_["pat"] = G.Pattern(df, scores)
    names = [str(x) for x in xr.open_datatree(RUNS / "W/W2/seed12345.nc")["posterior"].to_dataset()["model"].values]
    G_["low"], G_["high"] = names.index("Claude 3.5 Sonnet"), names.index("GPT-5")

def one(a):
    import xarray as xr
    from lib import generators as G
    r, src, nc = a; pat = G_["pat"]
    ds = xr.open_dataset(nc).load(); draws = {k: ds[k].values for k in ds.data_vars if k != "log_slope"}
    z = np.load(W3 / "truth" / f"null_{r}.npz"); truth = {k: z[k] for k in z.files}
    y, _ = G.simulate("null", r, truth, pat); yc = np.clip(y, wm.EPS, 1 - wm.EPS)
    rng = np.random.default_rng(G.seed_of("modrak:null", r))
    return r, sm_.replicate_ranks(draws, truth, yc, pat.mi, pat.bi, pat.K, G_["low"], G_["high"], rng, thin=True)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=0); ap.add_argument("--procs", type=int, default=12); a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True); L = reps(); L = L[:a.n] if a.n else L
    print("replicates", len(L), flush=True); t = time.time()
    with Pool(a.procs, initializer=init) as P: res = P.map(one, L, chunksize=1)
    print("ranks done", time.time() - t, flush=True)
    per = [p for _, p in res]; agg, figU = sm_.aggregate(per)
    meta = dict(n=len(L), from_W3=sum(s == "W3" for _, s, _ in L), from_W4d_refit=sum(s != "W3" for _, s, _ in L), replicates=[r for r, _, _ in L],
                thinning=True, written=time.strftime("%Y-%m-%d %H:%M:%S"))
    (OUT / "modrak_full.json").write_text(json.dumps(dict(meta=meta, quantities=agg), indent=1, default=float))
    np.savez_compressed(OUT / "ranks_null.npz", **{c: figU[c][0] for c in figU}, replicates=np.array(meta["replicates"]))
    wm._figure(OUT, "null", figU, len(per)); wm._summary(OUT, dict(interim=False, counts={"null": dict(used=len(L), planned=len(L))}, thinning=True, written=meta["written"],
        caveat="truth drawn from the W2 posterior and the refit uses y_sim only; ranks are not exactly uniform even when everything is exact (selftest C). 32 W3 fits plus 148 W4d refits"), {"null": dict(n_replicates=len(per), quantities=agg)})
    print("done", time.time() - t, flush=True)
