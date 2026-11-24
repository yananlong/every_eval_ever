"""Parallel W3 driver (local, untracked). Runs pending replicates of null,2d,offset,shape,disp,drift concurrently, N at a time.
Usage (from work root): runs/w3_parallel.py [--workers 44] ; each task runs its own capped `w3_calibrate.py --one` subprocess."""
import sys, json, time, argparse, os, signal, subprocess, threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.path.insert(0, str(Path(__file__).resolve().parent))
import w3_resume  # patches W.run_rep_capped
import w3_calibrate as W
from lib import generators as G

def finished(gen, r):
    js = W.OUT / "rep" / f"{gen}_{r}.json"
    if not js.exists(): return False
    old = json.loads(js.read_text())
    return bool(old.get("timeout") or old.get("code_sha256") == W.code_dig())

def handle_external(gen, r, pid, pooled):
    """A replicate started by the old sequential driver (its parent is gone): wait for its JSON, enforce the 3600 s cap from the process's etimes, rerun via run_rep_capped if it overruns or dies without a JSON."""
    def alive():
        return subprocess.run(["ps", "-o", "etimes=", "-p", str(pid)], capture_output=True, text=True).stdout.strip()
    while True:
        if finished(gen, r): return json.loads((W.OUT / "rep" / f"{gen}_{r}.json").read_text())
        et = alive()
        if not et or not et.isdigit():
            time.sleep(20)
            if finished(gen, r): continue
            break
        if int(et) > W.CAP_SECONDS:
            try: os.killpg(pid, signal.SIGKILL)
            except ProcessLookupError: pass
            time.sleep(5); break
        time.sleep(15)
    W.log(gen, r, "external run died/overran without JSON; rerunning under cap")
    return W.run_rep_capped(gen, r, pooled)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--workers", type=int, default=44); ap.add_argument("--exclude", default=""); ap.add_argument("--external-pid", type=int, default=0); a = ap.parse_args()
    df, scores, el, pat, pooled, names = W.setup()
    excl = {(e.split(":")[0], int(e.split(":")[1])) for e in a.exclude.split(",") if e}
    pend = [(st, r) for st in ["null", "2d", "offset", "shape", "disp", "drift"] for r in range(G.REPS[st]) if not finished(st, r) and (st, r) not in excl]
    W.log("parallel driver: workers", a.workers, "pending", len(pend))
    ext = None
    if excl and a.external_pid:
        (eg, er), = excl
        ext = ThreadPoolExecutor(max_workers=1).submit(handle_external, eg, er, a.external_pid, pooled)
    lock = threading.Lock()
    def task(st, r):
        # lib/freeze.py (frozen) rewrites runs/freeze.json non-atomically at every child start-up; space the starts out so two children never write it at the same time
        with lock: time.sleep(2.5)
        return W.run_rep_capped(st, r, pooled)
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(task, st, r): (st, r) for st, r in pend}
        for f in as_completed(futs):
            st, r = futs[f]
            try:
                x = f.result()
                W.log(st, r, "converged", x["converged"], x.get("started_from"), x["last_attempt"]["draws"], f"{x['wall_seconds']}s", "TIMEOUT" if x.get("timeout") else "")
            except Exception as e:
                W.log(st, r, "ERROR", repr(e))
    if ext is not None:
        x = ext.result(); W.log(eg, er, "converged", x["converged"], x.get("started_from"), x["last_attempt"]["draws"], f"{x['wall_seconds']}s", "TIMEOUT" if x.get("timeout") else "", "(external)")
    res = W.summarise(names, el); W.log(json.dumps(res.get("G1", res["counts"]), default=str)[:600])
