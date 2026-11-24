"""BSEL (benchmark-selection sensitivity, exploratory except A4): shared helpers.
Subsetting with Epoch's inclusion rule re-applied, and the comparison of one refit with P0 (runs/W/W5/P0.npz).
Run from the v11 root.  Nothing in runs/lib or runs/vendor is modified; sens_metrics.score is used as is."""
import json, sys
from pathlib import Path
import numpy as np

RUNS = Path("runs").resolve()
if str(RUNS) not in sys.path: sys.path.insert(0, str(RUNS))
OUT = Path("runs/W/BSEL")
P0_NPZ, P0_NC = Path("runs/W/W5/P0.npz"), Path("runs/W/W5/P0.nc")
ANCHORS = ("Claude 3.5 Sonnet", "GPT-5")
A4 = ["DTBench", "GPQA diamond", "MATH level 5", "METR Time Horizons", "OTIS Mock AIME 2024-2025", "SimpleBench", "VPCT", "WeirdML"]
CLUSTERS = {
    "C_FM": ["FrontierMath-Tiers-1-3-v2-Private", "FrontierMath-Tier-4-v2-Private", "FrontierMath-2025-02-28-Private", "FrontierMath-Tier-4-2025-07-01-Private"],
    "C_ARC": ["ARC-AGI", "ARC-AGI-2"],
    "C_OTIS_LMCA": ["OTIS Mock AIME 2024-2025", "LMCA"],
    "C_OLD": ["HellaSwag", "PIQA", "Winogrande", "TriviaQA", "GSM8K"],
}
RNG_SEED, N_RANDOM, RANDOM_FRAC = 20261121, 20, 0.2
FIT_SEED, DRAWS = 12345, 4000


def apply_inclusion(df):
    """Epoch's rule as in eci.dataloader.prepare_benchmark_data step 7: >= 4 distinct benchmarks per model group, then
    >= 4 distinct benchmarks with score in [0.1, 0.9] (Epoch's filter_mid_range_models, unmodified)."""
    from eci import dataloader as dl
    counts = df.groupby("model")["benchmark"].nunique()
    df = df[df["model"].isin(counts[counts >= 4].index)]
    return dl.filter_mid_range_models(df, 4, (0.1, 0.9), model_col="model")


def subset(df, drop):
    """Delete the rows of the benchmarks in `drop`, re-apply the inclusion rule. Returns (df_sub, dropped_models)."""
    unknown = set(drop) - set(df["benchmark"])
    if unknown: raise ValueError(f"unknown benchmarks {sorted(unknown)}")
    kept = df[~df["benchmark"].isin(drop)]
    before = list(dict.fromkeys(kept["Model"]))
    sub = apply_inclusion(kept)
    after = set(sub["Model"])
    gone_entirely = sorted(set(df["Model"]) - set(kept["Model"]))   # every score was on dropped benchmarks
    return sub, sorted(set(before) - after) + gone_entirely


def load_p0():
    import xarray as xr
    t = xr.open_datatree(P0_NC); p = t["posterior"].to_dataset()
    names = [str(x) for x in p["model"].values]
    cap = p["capability"].stack(s=("chain", "draw")).transpose("s", "model").to_numpy()
    lo, hi = names.index(ANCHORS[0]), names.index(ANCHORS[1])
    eci = np.load(P0_NPZ)["eci"].astype("float64")
    return dict(names=names, eci=eci, cap_low=cap[:, lo], cap_high=cap[:, hi])


def strata():
    return json.loads(Path("runs/strata.json").read_text())


def anchor_block(cap_low, cap_high):
    b = 20.0 / (cap_high - cap_low)
    return dict(cap_low_mean=float(np.mean(cap_low)), cap_low_sd=float(np.std(cap_low)), cap_high_mean=float(np.mean(cap_high)), cap_high_sd=float(np.std(cap_high)),
                spread_mean=float(np.mean(cap_high - cap_low)), spread_sd=float(np.std(cap_high - cap_low)),
                b_mean=float(np.mean(b)), b_sd_over_mean=float(np.std(b) / np.mean(b)))


