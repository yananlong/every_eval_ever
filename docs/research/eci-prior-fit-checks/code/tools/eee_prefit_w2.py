"""Prefit one W2 fit with exactly the arguments w2_fit.py uses, so w2_fit.py (unmodified) skips it through the
sidecar match. usage (from the EEE mirror root): eee_prefit_w2.py seed12345|seed22345|seed32345|loader_input|f0_seed12345|f0_seed22345"""
import sys, warnings; sys.path.insert(0, "runs"); warnings.filterwarnings("ignore")
from pathlib import Path
from lib import data, fit, models
name = sys.argv[1]; OUT = Path("runs/W/W2")
df = data.fit_input()
if name.startswith("seed"):
    s, _ = fit.fit(name, OUT, df, spec=None, seed=int(name[4:]), evaluate=True)
elif name == "loader_input":
    from eci import prepare_benchmark_data
    s, _ = fit.fit(name, OUT, prepare_benchmark_data(Path(data.ZIP)), spec=None, seed=12345, evaluate=False)
else:
    s, _ = fit.fit(name, OUT, df, spec=models.Spec(), seed=int(name[7:]), loglik=True)
print(name, "converged", s["converged"], s["started_from"], s["last_attempt"], "wall", s["wall_seconds"], flush=True)
