"""W7 diagnostics (exploratory, follows deviations entry 15): shared helpers for runs/w7d_*.py.
Nothing here edits runs/lib, runs/vendor or the existing runs/w7_*.py; it only imports them.
  meta()          per-benchmark metadata (rows, release date, Epoch tags, domain, interaction style, source kind)
  bundle_g3()     residual quantities, standardised residuals, pointwise PSIS-LOO and LOO-PIT for a W7 fit stored as .nc
  pp_envelope()   posterior predictive draws of the standardised residuals with the residual quantities held fixed
  rep_maxima()    family-wise thresholds from the model-true replicates' stored maxima (runs/W/W7/rep/<cand>/r*.json)
"""
import csv, json
from pathlib import Path
import numpy as np, pandas as pd, xarray as xr, arviz as az

EPS = 1e-3
DIAG = Path("runs/W/W7/diag")
INTERNAL = {  # benchmarks Epoch runs itself (zip members without the _external suffix): name -> member
    "GPQA diamond": "gpqa_diamond.csv", "MATH level 5": "math_level_5.csv", "SWE-Bench verified": "swe_bench_verified.csv",
    "OTIS Mock AIME 2024-2025": "otis_mock_aime_2024_2025.csv", "FrontierMath-2025-02-28-Private": "frontiermath.csv",
    "FrontierMath-Tier-4-2025-07-01-Private": "frontiermath_tier_4.csv",
    "FrontierMath-Tiers-1-3-v2-Private": "frontiermath_tiers_1_3_v2.csv", "FrontierMath-Tier-4-v2-Private": "frontiermath_tier_4_v2.csv",
    "EBR-bench": "ebr_bench.csv", "SimpleQA Verified": "simpleqa_verified.csv", "Chess Puzzles": "chess_puzzles.csv",
    "Mystery Game Puzzles": "mystery_game_puzzles.csv", "MirrorCode": "mirrorcode.csv", "Furniture Assembly": "furniture_assembly.csv",
    "SpireClimb": "spireclimb.csv"}


def meta(df, el):
    tax = {r["benchmark"]: r for r in csv.DictReader(open("runs/TAX/combined_eci_map.csv"))}
    rows = []
    for b, name in enumerate(el.bench_names):
        sub = df[df["benchmark"] == name]; t = tax.get(name, {})
        rows.append(dict(b=b, benchmark=name, n=len(sub), release=str(sub["benchmark_release_date"].iloc[0])[:10],
                         year=int(str(sub["benchmark_release_date"].iloc[0])[:4]), tags=t.get("epoch_tags", ""),
                         domain=t.get("primary_domain", ""), style=t.get("interaction_style", ""),
                         epoch_run=name in INTERNAL, n_sources=sub["source"].nunique(),
                         zeros=int((sub["performance"] <= EPS).sum()), ones=int((sub["performance"] >= 1 - EPS).sum())))
    return pd.DataFrame(rows)


def short(name, n=22):
    s = (name.replace("FrontierMath", "FM").replace("-Private", "").replace("2024-2025", "").replace("Mock ", "")
         .replace("Puzzles", "Puz.").replace("Assembly", "Asm.").replace("Time Horizons", "TH").replace("verified", "ver.")
         .replace("-2025-02-28", " v1").replace("-Tier-4-2025-07-01", " T4 v1").replace("-Tier-4-v2", " T4 v2").replace("-Tiers-1-3-v2", " T1-3 v2").strip())
    return s[:n]


def bundle_g3(nc, feats, kind="orig"):
    """Everything the diagnostics need from a W7 fit on Epoch's rows."""
    import w7_models as w7, w7_data, w7_ppc
    from lib import data, ppc_checks as ppc
    df, ex = w7_data.load(kind, "lin"); el = ppc.Elig(df, data.read_member(data.SCORES))
    P, t = w7_ppc.post_arrays(Path(nc), feats)
    mu, kap = w7.mu_kappa(feats, P, df, ex)
    y = np.clip(df["performance"].to_numpy(float), EPS, 1 - EPS)
    rq = w7_ppc.rq_from(mu, kap, P)
    T, comp, mx = ppc.stats(y, rq, el)
    loo = az.loo(t, pointwise=True, var_name="obs")
    pit = np.asarray(az.loo_pit(w7_ppc.pit_tree(t, feats, kind), var_names="obs")["obs"]).ravel()
    org = df["Model"].map(ex["org_map"]).fillna("(none)").to_numpy()
    return dict(df=df, ex=ex, el=el, P=P, t=t, mu=mu, kap=kap, y=y, rq=rq, T=T, comp=comp, loo=loo,
                elpd_i=np.asarray(loo.elpd_i).ravel(), k=np.asarray(loo.pareto_k).ravel(), pit=pit, org=org,
                z=(y - rq["mubar"]) / np.sqrt(rq["v"]))


def pp_envelope(mu, kap, rq, seed=20261125):
    """One Beta draw per posterior draw, clipped as the data are; standardised with the fixed residual quantities."""
    rng = np.random.default_rng(seed)
    yr = np.clip(rng.beta(mu * kap, (1 - mu) * kap), EPS, 1 - EPS)
    return yr, (yr - rq["mubar"][None]) / np.sqrt(rq["v"])[None]


def pair_r(z, el):
    return np.array([np.corrcoef(z[ra], z[rb])[0, 1] for _, _, ra, rb in el.pairs])


def r_matrix(r, el):
    R = np.full((el.K, el.K), np.nan)
    for (a, b, _, _), v in zip(el.pairs, r): R[a, b] = R[b, a] = v
    np.fill_diagonal(R, 1.0); return R


def rep_maxima(cand="G3_ta99"):
    reps = [json.loads(p.read_text()) for p in (Path("runs/W/W7/rep") / cand).glob("r*.json")]
    reps = [r for r in reps if r["converged"]]
    return {k: np.array([r["maxima"][k] for r in reps]) for k in ("Qb", "q", "t", "cb")}, len(reps)
