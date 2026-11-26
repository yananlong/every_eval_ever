"""Helpers for W6: extras for sub-frames, the candidates' mean and concentration (mirrors models.build_model), simulation from a posterior draw."""
import numpy as np, pandas as pd
from . import data, models

CANDIDATES = {"F0": models.Spec(), "F1": models.Spec(("2d",)), "F2": models.Spec(("dev",)), "F3": models.Spec(("asym",)),
              "F4": models.Spec(("drift",)), "F5": models.Spec(("hetero",)), "F6": models.Spec(prior="reference")}


def extras_info(df):
    ex = data.extras(df); sc = data.read_member(data.SCORES)
    org = df["Model"].map(sc.drop_duplicates("Model").set_index("Model")["Organization"])
    big = org.value_counts(); big = set(big[big >= 20].index)
    cnt = df.assign(org=org)[org.isin(big)].groupby(["org", "benchmark_id"]).size(); cells = cnt[cnt >= 5].index.tolist()
    ex["cells"] = cells; ex["org_map"] = sc.drop_duplicates("Model").set_index("Model")["Organization"].to_dict()
    ex["ref_id"] = df["benchmark_id"].unique()[ex["ref_bench"]]
    return ex


def extras_for(sub, full_ex):
    """Extras of a sub-frame (rows of the full frame, any order) with the full frame's cell list and reference benchmark."""
    cid = {c: i for i, c in enumerate(full_ex["cells"])}
    org = sub["Model"].map(full_ex["org_map"])
    cell_idx = np.array([cid.get((o, b), -1) for o, b in zip(org, sub["benchmark_id"])])
    gap = np.clip((pd.to_datetime(sub["date"]) - pd.to_datetime(sub["benchmark_release_date"])).dt.days.to_numpy() / 365.25, 0.0, 3.0)
    ref = int(np.where(sub["benchmark_id"].unique() == full_ex["ref_id"])[0][0])
    return dict(cell_idx=cell_idx, n_cells=full_ex["n_cells"], gap=gap, ref_bench=ref)


def mu_kappa(spec, P, df, ex):
    """P: dict of posterior arrays with leading draw axis. Returns mu (S, N) and kappa_obs (S, N)."""
    _, names_b, midx, bidx = models._index(df)
    K = len(names_b); f = set(spec.features)
    cap = P["capability"][:, midx]
    if "2d" in f:
        ref = ex["ref_bench"]; rest = np.array([b for b in range(K) if b != ref]); inv = np.zeros(K, int); inv[ref] = 0; inv[rest] = 1 + np.arange(K - 1)
        xi = np.concatenate([P["xi_ref"][:, None], P["xi_rest"]], axis=1)[:, inv]
        loading = P["tau_lambda"][:, None] * xi
        cap = cap + loading[:, bidx] * P["z"][:, midx]
    eta = P["slope"][:, bidx] * (cap - P["difficulty"][:, bidx])
    if "dev" in f:
        delta = np.concatenate([P["tau_delta"][:, None] * P["zeta"], np.zeros((P["zeta"].shape[0], 1))], axis=1)
        ci = np.where(ex["cell_idx"] < 0, ex["n_cells"], ex["cell_idx"]); eta = eta + delta[:, ci]
    if "drift" in f:
        eta = eta + P["gamma"][:, None] * ex["gap"][None, :]
    mu = 1 / (1 + np.exp(-np.clip(eta, -700, 700)))
    if "asym" in f: mu = (1 - P["eps"][:, bidx]) * mu
    mu = np.clip(mu, models.MU_EPS, 1 - models.MU_EPS)
    if "hetero" in f:
        lg = np.log(2 * P["sigma"][:, bidx]) - np.log1p(-2 * P["sigma"][:, bidx])
        s_row = 0.5 / (1 + np.exp(-(lg + P["tau_omega"][:, None] * P["phi"][:, midx])))
        kap = 1 / (4 * s_row ** 2) - 1
    else:
        kap = (1 / (4 * P["sigma"] ** 2) - 1)[:, bidx]
    return mu, kap


def simulate(spec, P, pos, df, ex, rng):
    Pi = {k: v[pos:pos + 1] for k, v in P.items()}
    mu, kap = mu_kappa(spec, Pi, df, ex)
    return rng.beta(mu[0] * kap[0], (1 - mu[0]) * kap[0])
