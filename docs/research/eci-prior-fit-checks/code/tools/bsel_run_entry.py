"""BSEL per-refit runner, modelled on tools/w5_run_entry.py: one child process per fit attempt with a 2 h wall-clock cap (process-group kill),
attempts at 4,000 then 8,000 draws per chain, then a third attempt at target_accept 0.99 (4,000 draws), as W5 did for its arms.
Fit call is the one W5 used for P0: fit_any.run(df_sub, 12345, draws=..., epoch_priors=None) -> Epoch's unmodified fit_bayesian_eci.
df_sub = fit input minus the refit's benchmarks, Epoch's inclusion rule re-applied (bsel_common.subset).
Usage (from v11 root): bsel_run_entry.py ID      Writes runs/W/BSEL/fits/ID.json (+ ID.npz thinned draws), status in runs/W/BSEL/_status/."""
import sys, os, json, time, signal, subprocess, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bsel_common as C
CAP = int(os.environ.get("BSEL_CAP_S", 7200))
ap = argparse.ArgumentParser(); ap.add_argument("id"); ap.add_argument("--draws", type=int, default=C.DRAWS)
ap.add_argument("--worker", type=int, default=-1); ap.add_argument("--ta", type=float, default=0.95)
ap.add_argument("--seed", type=int, default=C.FIT_SEED)   # non-default seed: labelled rerun, written as ID__s<seed>
A = ap.parse_args()
TAG = A.id if A.seed == C.FIT_SEED else f"{A.id}__s{A.seed}"
FITS = C.OUT / "fits"; ST = C.OUT / "_status"; FITS.mkdir(parents=True, exist_ok=True); ST.mkdir(parents=True, exist_ok=True)
log = lambda *a: print(time.strftime("%H:%M:%S"), A.id, *a, flush=True)


def spec():
    d = json.loads((C.OUT / "design.json").read_text())
    return next(f for f in d["fits"] if f["id"] == A.id)


def worker():
    import warnings; warnings.filterwarnings("ignore")
    import numpy as np
    from lib import data, fit as fitmod, fit_any
    f = spec(); df = data.fit_input(); sub, dropped = C.subset(df, f["drop"])
    assert sorted(dropped) == sorted(f["dropped_models"])
    d, warns, wall = fit_any.run(sub, A.seed, draws=A.draws, epoch_priors=None, target_accept=A.ta)
    ok, last = fitmod.verdict(d["attempts"])
    names = list(d["model_names"]); eci = np.asarray(d["eci"], dtype="float64")
    post = d["trace"].posterior
    cap = post["capability"].stack(s=("chain", "draw")).transpose("s", ...).to_numpy()
    lo, hi = names.index(C.ANCHORS[0]), names.index(C.ANCHORS[1])
    p0 = C.load_p0()
    rows_full = df.groupby("Model").size().to_dict(); rows_sub = sub.groupby("Model").size().to_dict()
    cmp = C.compare(eci, names, p0, rows_sub, rows_full)
    anc = dict(refit=C.anchor_block(cap[:, lo], cap[:, hi]), p0=C.anchor_block(p0["cap_low"], p0["cap_high"]))
    keep = np.linspace(0, eci.shape[0] - 1, 4000).astype(int)
    np.savez_compressed(ST / f"{TAG}.att{A.worker}.npz", eci=eci[keep].astype("float32"), names=np.array(names), cap_low=cap[:, lo].astype("float32"),
                        cap_high=cap[:, hi].astype("float32"), mean=eci.mean(0), q05=np.quantile(eci, 0.05, axis=0), q95=np.quantile(eci, 0.95, axis=0))
    r = dict(draws=A.draws, target_accept=A.ta, converged=bool(ok), last_attempt=last, started_from=d["started_from"], wall=round(wall, 1), warnings=warns[:3],
             ladder=d["attempts"], seed=A.seed, n_draws_total=int(eci.shape[0]), n_models=len(names), n_rows=int(len(sub)), anchors=anc, compare=cmp)
    (ST / f"{TAG}.att{A.worker}.json").write_text(json.dumps(r, indent=1, default=str))


def run_child(cmd):
    t0 = time.time(); p = subprocess.Popen(cmd, start_new_session=True)
    try:
        rc = p.wait(timeout=CAP); return rc, time.time() - t0, False
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL); p.wait(); return -9, time.time() - t0, True


def attempt(k, draws, ta=0.95):
    cmd = [sys.executable, "-W", "ignore", __file__, A.id, "--draws", str(draws), "--worker", str(k), "--ta", str(ta), "--seed", str(A.seed)]
    rc, wall, to = run_child(cmd)
    f = ST / f"{TAG}.att{k}.json"
    if to: return dict(k=k, draws=draws, target_accept=ta, timeout=True, wall=round(wall, 1), converged=False)
    if rc != 0 or not f.exists(): return dict(k=k, draws=draws, target_accept=ta, crashed=True, rc=rc, wall=round(wall, 1), converged=False)
    return dict(json.loads(f.read_text()), k=k, child_wall=round(wall, 1))


def orchestrate():
    f = spec(); out = FITS / f"{TAG}.json"
    if out.exists() and json.loads(out.read_text()).get("finished"): log("already done"); return
    final = dict(id=TAG, design_id=A.id, seed=A.seed, kind=f["kind"], drop=f["drop"], dropped_models=f["dropped_models"], cap_s=CAP, started=time.strftime("%FT%TZ", time.gmtime()))
    if f["unanchored"]:
        final.update(unanchored=True, anchors_present=f["anchors_present"], resolved=False, finished=True)
        out.write_text(json.dumps(final, indent=1)); log("unanchored; not fitted"); return
    attempts = []; resolved = False; timed_out = False
    plan = [(0, A.draws, 0.95), (1, 2 * A.draws, 0.95)]
    for k, dr, ta in plan:
        log("attempt", k, "draws", dr); a = attempt(k, dr, ta); attempts.append(a)
        if a.get("timeout"): timed_out = True; break
        if a.get("converged"): resolved = True; break
    if not resolved and not timed_out:
        log("third attempt target_accept 0.99"); a = attempt(2, A.draws, 0.99); attempts.append(a)
        resolved = bool(a.get("converged")); timed_out = bool(a.get("timeout"))
    used = next((a for a in reversed(attempts) if "compare" in a), None)   # last attempt that produced draws
    final.update(attempts=[{k: v for k, v in a.items() if k not in ("compare", "anchors")} for a in attempts], resolved=resolved, converged=resolved, timeout=timed_out,
                 used_attempt=None if used is None else used["k"], finished=True)
    if used is not None:
        final.update(compare=used["compare"], anchors=used["anchors"], n_models=used["n_models"], n_rows=used["n_rows"])
        os.replace(ST / f"{TAG}.att{used['k']}.npz", FITS / f"{TAG}.npz")
    for p in ST.glob(f"{TAG}.att*.npz"): p.unlink()
    tmp = FITS / f".{TAG}.json.tmp"; tmp.write_text(json.dumps(final, indent=1, default=str)); os.replace(tmp, out)
    log("done resolved", resolved, "timeout", timed_out)


if __name__ == "__main__":
    worker() if A.worker >= 0 else orchestrate()
