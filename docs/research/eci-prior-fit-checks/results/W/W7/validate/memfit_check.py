"""Check that runs/w7_memfit.fit_mem reproduces a fit made by the frozen lib/fit.fit (W6 F2: spec dev, seed 12345)."""
import sys; sys.path[:0] = ["runs/vendor/eci-public/src", "runs"]
import warnings; warnings.filterwarnings("ignore")
import numpy as np, xarray as xr, arviz as az, json
import w7_models as w7, w7_data, w7_memfit
from lib import models
w7.install(); df, ex = w7_data.load("orig")
side, tr = w7_memfit.fit_mem(df, models.Spec(("dev",)), 12345, ex)
ref = xr.open_datatree("runs/W/W6/F2.nc")
a = az.extract(tr, var_names=["capability", "zeta", "tau_delta"]); b = az.extract(ref, var_names=["capability", "zeta", "tau_delta"])
out = {v: float(np.abs(a[v].to_numpy() - b[v].to_numpy()).max()) for v in ("capability", "zeta", "tau_delta")}
out.update(converged=side["converged"], started_from=side["started_from"], ref=json.load(open("runs/W/W6/F2.json"))["started_from"])
print("MEMFIT_CHECK", out); open("runs/W/W7/validate/memfit_check.json", "w").write(json.dumps(out))
