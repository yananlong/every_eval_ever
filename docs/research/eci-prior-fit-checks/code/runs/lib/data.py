"""Read the fit input and the per-row extras (developer cells, release gap) straight from the zip."""
import io, zipfile
import numpy as np, pandas as pd

ZIP = "ext/epoch_zip/benchmark_data.zip"
FIT = "epoch_capabilities_index/processed_data_for_eci.csv"
SCORES = "epoch_capabilities_index/eci_scores.csv"


def read_member(name, zip_path=ZIP):
    with zipfile.ZipFile(zip_path) as z:
        return pd.read_csv(io.BytesIO(z.read(name)))


def fit_input(zip_path=ZIP):
    return read_member(FIT, zip_path)


def extras(df, zip_path=ZIP):
    """Row-aligned arrays for the expansions (M14): developer cell index (-1 = none),
    release gap in years capped to [0, 3], index of the benchmark with most rows."""
    sc = read_member(SCORES, zip_path)
    org = df["Model"].map(sc.drop_duplicates("Model").set_index("Model")["Organization"])
    big = org.value_counts()
    big = big[big >= 20].index
    cnt = df.assign(org=org)[org.isin(big)].groupby(["org", "benchmark_id"]).size()
    cells = cnt[cnt >= 5].index.tolist()
    cell_id = {c: i for i, c in enumerate(cells)}
    cell_idx = np.array([cell_id.get((o, b), -1) for o, b in zip(org, df["benchmark_id"])])
    gap = (pd.to_datetime(df["date"]) - pd.to_datetime(df["benchmark_release_date"])).dt.days.to_numpy() / 365.25
    gap = np.clip(gap, 0.0, 3.0)
    bench_ids = df["benchmark_id"].unique()
    counts = df["benchmark_id"].value_counts()
    ref = int(np.argmax([counts[b] for b in bench_ids]))   # first maximum
    return dict(cell_idx=cell_idx, n_cells=len(cells), gap=gap, ref_bench=ref, n_orgs=len(big))
