"""runs/freeze.json: sha256 digests of frozen files, written at the freeze points of M10, checked before use."""
import json, hashlib
from pathlib import Path
RUNS = Path(__file__).resolve().parents[1]
FJ = RUNS / "freeze.json"
PLAN = RUNS.parent.parent / "wt-pr14/docs/research/eci-prior-fit-checks"   # frozen plan copy
PATHS = {"prior-grid.json": PLAN / "prior-grid.json", "sens_metrics.py": RUNS / "lib/sens_metrics.py",
         "ppc_checks.py": RUNS / "lib/ppc_checks.py", "sbc.py": RUNS / "lib/sbc.py", "models.py": RUNS / "lib/models.py",
         "compare.py": RUNS / "lib/compare.py", "strata.json": RUNS / "strata.json"}


AMENDMENTS = {"prior-grid.json": ("jeffreys_prior_exploratory", "jeffreys_priors_exploratory")}   # exploratory keys added by the owner after the freeze (R26)


def sha(p):
    p = Path(p)
    if p.name == "prior-grid.json":   # digest of the grid without the exploratory entries added after the freeze
        g = json.loads(p.read_text())
        for k in AMENDMENTS["prior-grid.json"]: g.pop(k, None)
        return hashlib.sha256((json.dumps(g, indent=2) + "\n").encode()).hexdigest()
    return hashlib.sha256(p.read_bytes()).hexdigest()


def freeze(*names, extra=None):
    d = json.loads(FJ.read_text())
    for n in names:
        p = PATHS[n]
        new = sha(p)
        if n in d["frozen"] and d["frozen"][n] != new:
            raise RuntimeError(f"{n} changed after freeze")
        d["frozen"][n] = new
    for k, v in (extra or {}).items(): d[k] = v
    FJ.write_text(json.dumps(d, indent=1))


def check(*names):
    d = json.loads(FJ.read_text())
    for n in names:
        if d["frozen"].get(n) != sha(PATHS[n]):
            raise RuntimeError(f"{n} is not frozen or has changed")
