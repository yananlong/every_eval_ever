"""W7 figures, all drawn with ArviZ (arviz_plots, matplotlib backend) into runs/W/W7/fig/:
  loo_pit_<name>.png      az.plot_loo_pit for F0 and each named fit (posterior predictive simulated from the fit's own
                          mean and concentration, w7_ppc.pit_tree)
  forest_hyper.png        az.plot_forest of the new hyperparameters (tau_l, tau_g, tau_delta, tau_fam, tau_u) over fits
  tstat_<cand>.png        az.plot_dist of log T1-T7 over a candidate's own model-true replicates (runs/W/W7/rep/<cand>),
                          with the observed value from <cand>_ppc.json added by az.add_lines; the same for F0 against
                          its W3 model-true replicates (tstat_F0.png)
Usage: w7_figs.py pit NAME:FEATURES:FOLDER ... | forest NAME:FOLDER ... | tstat CAND"""
import sys, json, os, warnings
from pathlib import Path
sys.path[:0] = ["runs/vendor/eci-public/src", "runs"]; warnings.filterwarnings("ignore")
import matplotlib; matplotlib.use("Agg")
import numpy as np, xarray as xr, arviz as az
import w7_ppc
from lib import ppc_checks as ppc

FIG = Path("runs/W/W7/fig"); FIG.mkdir(parents=True, exist_ok=True)
NEW = ["tau_delta", "tau_fam", "tau_l", "tau_g", "tau_u"]
az.style.use("arviz-variat")


def save(pc, path):
    pc.savefig(path, dpi=130); print("wrote", path)


def pit(specs):
    for s in specs:
        name, feats, folder = s.split(":"); feats = tuple(f for f in feats.split(",") if f)
        dt = w7_ppc.pit_tree(Path(folder) / f"{name}.nc", feats)
        pc = az.plot_loo_pit(dt, var_names="obs", backend="matplotlib")
        fig = pc.viz["figure"].item() if "figure" in pc.viz else None
        if fig is not None: fig.suptitle(f"LOO-PIT, {name} (Epoch's 2,879 rows)", fontsize=10)
        save(pc, FIG / f"loo_pit_{name}.png")


def forest(specs):
    trees = {}
    for s in specs:
        name, folder = s.split(":"); t = xr.open_datatree(Path(folder) / f"{name}.nc")
        have = [v for v in NEW if v in t["posterior"]]
        trees[name] = xr.DataTree.from_dict({"posterior": t["posterior"].to_dataset()[have]})
    present = [v for v in NEW if any(v in t["posterior"] for t in trees.values())]
    pc = az.plot_forest(trees, var_names=present, combined=True, ci_kind="eti", ci_probs=(0.5, 0.9), backend="matplotlib")
    if len(trees) > 1: pc.add_legend("model", title="fit")
    save(pc, FIG / "forest_hyper.png")


def tstat(cand):
    if cand == "F0":
        reps = [json.loads(p.read_text()) for p in Path("runs/W/W3/rep").glob("null_*.json")]
        obs = json.loads(Path("runs/W/W7/validate/f0_seed12345_ppc.json").read_text())["T"]
    else:
        reps = [json.loads(p.read_text()) for p in (Path("runs/W/W7/rep") / cand).glob("r*.json")]
        obs = json.loads(Path(f"runs/W/W7/{cand}_ppc.json").read_text())["T"]
    reps = [r for r in reps if r["converged"]]
    post = xr.Dataset({k: (("chain", "draw"), np.log([[r["T"][k] + 1e-12 for r in reps]])) for k in ppc.TNAMES})
    dt = xr.DataTree.from_dict({"posterior": post})
    pc = az.plot_dist(dt, kind="hist", point_estimate="median", ci_kind="eti", ci_prob=0.9, backend="matplotlib",
                      visuals={"title": True})
    az.add_lines(pc, values={k: float(np.log(obs[k] + 1e-12)) for k in ppc.TNAMES})
    fig = pc.viz["figure"].item() if "figure" in pc.viz else None
    if fig is not None:
        fig.suptitle(f"log T over {len(reps)} converged model-true replicates of {cand}; dashed line = observed value", fontsize=10)
    save(pc, FIG / f"tstat_{cand}.png")


if __name__ == "__main__":
    what, args = sys.argv[1], sys.argv[2:]
    dict(pit=pit, forest=forest, tstat=lambda a: [tstat(c) for c in a])[what](args)
