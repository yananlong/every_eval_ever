import sys, glob, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "ext/eci-public/src")
from eci import dataloader as dl
z = sorted(glob.glob("ext/epoch_zip/*.zip"))[0]
dfs = dl.download_benchmark_data(z, None)
md = dl.load_benchmark_metadata(dfs); md = md[md["in_eci"]]
raw = dl._load_raw_scores(dfs, md)
print("zip", z)
print("raw rows in in-ECI benchmarks", len(raw), "benchmarks", raw.benchmark.nunique(), "model versions", raw.model_version.nunique())
norm = dl._normalize_scores(raw, md); print("after normalise (numeric score)", len(norm))
def run(**kw):
    d = dl.prepare_benchmark_data(z, **kw)
    mc = "model" if "model" in d.columns else d.columns[0]
    return len(d), d[mc].nunique(), d["benchmark"].nunique()
print("dedup to model group x benchmark, no date/min filters", run(min_date="1900-01-01", min_benchmarks_per_model=0, min_mid_range_benchmarks_per_model=0))
print("+ date >= 2023-01-01", run(min_benchmarks_per_model=0, min_mid_range_benchmarks_per_model=0))
print("+ >=4 benchmarks", run(min_mid_range_benchmarks_per_model=0))
print("+ >=4 mid-range benchmarks (default)", run())
