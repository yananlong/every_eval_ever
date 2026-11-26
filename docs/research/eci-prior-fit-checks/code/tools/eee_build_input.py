"""Build the EEE fit input on Epoch's 2,879 cells (primary variant) and the mirror working root.
Primary variant: for each Epoch cell with at least one matched EEE pair, take the EEE normalised score from the
preferred source class (independent > same-upstream > upstream-unknown); within that class the highest score
across sources (Epoch's best-of rule). Cells without an EEE pair keep Epoch's value."""
import sys, os, io, json, zipfile, hashlib, shutil
import numpy as np, pandas as pd
sys.path.insert(0, "../tools"); from eee_xwalk_lib import *
OUT = "runs/EEE"; os.makedirs(OUT + "/input", exist_ok=True)
fr = json.load(open(XW + "/crosswalk_freeze.json"))
for f, h in fr["maps_sha256"].items():
    assert hashlib.sha256(open(XW + "/" + f, "rb").read()).hexdigest() == h, f"{f} changed after the audit"
aud = json.load(open(XW + "/audit_result.json")); assert aud["final_passed"]
fi = zread("epoch_capabilities_index/processed_data_for_eci.csv")
p = pd.read_csv(XW + "/pairs.csv")
PRI = {"independent": 0, "same-upstream": 1, "upstream-unknown": 2}
p["pri"] = p.source_class.map(PRI)
p = p.sort_values(["model_group", "eci_benchmark", "pri", "norm"], ascending=[True, True, True, False])
best = p.groupby(["model_group", "eci_benchmark"]).head(1).set_index(["model_group", "eci_benchmark"])
nsrc = p.groupby(["model_group", "eci_benchmark"]).src.nunique()
df = fi.copy()
key = list(zip(df.Model, df.benchmark))
df["epoch_performance"] = df.performance
df["eee_class"] = [best.source_class.get(k, "none") for k in key]
df["eee_source"] = [best.src.get(k, "") for k in key]
df["eee_n_sources"] = [int(nsrc.get(k, 0)) for k in key]
df["performance"] = [float(best.norm.get(k, e)) for k, e in zip(key, df.epoch_performance)]
df["absdiff"] = (df.performance - df.epoch_performance).abs()
df.to_csv(OUT + "/input/eee_fit_input_annotated.csv", index=False)
fit = df[fi.columns]
assert list(fit.columns) == list(fi.columns) and len(fit) == 2879 and (fit[["model_id", "benchmark_id"]].values == fi[["model_id", "benchmark_id"]].values).all()
fit.to_csv(OUT + "/input/processed_data_for_eci.csv", index=False)
# zip clone with only the fit-input member replaced
src = ZIP; dst = OUT + "/input/benchmark_data.zip"
with zipfile.ZipFile(src) as zi, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zo:
    for it in zi.infolist():
        data = zi.read(it.filename)
        if it.filename == "epoch_capabilities_index/processed_data_for_eci.csv":
            data = fit.to_csv(index=False).encode()
        zo.writestr(it, data)
cov = dict(cells=len(df), cells_with_eee=int((df.eee_class != "none").sum()),
           by_class=df.eee_class.value_counts().to_dict(),
           changed_gt_0015=int((df.absdiff > 0.0015).sum()), changed_gt_0_02=int((df.absdiff > 0.02).sum()), changed_gt_0_05=int((df.absdiff > 0.05).sum()), changed_gt_0_10=int((df.absdiff > 0.10).sum()),
           median_absdiff_changed=float(df.absdiff[df.absdiff > 0.0015].median()), mean_signed_diff_covered=float((df.performance - df.epoch_performance)[df.eee_class != "none"].mean()),
           models_with_eee=int(df[df.eee_class != "none"].Model.nunique()), models=int(df.Model.nunique()),
           benchmarks_with_eee=int(df[df.eee_class != "none"].benchmark.nunique()), benchmarks=int(df.benchmark.nunique()),
           anchors={a: dict(cells=int((df.Model == a).sum()), eee_cells=int(((df.Model == a) & (df.eee_class != "none")).sum()), changed=int(((df.Model == a) & (df.absdiff > 0.0015)).sum())) for a in ("Claude 3.5 Sonnet", "GPT-5")},
           zip_sha256=hashlib.sha256(open(dst, "rb").read()).hexdigest(), fit_input_sha256=hashlib.sha256(open(OUT + "/input/processed_data_for_eci.csv", "rb").read()).hexdigest())
bb = df.groupby("benchmark").agg(cells=("performance", "size"), eee=("eee_class", lambda s: int((s != "none").sum())), independent=("eee_class", lambda s: int((s == "independent").sum())),
                                 same_upstream=("eee_class", lambda s: int((s == "same-upstream").sum())), unknown=("eee_class", lambda s: int((s == "upstream-unknown").sum())),
                                 changed=("absdiff", lambda s: int((s > 0.0015).sum())), mean_absdiff=("absdiff", "mean")).sort_values("eee", ascending=False)
bb.to_csv(OUT + "/input/coverage_by_benchmark.csv")
mb = df.groupby("Model").agg(cells=("performance", "size"), eee=("eee_class", lambda s: int((s != "none").sum())), changed=("absdiff", lambda s: int((s > 0.0015).sum())), mean_absdiff=("absdiff", "mean"),
                             mean_signed=("performance", lambda s: 0.0)).drop(columns="mean_signed")
mb["mean_signed_diff"] = (df.performance - df.epoch_performance).groupby(df.Model).mean()
mb.sort_values("eee", ascending=False).to_csv(OUT + "/input/coverage_by_model.csv")
cov["models_by_eee_cells"] = {"0": int((mb.eee == 0).sum()), "1-2": int(mb.eee.between(1, 2).sum()), "3-5": int(mb.eee.between(3, 5).sum()), "6+": int((mb.eee >= 6).sum())}
# EEE-only matrix under Epoch's inclusion rule (G4 size condition for B5: >=15 benchmarks and >=100 models)
eo = df[df.eee_class != "none"]
cnt = eo.groupby("Model").benchmark.nunique(); mid = eo[eo.performance.between(0.1, 0.9)].groupby("Model").benchmark.nunique()
keep = set(cnt[cnt >= 4].index) & set(mid[mid >= 4].index)
eo2 = eo[eo.Model.isin(keep)]
cov["eee_only"] = dict(cells=int(len(eo)), models_meeting_inclusion=len(keep), benchmarks_in_those=int(eo2.benchmark.nunique()), cells_in_those=int(len(eo2)),
                       anchors_in={a: a in keep for a in ("Claude 3.5 Sonnet", "GPT-5")}, size_condition_15_benchmarks_100_models=bool(len(keep) >= 100 and eo2.benchmark.nunique() >= 15))
json.dump(cov, open(OUT + "/input/coverage.json", "w"), indent=1)
print(json.dumps(cov, indent=1)); print(bb.head(34).round(4).to_string())
