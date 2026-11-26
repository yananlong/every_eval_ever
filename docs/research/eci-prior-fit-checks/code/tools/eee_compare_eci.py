"""ECI under Epoch's model: Epoch-data fit (runs/W/W2/seed12345.nc) against EEE-data fit (runs/EEE/W2/seed12345.nc).
Run from eci_work/v11 (the real root). Writes runs/EEE/eci_compare.json and eci_compare.csv."""
import sys, json, warnings; sys.path.insert(0, "runs"); warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from scipy.stats import spearmanr, kendalltau
from lib import fit, sens_metrics as sm
dE, nE, _ = fit.load_eci("runs/W/W2/seed12345.nc"); dX, nX, _ = fit.load_eci("runs/EEE/W2/seed12345.nc")
assert list(nE) == list(nX); names = list(nE)
strata = json.load(open("runs/strata.json"))
ann = pd.read_csv("runs/EEE/input/eee_fit_input_annotated.csv")
def summ(d): return dict(mean=d.mean(0), lo=np.quantile(d, .05, 0), hi=np.quantile(d, .95, 0))
E, X = summ(dE), summ(dX)
t = pd.DataFrame(dict(model=names, eci_epoch=E["mean"], eci_eee=X["mean"], lo_epoch=E["lo"], hi_epoch=E["hi"], lo_eee=X["lo"], hi_eee=X["hi"]))
t["shift"] = t.eci_eee - t.eci_epoch; t["w_epoch"] = t.hi_epoch - t.lo_epoch; t["w_eee"] = t.hi_eee - t.lo_eee
t["shift_over_w"] = t["shift"] / t.w_epoch
t["intervals_intersect"] = (t.lo_eee <= t.hi_epoch) & (t.lo_epoch <= t.hi_eee)
g = ann.groupby("Model")
t["cells"] = t.model.map(g.size()); t["eee_cells"] = t.model.map(g.eee_class.apply(lambda s: int((s != "none").sum())))
t["changed_cells"] = t.model.map(g.absdiff.apply(lambda s: int((s > 0.0015).sum())))
t["mean_signed_score_diff"] = t.model.map((ann.performance - ann.epoch_performance).groupby(ann.Model).mean())
t["rank_epoch"] = t.eci_epoch.rank(ascending=False).astype(int); t["rank_eee"] = t.eci_eee.rank(ascending=False).astype(int)
anch = t.model.isin(sm.ANCHORS); na = ~anch
out = {}
for k in ("all", "frontier", "sparse", "dense"):
    m = t.model.isin(set(strata[k])) & na if k != "all" else na
    s = t[m]
    out[k] = dict(n=int(len(s)), spearman=float(spearmanr(s.eci_epoch, s.eci_eee).statistic), kendall=float(kendalltau(s.eci_epoch, s.eci_eee).statistic),
                  mean_shift=float(s["shift"].mean()), median_abs_shift=float(s["shift"].abs().median()), max_abs_shift=float(s["shift"].abs().max()),
                  argmax=str(s.loc[s["shift"].abs().idxmax(), "model"]), n_abs_shift_gt_1=int((s["shift"].abs() > 1).sum()), n_abs_shift_gt_2=int((s["shift"].abs() > 2).sum()),
                  n_shift_gt_quarter_W=int((s.shift_over_w.abs() > .25).sum()), share_intervals_intersect=float(s.intervals_intersect.mean()),
                  median_width_ratio=float((s.w_eee / s.w_epoch).median()))
top = lambda c: list(t.sort_values(c, ascending=False).model[:10])
tE, tX = top("eci_epoch"), top("eci_eee")
out["top10"] = dict(epoch=tE, eee=tX, same_set=set(tE) == set(tX), same_order=tE == tX, n_common=len(set(tE) & set(tX)))
out["top10_table"] = [dict(model=m, rank_epoch=int(t.set_index("model").rank_epoch[m]), rank_eee=int(t.set_index("model").rank_eee[m]),
                           eci_epoch=float(t.set_index("model").eci_epoch[m]), eci_eee=float(t.set_index("model").eci_eee[m])) for m in dict.fromkeys(tE + tX)]
out["spearman_all_models"] = float(spearmanr(t.eci_epoch, t.eci_eee).statistic)
out["G5"] = dict(spearman=out["all"]["spearman"], share_intersect=out["all"]["share_intervals_intersect"], anchors_present=True,
                 passes=bool(out["all"]["spearman"] >= .9 and out["all"]["share_intervals_intersect"] >= .8),
                 note="G5 was registered for an EEE-only matrix (B5); here it is read on the substitution matrix")
out["largest_shifts"] = t[na].reindex(t[na]["shift"].abs().sort_values(ascending=False).index)[["model", "eci_epoch", "eci_eee", "shift", "w_epoch", "eee_cells", "changed_cells", "cells", "mean_signed_score_diff"]].head(12).round(3).to_dict("records")
out["shift_vs_changed_cells"] = dict(spearman_abs_shift_vs_share_changed=float(spearmanr(t[na]["shift"].abs(), (t.changed_cells / t.cells)[na]).statistic),
                                     models_with_no_changed_cell=int((t.changed_cells[na] == 0).sum()), median_abs_shift_no_changed=float(t[na & (t.changed_cells == 0)]["shift"].abs().median()),
                                     median_abs_shift_changed=float(t[na & (t.changed_cells > 0)]["shift"].abs().median()))
# S1-S4 scoring with the frozen sens_metrics (EEE-data fit scored against the Epoch-data fit as baseline)
try:
    masks = {k: np.array([n in set(strata[k]) for n in names]) for k in ("all", "frontier", "sparse", "dense")}
    sc = sm.score(dX, dE, names, masks)
    for k in sc:
        if isinstance(sc[k], dict): sc[k].pop("p_top10_k", None); sc[k].pop("p_top10_0", None)
    out["S1_S4_eee_vs_epoch"] = sc
except Exception as e: out["S1_S4_error"] = repr(e)
t.round(4).to_csv("runs/EEE/eci_compare.csv", index=False)
json.dump(out, open("runs/EEE/eci_compare.json", "w"), indent=1, default=str)
print(json.dumps({k: out[k] for k in ("all", "frontier", "top10", "G5", "shift_vs_changed_cells")}, indent=1, default=str)); print(pd.DataFrame(out["largest_shifts"]).to_string()); print(pd.DataFrame(out["top10_table"]).round(2).to_string())
