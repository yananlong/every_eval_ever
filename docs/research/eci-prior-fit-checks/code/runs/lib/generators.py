"""M4 simulation generators. A simulated dataset replaces only `performance`; the cell list is the real one."""
import hashlib
import numpy as np, pandas as pd

R_NULL, R_MISFIT = 199, 20
GENERATORS = ["null", "2d", "offset", "shape", "disp", "drift"]
REPS = {"null": R_NULL, "2d": R_MISFIT, "offset": R_MISFIT, "shape": R_MISFIT, "disp": R_MISFIT, "drift": R_MISFIT}
DEVELOPERS = ["OpenAI", "Anthropic", "Google DeepMind", "Alibaba", "Meta AI", "DeepSeek", "xAI"]


def seed_of(gen, r):
    return int.from_bytes(hashlib.sha256(f"{gen}:{r}".encode()).digest()[:4], "big")


class Pattern:
    def __init__(self, df, scores):
        mids, bids = df["model_id"].unique(), df["benchmark_id"].unique()
        mmap = {m: i for i, m in enumerate(mids)}; bmap = {b: i for i, b in enumerate(bids)}
        self.mi = np.array([mmap[m] for m in df["model_id"]]); self.bi = np.array([bmap[b] for b in df["benchmark_id"]])
        self.M, self.K = len(mids), len(bids)
        self.org = df["Model"].map(scores.drop_duplicates("Model").set_index("Model")["Organization"]).to_numpy()
        self.years = ((pd.to_datetime(df["date"]) - pd.to_datetime(df["benchmark_release_date"])).dt.days.to_numpy() / 365.25)


def position(gen, r, S):
    return int(np.floor(r * S / REPS[gen]))


def simulate(gen, r, theta, pat):
    """theta: dict capability (M,), difficulty (K,), slope (K,), sigma (K,) raw-scale. Returns (y, info)."""
    rng = np.random.default_rng(seed_of(gen, r))
    c, d, a, sg = theta["capability"].copy(), theta["difficulty"], theta["slope"], theta["sigma"]
    kap_b = 1 / (4 * sg ** 2) - 1
    mi, bi = pat.mi, pat.bi
    info = {}
    cap_row = c[mi].copy()
    if gen == "2d":
        cbar, sc = c.mean(), c.std()
        e = rng.standard_normal(pat.M)
        c2 = cbar + 0.7 * (c - cbar) + np.sqrt(1 - 0.49) * sc * e
        use = np.zeros(pat.K, bool); use[rng.choice(pat.K, 28, replace=False)] = True
        cap_row = np.where(use[bi], c2[mi], c[mi]); info["second_dim_benchmarks"] = np.where(use)[0].tolist()
    eta = a[bi] * (cap_row - d[bi])
    if gen == "offset":
        eligible = [o for o in DEVELOPERS if (pat.org == o).sum() >= 100]
        dev = eligible[rng.integers(len(eligible))]
        cnt = pd.Series(bi[pat.org == dev]).value_counts(); cand = sorted(cnt[cnt >= 5].index.tolist())
        bs = rng.choice(cand, 3, replace=False); cell = (pat.org == dev) & np.isin(bi, bs)
        eta = eta + 0.5 * cell; info.update(developer=dev, benchmarks=[int(b) for b in bs], n_cells=int(cell.sum()))
    if gen == "drift":
        eta = eta + 0.3 * np.minimum(3, np.maximum(0, pat.years))
    mu = np.clip(1 / (1 + np.exp(-np.clip(eta, -700, 700))), 1e-6, 1 - 1e-6)
    if gen == "shape":
        aff = np.zeros(pat.K, bool); aff[rng.choice(pat.K, 19, replace=False)] = True
        mu = mu * np.where(aff[bi], 0.85, 1.0); info["asymptote_benchmarks"] = np.where(aff)[0].tolist()
    if gen == "disp":
        y = np.clip(mu + sg[bi] * rng.standard_normal(len(mu)), 0.0, 1.0)
    else:
        k = kap_b[bi]; y = rng.beta(mu * k, (1 - mu) * k)
    return y, info
