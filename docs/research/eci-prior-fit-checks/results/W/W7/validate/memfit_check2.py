"""fit_mem with the frozen builder (as runs/w6_fit_one.py fits W6 F2): must reproduce runs/W/W6/F2.nc draw for draw."""
import sys; sys.path[:0] = ["runs/vendor/eci-public/src", "runs"]
import warnings; warnings.filterwarnings("ignore")
import numpy as np, xarray as xr, arviz as az, json
import w7_memfit
from lib import data, models, expand
df = data.fit_input(); ex = expand.extras_info(df)
side, tr = w7_memfit.fit_mem(df, models.Spec(("dev",), "epoch"), 12345, ex)
ref = xr.open_datatree("runs/W/W6/F2.nc")
a = az.extract(tr, var_names=["capability", "zeta", "tau_delta"]); b = az.extract(ref, var_names=["capability", "zeta", "tau_delta"])
out = {v: float(np.abs(a[v].to_numpy() - b[v].to_numpy()).max()) for v in ("capability", "zeta", "tau_delta")}
out.update(converged=side["converged"], started_from=side["started_from"])
print("MEMFIT_CHECK2", out); open("runs/W/W7/validate/memfit_check2.json", "w").write(json.dumps(out))