def compare(eci_k, names_k, p0, n_rows_k=None, n_rows_full=None):
    """All BSEL quantities of one refit (draws eci_k, names_k) against P0, on the models present in both."""
    from lib import sens_metrics as sm
    st = strata()
    idx0 = {n: i for i, n in enumerate(p0["names"])}
    common = [n for n in names_k if n in idx0]
    ik = np.array([names_k.index(n) for n in common]); i0 = np.array([idx0[n] for n in common])
    ek, e0 = eci_k[:, ik], p0["eci"][:, i0]
    masks = {s: np.array([n in set(st[s]) for n in common]) for s in ("all", "frontier", "sparse", "dense")}
    sc = sm.score(ek, e0, common, masks)
    p_top10_k, p_top10_0 = sc["S4"].pop("p_top10_k"), sc["S4"].pop("p_top10_0")
    sk, s0 = sm.summarise(ek), sm.summarise(e0)
    anchor = np.array([n in ANCHORS for n in common])
    d = sk["mean"] - s0["mean"]; rel = np.abs(d) / np.where(anchor, np.nan, s0["width"]); wr = sk["width"] / np.where(anchor, np.nan, s0["width"])
    o0, ok_ = np.argsort(-s0["mean"]), np.argsort(-sk["mean"])
    top0, topk = [common[i] for i in o0[:10]], [common[i] for i in ok_[:10]]
    full_top10 = [p0["names"][i] for i in np.argsort(-p0["eci"].mean(0))[:10]]

    def gaps(mask):
        dd = d[mask]; g = np.abs(dd[:, None] - dd[None, :])[np.triu_indices(mask.sum(), 1)]
        return dict(n_pairs=int(g.size), median_abs_gap_change=float(np.median(g)), max_abs_gap_change=float(np.max(g)))

    fm = masks["frontier"]
    stretch = lambda m: float(np.sort(m)[::-1][0] - np.sort(m)[::-1][19])
    fr = dict(stretch_rank1_minus_rank20_k=stretch(sk["mean"]), stretch_rank1_minus_rank20_p0=stretch(s0["mean"]),
              stratum_max_minus_min_k=float(sk["mean"][fm].max() - sk["mean"][fm].min()), stratum_max_minus_min_p0=float(s0["mean"][fm].max() - s0["mean"][fm].min()))
    fr["stretch_change"] = fr["stretch_rank1_minus_rank20_k"] - fr["stretch_rank1_minus_rank20_p0"]
    fr["stratum_range_change"] = fr["stratum_max_minus_min_k"] - fr["stratum_max_minus_min_p0"]
    fna = fm & ~anchor
    fr["max_abs_shift"] = float(np.max(np.abs(d[fna]))); fr["max_rel_shift"] = float(np.nanmax(rel[fna]))
    fr["mean_signed_shift"] = float(np.mean(d[fna])); fr["median_width_ratio"] = float(np.nanmedian(wr[fna]))
    # by P0 ECI quintile (non-anchor models): low end against frontier
    na = ~anchor; q = np.quantile(s0["mean"][na], [0.2, 0.4, 0.6, 0.8]); qi = np.digitize(s0["mean"], q)
    quint = [dict(q=int(k + 1), n=int((na & (qi == k)).sum()), p0_eci_range=[float(s0["mean"][na & (qi == k)].min()), float(s0["mean"][na & (qi == k)].max())],
                  median_abs_shift=float(np.median(np.abs(d[na & (qi == k)]))), median_rel_shift=float(np.nanmedian(rel[na & (qi == k)])),
                  mean_signed_shift=float(np.mean(d[na & (qi == k)])), median_width_ratio=float(np.nanmedian(wr[na & (qi == k)]))) for k in range(5)]
    from scipy.stats import spearmanr
    mv = np.argsort(-np.nan_to_num(np.abs(d) * na))[:10]
    movers = [dict(model=common[i], p0_eci=float(s0["mean"][i]), eci=float(sk["mean"][i]), shift=float(d[i]), rel_shift=float(rel[i]), width_ratio=float(wr[i]),
                   rows_full=None if n_rows_full is None else int(n_rows_full.get(common[i], 0)), rows_sub=None if n_rows_k is None else int(n_rows_k.get(common[i], 0)),
                   strata=[s for s in ("frontier", "sparse", "dense") if masks[s][i]]) for i in mv]
    return dict(n_common=len(common), scores=sc,
                top10=dict(p0=top0, refit=topk, set_same=set(top0) == set(topk), order_same=top0 == topk, entered=[n for n in topk if n not in top0], left=[n for n in top0 if n not in topk],
                           p0_full_top10_dropped=[n for n in full_top10 if n not in common],
                           rank_changes={n: int(topk.index(n) - top0.index(n)) if n in topk else None for n in top0}),
                frontier=fr, gaps=dict(frontier=gaps(fm), all=gaps(np.ones(len(common), bool))),
                shift=dict(median_abs_all=float(np.median(np.abs(d[na]))), max_abs_all=float(np.max(np.abs(d[na]))), mean_signed_all=float(np.mean(d[na])),
                           spearman_shift_vs_p0eci=float(spearmanr(d[na], s0["mean"][na]).statistic),
                           median_width_ratio_all=float(np.nanmedian(wr[na])), by_p0_quintile=quint),
                movers=movers,
                p_top10_changes=sorted([dict(model=common[i], p0=float(p_top10_0[i]), refit=float(p_top10_k[i])) for i in range(len(common)) if abs(p_top10_k[i] - p_top10_0[i]) >= 0.1],
                                       key=lambda r: -abs(r["refit"] - r["p0"])))
