"""W5 per-entry runner (tools copy; runs/ untouched). Runs one prior-arm fit as a child process with a 2 h wall-clock cap per attempt.
Fit logic is w5_sensitivity.entry_fit's (same seeds, draws, kwargs, retry with doubled draws, third attempt), but each attempt is a separate
child so a timeout can be killed (process group) and recorded as unresolved.  Usage (from v11 root):
  w5_run_entry.py NAME --draws 4000      NAME in P0 P0b P1..P10 X1 X2 S5F_<h>_<a> S5T_<h>_<a>   (PR and J2 also accepted)
Writes runs/W/W5/<NAME>.json (+ .npz .nc), status in runs/W/W5/_status/<NAME>.json."""
import sys, os, json, time, signal, subprocess, argparse
from pathlib import Path
RUNS = Path("runs").resolve()
sys.path.insert(0, str(RUNS))
CAP = int(os.environ.get("W5_CAP_S", 7200))
ap = argparse.ArgumentParser(); ap.add_argument("name"); ap.add_argument("--draws", type=int, default=4000)
ap.add_argument("--worker", type=int, default=-1); ap.add_argument("--kw", default="")
A = ap.parse_args()
OUT = Path("runs/W/W5"); ST = OUT / "_status"; ST.mkdir(parents=True, exist_ok=True)
log = lambda *a: print(time.strftime("%H:%M:%S"), A.name, *a, flush=True)


def kw_for(name, s0, third=False):
    import w5_sensitivity as W
    from lib import models
    base = name[:-len("_retry3")] if name.endswith("_retry3") else name
    seed = 12345 if base != "P0b" else 22345
    if base in ("P0", "P0b"): kw = dict(epoch_priors=None)
    elif base.startswith(("S5F_", "S5T_")):
        h, a = base.split("_", 1)[1].rsplit("_", 1)
        kw = dict(epoch_priors={h: W.powered(models.DEFAULT_PRIORS[h], float(a))})
    else: kw = W.build_entries(s0)[base]
    if third:
        if base == "P9": kw = dict(kw, noncentred=True)
        else: kw = dict(kw, target_accept=0.99)
    return seed, kw


def worker():
    import warnings; warnings.filterwarnings("ignore")
    import numpy as np
    import w5_sensitivity as W
    from lib import data, fit as fitmod, fit_any
    df = data.fit_input(); s0 = json.loads((OUT / "s5_screen.json").read_text())["s0_raw_capability_sd"]
    third = A.name.endswith("_retry3"); seed, kw = kw_for(A.name, s0, third)
    if third and A.name.startswith("P9"):   # deviation: Epoch's _chain_starts indexes draws["capability"], which is not a free variable in the non-centred P9
        import eci.bayesian as eb
        def _cs(draws, chains, rng):
            picks = rng.choice(len(draws["cap_z"]), chains, replace=False)
            return [{v: draws[v][i] for v in eb._FREE_VARS} for i in picks]
        eb._chain_starts = _cs
    d, warns, wall = fit_any.run(df, seed, draws=A.draws, **kw)
    ok, last = fitmod.verdict(d["attempts"])
    npz = OUT / f"{A.name}.npz"; (OUT / f"{A.name}.nc").unlink(missing_ok=True)
    np.savez_compressed(npz, eci=d["eci"].astype("float32")); W.save_nc(A.name, df, d, kw)
    r = dict(draws=A.draws, converged=bool(ok), last_attempt=last, started_from=d["started_from"], wall=round(wall, 1), warnings=warns[:3], ladder=d["attempts"], seed=seed,
             kw=json.dumps(kw, sort_keys=True, default=str), n_draws_total=int(d["eci"].shape[0]))
    (ST / f"{A.name}.att{A.worker}.json").write_text(json.dumps(r, indent=1, default=str))


def run_child(cmd, tag):
    t0 = time.time(); p = subprocess.Popen(cmd, start_new_session=True)
    try:
        rc = p.wait(timeout=CAP); return rc, time.time() - t0, False
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL); p.wait(); return -9, time.time() - t0, True


def attempt(name, k, draws):
    cmd = [sys.executable, __file__, name, "--draws", str(draws), "--worker", str(k)]
    rc, wall, to = run_child(cmd, name)
    f = ST / f"{name}.att{k}.json"
    if to: return dict(draws=draws, timeout=True, wall=round(wall, 1), converged=False)
    if rc != 0 or not f.exists(): return dict(draws=draws, crashed=True, rc=rc, wall=round(wall, 1), converged=False)
    return json.loads(f.read_text())


def orchestrate():
    final = dict(name=A.name, cap_s=CAP, started=time.strftime("%FT%TZ", time.gmtime()))
    if A.name in ("PR", "J2"):
        if A.name == "PR":
            code = ("import sys,json,warnings;sys.path.insert(0,'runs');warnings.filterwarnings('ignore');from lib import data,fit,models;"
                    f"df=data.fit_input();s,_=fit.fit('PR','runs/W/W5',df,spec=models.Spec(prior='reference'),seed=12345,draws={A.draws},loglik=True);print('PR converged',s['converged'],s['last_attempt'])")
            cmd = [sys.executable, "-c", code]
        else:
            cmd = [sys.executable, "runs/w5j_fit.py", "--variant", "J2", "--draws", str(A.draws)]
        rc, wall, to = run_child(cmd, A.name)
        final.update(timeout=to, rc=rc, wall=round(wall, 1), resolved=False)
        p = (OUT / "PR.json") if A.name == "PR" else Path("runs/W/W5J/J2/J2.json")
        if not to and rc == 0 and p.exists():
            s = json.loads(p.read_text()); final.update(converged=s["converged"], resolved=s["converged"], last_attempt=s["last_attempt"])
        (ST / f"{A.name}.json").write_text(json.dumps(final, indent=1, default=str)); log("done", final); return
    attempts = []; resolved = False; timed_out = False
    for k, dr in enumerate((A.draws, 2 * A.draws)):
        log("attempt", k, "draws", dr); a = attempt(A.name, k, dr); attempts.append(a)
        if a.get("timeout"): timed_out = True; break
        if a.get("converged"): resolved = True; break
    final.update(attempts=attempts, resolved=resolved, converged=resolved, timeout=timed_out, n_draws_total=attempts[-1].get("n_draws_total"))
    if not resolved and not timed_out and not A.name.endswith("_retry3"):   # G2 add_evidence: third attempt (non-centred P9, else target_accept 0.99)
        n3 = A.name + "_retry3"; log("third attempt", n3); a3 = attempt(n3, 0, A.draws)
        final["third_attempt"] = dict(a3, name=n3)
        if a3.get("converged"): final.update(resolved=True, converged=True, resolved_by="third_attempt")
        if a3.get("timeout"): final["timeout"] = True
    (OUT / f"{A.name}.json").write_text(json.dumps(final, indent=1, default=str))
    (ST / f"{A.name}.json").write_text(json.dumps(final, indent=1, default=str)); log("done resolved", final["resolved"], "timeout", final["timeout"])


if __name__ == "__main__":
    worker() if A.worker >= 0 else orchestrate()
