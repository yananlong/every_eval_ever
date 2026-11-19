"""Anchor sensitivity (block WA): re-anchoring posterior draws, pair selection, invariance checks, anchor-free scales.
Post-processing only (numpy); no sampling. Paths are relative to the v11/ directory, as in the other entrypoints.
Epoch's map per draw s:  eci = T_low + (T_high - T_low) * (c - c_low) / (c_high - c_low)   (bayesian._anchor_transform)."""
import json
from pathlib import Path
import numpy as np
import xarray as xr

ORIG = ("Claude 3.5 Sonnet", "GPT-5")
ORIG_ECI = (130.0, 150.0)
SEEDS = (12345, 22345, 32345)
MIN_OBS, MIN_GAP = 20, 10.0
# Pre-declared (plan M11a / R28): low anchors at these positions of the eligible list (sorted by P0 mean ECI, 0 = lowest),
# high anchor = first eligible model whose P0 mean ECI is at least (low + span), for each minimum span in ECI points;
# plus the pair (lowest, highest eligible model).
LOW_POS = (0, 6, 12)
SPANS = (10.0, 15.0, 20.0)


def load_seed(seed, root="runs/W/W2"):
    """(eci (n, M), raw capability (n, M), names) for one W2 seed, chain-major."""
    t = xr.open_datatree(Path(root) / f"seed{seed}.nc")
    p = t["posterior"].to_dataset()
    names = [str(x) for x in p["model"].values]
    flat = lambda v: p[v].stack(s=("chain", "draw")).transpose("s", "model").to_numpy().astype("float64")
    return flat("eci"), flat("capability"), names


def obs_counts(names, zip_path="ext/epoch_zip/benchmark_data.zip"):
    from lib import data
    vc = data.fit_input(zip_path)["Model"].value_counts()
    return np.array([int(vc.get(n, 0)) for n in names])


def reanchor(draws, i_low, i_high, t_low, t_high):
    """Per-draw positive affine re-anchoring of draws (n, M) on any linear scale. Returns (new draws, scale b, n_bad).
    Draws with c_high <= c_low (no positive map) are returned as NaN rows and counted."""
    lo, hi = draws[:, i_low], draws[:, i_high]
    sp = hi - lo
    bad = ~(sp > 1e-12)
    b = np.where(bad, np.nan, (t_high - t_low) / np.where(bad, 1.0, sp))
    out = t_low + b[:, None] * (draws - lo[:, None])
    return out, b, int(bad.sum())


def eligible(names, counts, cap_pooled):
    """Pre-declared candidate set: at least MIN_OBS observed scores and posterior SD of raw capability at or below the
    median over all models. Returns (boolean mask, per-model SD, median SD)."""
    sd = cap_pooled.std(axis=0, ddof=1)
    med = float(np.median(sd))
    return (counts >= MIN_OBS) & (sd <= med), sd, med


def select_pairs(names, mean_eci, ok):
    """Deterministic pair list (original first). Eligible models sorted by P0 mean ECI (list e). For each low position
    in LOW_POS and each minimum span in SPANS: low = e[pos]; high = the first model above it in e with mean ECI >= low + span
    (dropped and listed if none); then the pair (e[0], e[-1]). A pair equal to an earlier one is skipped (listed)."""
    e = [int(i) for i in np.argsort(mean_eci) if ok[i]]
    io = tuple(names.index(a) for a in ORIG)
    cand = [("orig", *io, "original anchors (reproduction check)")]
    drops = []
    for pos in LOW_POS:
        for sp in SPANS:
            lo = e[pos]
            hi = next((i for i in e[pos + 1:] if mean_eci[i] - mean_eci[lo] >= sp), None)
            pid = f"L{pos}-S{int(sp)}"
            if hi is None: drops.append(dict(id=pid, reason="no eligible high anchor at the span")); continue
            cand.append((pid, lo, hi, f"low position {pos}, minimum span {sp:g}"))
    cand.append(("Full", e[0], e[-1], "lowest and highest eligible model"))
    pairs, seen = [], set()
    for pid, lo, hi, note in cand:
        if (lo, hi) in seen: drops.append(dict(id=pid, reason="duplicate of an earlier pair")); continue
        seen.add((lo, hi))
        pairs.append(dict(id=pid, low=names[lo], high=names[hi], low_idx=lo, high_idx=hi, note=note,
                          target_low=ORIG_ECI[0] if pid == "orig" else float(mean_eci[lo]),
                          target_high=ORIG_ECI[1] if pid == "orig" else float(mean_eci[hi])))
    return pairs, drops, len(e)


# ---------- summaries and invariance ----------
def widths(d):
    q = np.quantile(d, [.05, .95], axis=0)
    return q[1] - q[0]


def rank_matrix(d):
    return np.argsort(np.argsort(-d, axis=1), axis=1)


def p_matrix(d):
    """P(i > j) for all pairs, same draw index; (M, M)."""
    M = d.shape[1]
    out = np.empty((M, M))
    for i in range(M):
        out[i] = (d[:, i, None] > d).mean(axis=0)
    return out


def top10_p(d):
    return (rank_matrix(d) < 10).mean(axis=0)


def invariance(d0, dk):
    """Max abs differences between two draws arrays (same draw index): within-draw ranks, P(i > j) over all pairs, P(top 10)."""
    ok = ~np.isnan(dk).any(axis=1)
    d0, dk = d0[ok], dk[ok]
    r0, rk = rank_matrix(d0), rank_matrix(dk)
    return dict(n_draws=int(ok.sum()), max_abs_rank_diff=int(np.abs(r0 - rk).max()), n_rank_mismatch_draws=int((r0 != rk).any(axis=1).sum()),
                max_abs_pij_diff=float(np.abs(p_matrix(d0) - p_matrix(dk)).max()),
                max_abs_ptop10_diff=float(np.abs(top10_p(d0) - top10_p(dk)).max()))


def frontier_gaps(d, k=10):
    """Gaps (posterior-mean ECI) between adjacent models of the baseline top-k order, and the order itself."""
    m = d.mean(axis=0)
    order = np.argsort(-m)[:k]
    return order, m[order[:-1]] - m[order[1:]]


def zscore(d, robust=False):
    """Per-draw standardisation across models. Robust: (x - median) / IQR (IQR scaled by 1.349 to an SD-equivalent)."""
    if robust:
        q1, med, q3 = np.quantile(d, [.25, .5, .75], axis=1)
        return (d - med[:, None]) / ((q3 - q1) / 1.349)[:, None]
    return (d - d.mean(axis=1, keepdims=True)) / d.std(axis=1, ddof=1, keepdims=True)


def jload(p):
    return json.loads(Path(p).read_text())
