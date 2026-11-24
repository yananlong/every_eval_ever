"""Diagnose the AUG cell model: one pilot-like run (4 chains, 1,000 tune, 1,000 draws, target 0.95, Epoch's
pilot settings) with per-variable-group divergences, R-hat and ESS (az.rhat, az.ess), and 90% equal-tailed
intervals with medians from az.summary. Usage: aug_pilot_diag.py all|ind"""
import sys, json, warnings
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, pymc as pm, arviz as az
import aug_model
from lib import models
s = sys.argv[1]; df = pd.read_csv(f"runs/AUG/input_{s}.csv"); aug_model.install()
m = models.build_model(df, models.Spec(("cell",)), ex=dict(cell=df.cell.to_numpy(), obs_class=df.obs_class.to_numpy()))
with m:
    tr = pm.sample(draws=1000, tune=1000, chains=4, cores=4, target_accept=0.95, random_seed=12345, progressbar=False)
out = dict(divergences=int(tr.sample_stats["diverging"].sum()))
multi = df.groupby("cell").size(); multi = multi[multi > 1].index.to_numpy()
for v in ["tau_u", "beta_src", "sigma", "sigma_median", "tau_sigma", "tau_alpha", "capability", "difficulty", "slope", "zc"]:
    r = az.rhat(tr, var_names=[v])[v].to_numpy().ravel(); e = az.ess(tr, var_names=[v])[v].to_numpy().ravel()
    out[v] = dict(max_rhat=float(np.nanmax(r)), min_ess=float(np.nanmin(e)), n_rhat_gt_1_01=int((r > 1.01).sum()), n=len(r))
    if v == "zc":
        out["zc_multi"] = dict(max_rhat=float(np.nanmax(r[multi])), min_ess=float(np.nanmin(e[multi])))
        out["zc_single"] = dict(max_rhat=float(np.nanmax(np.delete(r, multi))), min_ess=float(np.nanmin(np.delete(e, multi))))
sm = az.summary(tr, var_names=["tau_u", "sigma_median", "beta_src"], kind="stats_median", ci_prob=0.9, ci_kind="eti", round_to="none")
q = lambda row: [float(row["eti90_lb"]), float(row["median"]), float(row["eti90_ub"])]
out["tau_u_q"] = q(sm.loc["tau_u"]); out["sigma_median_q"] = q(sm.loc["sigma_median"])
ex_ = az.extract(tr, var_names=["tau_u", "sigma_median"])
out["corr_tau_u_sigma_median"] = float(np.corrcoef(ex_["tau_u"].to_numpy(), ex_["sigma_median"].to_numpy())[0, 1])
out["beta_src_q"] = {c: q(sm.loc[f"beta_src[{c}]"]) for c in ("independent", "upstream-unknown")}
json.dump(out, open(f"runs/AUG/pilot_diag_{s}.json", "w"), indent=1); print(json.dumps(out, indent=1))
