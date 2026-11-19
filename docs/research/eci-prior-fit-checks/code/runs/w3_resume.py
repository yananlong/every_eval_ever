"""Resume W3 without the .nc files: a replicate whose JSON is present, whose code digest matches or which timed out, counts as finished.

Same stages, order and options as w3_calibrate.py (which is left unchanged). Run from the work root, like every script here:
    runs/.venv/bin/python runs/w3_resume.py [--stage pc,null,2d,offset,shape,disp,drift] [--summarise]
w3_modrak.py still needs the .nc files, which this script does not recreate.
"""
import sys, json, time, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import w3_calibrate as W
from lib import generators as G

_orig = W.run_rep_capped


def run_rep_capped_nonc(gen, r, pooled=None):
    js = W.OUT / "rep" / f"{gen}_{r}.json"
    if js.exists():
        old = json.loads(js.read_text())
        if old.get("timeout") or old.get("code_sha256") == W.code_dig():
            return old
    return _orig(gen, r, pooled)


W.run_rep_capped = run_rep_capped_nonc

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--stage", default="pc,null,2d,offset,shape,disp,drift"); ap.add_argument("--summarise", action="store_true")
    a = ap.parse_args()
    df, scores, el, pat, pooled, names = W.setup()
    if not a.summarise:
        for st in a.stage.split(","):
            if st == "pc": W.run_positive_control(df, names); continue
            for r in range(G.REPS[st]):
                x = W.run_rep_capped(st, r, pooled)
                W.log(st, r, "converged", x["converged"], x.get("started_from"), x["last_attempt"]["draws"], f"{x['wall_seconds']}s", "TIMEOUT" if x.get("timeout") else "")
    res = W.summarise(names, el); W.log(json.dumps(res.get("G1", res["counts"]), default=str)[:600])
