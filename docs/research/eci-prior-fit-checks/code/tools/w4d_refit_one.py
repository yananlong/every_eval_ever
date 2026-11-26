"""Refit one converged G-null replicate through w3_calibrate.run_rep, writing to runs/W/W4d/null_refit/ (W3 files untouched). Usage: w4d_refit_one.py <r>"""
import sys, warnings
from pathlib import Path
sys.path.insert(0, "runs"); warnings.filterwarnings("ignore")
import w3_calibrate as W
import xarray as xr
from lib import data, generators as G, ppc_checks as ppc
W.OUT = Path("runs/W/W4d/null_refit")
(W.OUT / "rep").mkdir(parents=True, exist_ok=True); (W.OUT / "truth").mkdir(exist_ok=True)
# same as W.setup() minus freeze.freeze (which would rewrite runs/freeze.json)
df = data.fit_input(); scores = data.read_member(data.SCORES)
el = ppc.Elig(df, scores); pat = G.Pattern(df, scores)
t = xr.open_datatree(W.W2 / "seed12345.nc"); post = t["posterior"].to_dataset()
pooled = {v: post[v].stack(s=("chain", "draw")).transpose("s", ...).to_numpy() for v in ["capability", "difficulty", "slope", "sigma", "tau_alpha", "sigma_median", "tau_sigma"]}
names = [str(x) for x in post["model"].values]
low, high = names.index("Claude 3.5 Sonnet"), names.index("GPT-5")
W.run_rep("null", int(sys.argv[1]), df, el, pat, pooled, names, low, high)
