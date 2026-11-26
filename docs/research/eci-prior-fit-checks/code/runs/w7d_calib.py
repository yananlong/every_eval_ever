"""Calibrated max-T p for a W7 follow-up candidate against its own model-true replicates
(runs/W/W7/diag/rep/<cand>/r*.json from `w7d_fit.py --rep`), with the frozen lib/ppc_checks.max_t. Non-converged and
capped replicates are counted and excluded, as W3 and W7 do. Replicate distributions are summarised with az.eti (90%).
With the candidate's .npz on stdin it also runs the convergence-selection check of runs/w7_selection.py: every
started replicate's scores are regenerated from the same draw and seed, and capped and converged replicates are
compared (Mann-Whitney) on the posterior position, the share of scores at each bound, and T1-T7 against the
generating draw. Usage: w7d_calib.py CAND FEATURES CLUSTERS STARTED_FILE  [< CAND.npz]"""
import sys, json, io, hashlib
from pathlib import Path
sys.path[:0] = ["runs/vendor/eci-public/src", "runs"]
import warnings; warnings.filterwarnings("ignore")
import numpy as np, xarray as xr, arviz as az
from scipy.stats import mannwhitneyu
from lib import data, ppc_checks as ppc
import w7d_models as wd, w7_data

cand, feats, clu, started_file = sys.argv[1], tuple(f for f in sys.argv[2].split(",") if f), int(sys.argv[3]), sys.argv[4]
D = Path("runs/W/W7/diag"); R_dir = D / "rep" / cand
reps = [json.loads(p.read_text()) for p in sorted(R_dir.glob("r*.json"))]
conv = [r for r in reps if r["converged"]]
status = {}
for line in Path(started_file).read_text().splitlines():
    p = line.split()
    if len(p) >= 3 and p[1] == "exit": status[int(p[0][1:])] = int(p[2])
obs = json.loads((D / f"{cand}.json").read_text())["T"]
res = ppc.max_t(obs, [r["T"] for r in conv])
ds = xr.Dataset({k: (("chain", "draw"), [[r["T"][k] for r in conv]]) for k in ppc.TNAMES})
eti = az.eti(xr.DataTree.from_dict({"posterior": ds}), prob=0.9); eti = eti.to_dataset() if isinstance(eti, xr.DataTree) else eti
out = dict(cand=cand, ended=len(status), finished=len(reps), converged=len(conv), not_converged=len(reps) - len(conv),
           capped=sum(1 for v in status.values() if v == 124), failed_other=sum(1 for r_, v in status.items() if v not in (0, 124)),
           p_floor=1 / (len(conv) + 1), wall_median_s=float(np.median([r["wall_seconds"] for r in reps])) if reps else None,
           started_from={s: sum(1 for r in conv if r["started_from"] == s) for s in ("pilot", "cold")},
           max_t=res, rep_eti90={k: [float(x) for x in eti[k].to_numpy()] for k in ppc.TNAMES},
           rep_max={k: float(max(r["T"][k] for r in conv)) for k in ppc.TNAMES},
           rejected_at_0_01=[k for k in ppc.TNAMES if res[k]["p_adjusted"] < 0.01],
           maxima_q95={k: float(np.quantile([r["maxima"][k] for r in conv], .95)) for k in ("Qb", "q", "t", "cb")})
print(cand, f"{len(conv)} converged of {len(status)} ended ({out['capped']} capped, {out['not_converged']} finished without converging); p floor {out['p_floor']:.4f}")
for k in ppc.TNAMES:
    print(f"  {k} obs {obs[k]:.3f} rep90 {out['rep_eti90'][k][0]:.3f}-{out['rep_eti90'][k][1]:.3f} max {out['rep_max'][k]:.3f} p_unadj {res[k]['p_unadjusted']:.4f} p_adj {res[k]['p_adjusted']:.4f}")
print("  rejected at 0.01:", out["rejected_at_0_01"] or "none")
if not sys.stdin.isatty():
    raw = sys.stdin.buffer.read()
    if raw:
        Z = np.load(io.BytesIO(raw)); df, ex = w7_data.load("orig"); ex["clusters"] = wd.CLUSTERS if clu else None
        el = ppc.Elig(df, data.read_member(data.SCORES)); VN = wd.var_names(feats); rows = []
        okset = {r["r"] for r in conv}
        for r in sorted(status):
            Pi = {k: Z["rep_" + k][r:r + 1] for k in VN}
            seed = int.from_bytes(hashlib.sha256(f"w7d:{cand}:{r}".encode()).digest()[:4], "big")
            pr = wd.predict(feats, Pi, df, ex); y = wd.simulate({k: v[0] for k, v in pr.items()}, np.random.default_rng(seed))
            T = ppc.stats(np.clip(y, wd.EPS, 1 - wd.EPS), wd.rq(pr, Pi), el, with_components=False)
            rows.append(dict(r=r, group="converged" if r in okset else ("capped" if status[r] == 124 else "other"), position_frac=float(Z["rep_pos"][r]) / 4000,
                             share_y_le_eps=float((y <= wd.EPS).mean()), share_y_ge_1_eps=float((y >= 1 - wd.EPS).mean()), **{f"T_gen.{k}": v for k, v in T.items()}))
        sel = {}
        a_ = [x for x in rows if x["group"] == "converged"]; b_ = [x for x in rows if x["group"] != "converged"]
        for k in [k for k in rows[0] if k not in ("r", "group")]:
            if len(a_) > 2 and len(b_) > 2:
                sel[k] = dict(converged_median=float(np.median([x[k] for x in a_])), not_converged_median=float(np.median([x[k] for x in b_])),
                              mw_p=float(mannwhitneyu([x[k] for x in a_], [x[k] for x in b_]).pvalue))
        out["selection"] = dict(n_converged=len(a_), n_not=len(b_), tests=sel)
        print("  selection (converged vs capped or not converged):", {k: round(v["mw_p"], 3) for k, v in sel.items()})
(D / f"{cand}_calib.json").write_text(json.dumps(out, indent=1, default=float))
