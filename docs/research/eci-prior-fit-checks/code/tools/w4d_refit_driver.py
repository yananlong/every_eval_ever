"""Driver: refit the converged G-null replicates lacking a .nc, N at a time, 3600 s cap each (as W3 deviation 10)."""
import sys, json, glob, os, time, signal, subprocess, threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
N = int(sys.argv[1]) if len(sys.argv) > 1 else 44
OUT = Path("runs/W/W4d/null_refit/rep"); OUT.mkdir(parents=True, exist_ok=True)
todo = []
for p in sorted(glob.glob("runs/W/W3/rep/null_*.json")):
    d = json.load(open(p))
    if d["converged"] and not os.path.exists(p[:-5] + ".nc") and not (OUT / f"null_{d['r']}.nc").exists(): todo.append(d["r"])
print("todo", len(todo), flush=True); lock = threading.Lock()
def task(r):
    with lock: time.sleep(2.5)
    t0 = time.time()
    with open(OUT / f"null_{r}.log", "w") as f:
        p = subprocess.Popen([sys.executable, "../tools/w4d_refit_one.py", str(r)], start_new_session=True, stdout=f, stderr=subprocess.STDOUT)
        try: p.wait(timeout=3600); rc = p.returncode
        except subprocess.TimeoutExpired: os.killpg(p.pid, signal.SIGKILL); p.wait(); rc = "TIMEOUT"
    print(time.strftime("%H:%M:%S"), "rep", r, "rc", rc, f"{time.time()-t0:.0f}s", flush=True)
with ThreadPoolExecutor(N) as ex: list(ex.map(task, todo))
print("ALL DONE", flush=True)
