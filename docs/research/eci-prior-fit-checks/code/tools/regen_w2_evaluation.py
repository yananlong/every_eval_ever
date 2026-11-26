import sys, pickle, hashlib, warnings
from pathlib import Path
sys.path.insert(0, "runs"); warnings.filterwarnings("ignore")
import arviz as az
from lib import data
from eci.evaluation import evaluate_fit
trace = az.from_netcdf("runs/W/W2/seed12345.nc")
print("groups", trace.groups, flush=True)
df = data.fit_input()
ev = evaluate_fit(trace, df, max_draws=2000, performance_clip_eps=1e-3)
out = Path("runs/W/W2/seed12345_evaluation.pkl")
pickle.dump(ev, open(out, "wb"))
print("sha256", hashlib.sha256(out.read_bytes()).hexdigest(), out.stat().st_size)
print("keys", list(ev.keys()))
for k in ("metrics", "sampler_summary", "loo_summary", "calibration"):
    print("---", k); print(ev.get(k))
