"""The frozen lib/fit.fit today, same call as W6 F2 (frozen builder, spec dev, seed 12345), into runs/W/W7/validate/fitfit;
compare its draws with runs/W/W6/F2.nc and with fit_mem's draws (memfit_check2 gave the same distance to F2.nc)."""
import sys; sys.path[:0] = ["runs/vendor/eci-public/src", "runs"]
import warnings; warnings.filterwarnings("ignore")
import numpy as np, xarray as xr, arviz as az, json
from pathlib import Path
import w7_memfit
from lib import data, models, expand, fit as fitmod
df = data.fit_input(); ex = expand.extras_info(df); out = Path("runs/W/W7/validate/fitfit")
fitmod.fit("F2_now", out, df, spec=models.Spec(("dev",), "epoch"), seed=12345, ex=ex, loglik=False)
side, tr = w7_memfit.fit_mem(df, models.Spec(("dev",), "epoch"), 12345, ex)
v = ["capability", "zeta", "tau_delta"]
a = az.extract(xr.open_datatree(out / "F2_now.nc"), var_names=v); m = az.extract(tr, var_names=v); b = az.extract(xr.open_datatree("runs/W/W6/F2.nc"), var_names=v)
res = dict(fitfit_vs_memfit={k: float(np.abs(a[k].to_numpy() - m[k].to_numpy()).max()) for k in v},
           fitfit_vs_W6F2={k: float(np.abs(a[k].to_numpy() - b[k].to_numpy()).max()) for k in v})
print("MEMFIT_CHECK3", res); open("runs/W/W7/validate/memfit_check3.json", "w").write(json.dumps(res))
