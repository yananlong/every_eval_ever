"""M5 check statistics T1-T7 and M6 calibration (unadjusted and max-T adjusted p-values, raw in-sample p-values).
Reads no true parameters: the inputs are a dataset (scores), the fit to it (posterior draws) and the real-data eligibility sets."""
import numpy as np, pandas as pd
from scipy.special import betainc
from scipy.stats import spearmanr

EPS = 1e-3
N_DRAWS = 400
MU_EPS = 1e-6
TNAMES = ["T1", "T2", "T3", "T4", "T5", "T6", "T7"]


class Elig:
    """Eligibility sets, fixed from the real observation pattern (M5)."""

    def __init__(self, df, scores):
        self.mi = df["model_id"].astype("category").cat.codes.to_numpy()
        # codes by first appearance to match the fit's ordering
        mids, bids = df["model_id"].unique(), df["benchmark_id"].unique()
        mmap = {m: i for i, m in enumerate(mids)}; bmap = {b: i for i, b in enumerate(bids)}
        self.mi = np.array([mmap[m] for m in df["model_id"]]); self.bi = np.array([bmap[b] for b in df["benchmark_id"]])
        self.M, self.K, self.N = len(mids), len(bids), len(df)
        self.model_names = df.drop_duplicates("model_id")["Model"].tolist()
        self.bench_names = df.drop_duplicates("benchmark_id")["benchmark"].tolist()
        cnt_b = np.bincount(self.bi, minlength=self.K); cnt_m = np.bincount(self.mi, minlength=self.M)
        self.t1_bench = np.where(cnt_b >= 20)[0]
        # T2 pairs: benchmarks sharing >= 15 models
        mat = np.zeros((self.M, self.K), bool); mat[self.mi, self.bi] = True
        self.row_of = -np.ones((self.M, self.K), int); self.row_of[self.mi, self.bi] = np.arange(self.N)
        self.pairs = []
        for a in range(self.K):
            for b in range(a + 1, self.K):
                sh = np.where(mat[:, a] & mat[:, b])[0]
                if len(sh) >= 15: self.pairs.append((a, b, self.row_of[sh, a], self.row_of[sh, b]))
        # T4 gaps (days, negative allowed)
        self.gap = (pd.to_datetime(df["date"]) - pd.to_datetime(df["benchmark_release_date"])).dt.days.to_numpy().astype(float)
        # T5 cells
        org = df["Model"].map(scores.drop_duplicates("Model").set_index("Model")["Organization"])
        orgs = org.value_counts(); orgs = set(orgs[orgs >= 20].index)
        cells = {}
        for r, (o, b) in enumerate(zip(org, self.bi)):
            if o in orgs: cells.setdefault((o, b), []).append(r)
        self.cells = [(k, np.array(v)) for k, v in cells.items() if len(v) >= 5]
        self.t7_models = np.where(cnt_m >= 6)[0]
        self.rows_of_model = [np.where(self.mi == m)[0] for m in range(self.M)]
        self.rows_of_bench = [np.where(self.bi == b)[0] for b in range(self.K)]
        self.model_org_none = org.isna().to_numpy()

    def summary(self):
        return dict(T1_benchmarks=len(self.t1_bench), T2_pairs=len(self.pairs), T5_cells=len(self.cells), T7_models=len(self.t7_models))


def thin(arr, n=N_DRAWS):
    tot = arr.shape[0]; return arr[np.linspace(0, tot - 1, min(n, tot)).astype(int)]


def mu_kappa(post, el):
    """post: dict with capability (S,M), difficulty (S,K), slope (S,K), sigma (S,K) -> mu (S,N), kappa (S,N)."""
    eta = post["slope"][:, el.bi] * (post["capability"][:, el.mi] - post["difficulty"][:, el.bi])
    mu = np.clip(1 / (1 + np.exp(-np.clip(eta, -700, 700))), MU_EPS, 1 - MU_EPS)
    kap = (1 / (4 * post["sigma"] ** 2) - 1)[:, el.bi]
    return mu, kap


def residual_quantities(post, el):
    mu, kap = mu_kappa(post, el)
    mubar = mu.mean(0)
    v = (mu * (1 - mu) / (kap + 1)).mean(0) + mu.var(0)
    chat = post["capability"].mean(0)
    # expected mass at the bounds
    a, b = mu * kap, (1 - mu) * kap
    p0 = betainc(a, b, EPS).mean(0)            # per row
    p1 = (1 - betainc(a, b, 1 - EPS)).mean(0)
    return dict(mubar=mubar, v=v, chat=chat, p0=p0, p1=p1)


def stats(y, rq, el, with_components=True):
    """T1-T7 of scores y (already clipped to [EPS, 1-EPS]) given residual quantities rq (from the fit to the same data)."""
    z = (y - rq["mubar"]) / np.sqrt(rq["v"])
    out = {}
    # T1
    Q = []
    for b in el.t1_bench:
        rows = el.rows_of_bench[b]; order = rows[np.argsort(rq["chat"][el.mi[rows]], kind="stable")]
        Q.append(sum(len(g) * z[g].mean() ** 2 for g in np.array_split(order, 4)))
    Q = np.array(Q); out["T1"] = float(Q.mean())
    # T2
    qs = []
    for a, b, ra, rb in el.pairs:
        r = np.corrcoef(z[ra], z[rb])[0, 1]
        if not np.isfinite(r): r = 0.0
        f = np.arctanh(np.clip(r, -.999, .999)); qs.append((len(ra) - 3) * f * f)
    qs = np.array(qs); out["T2"] = float(qs.mean())
    # T3
    edges = [0, .1, .3, .7, .9, 1.0000001]
    g = np.digitize(rq["mubar"], edges[1:-1]); groups = [list(np.where(g == k)[0]) for k in range(5)]
    sizes = [len(x) for x in groups]; bins = [[k] for k in range(5)]
    size = lambda b: sum(sizes[k] for k in b)
    while len(bins) > 1:
        small = [i for i, b in enumerate(bins) if size(b) < 30]
        if not small: break
        i = small[0]; b = bins[i]
        if max(b) < 2: nb = i + 1                  # below 0.3: merge toward 0.5 (the next bin)
        elif min(b) > 2: nb = i - 1               # above 0.7: merge toward 0.5 (the previous bin)
        else:                                      # contains the middle bin: merge with the larger neighbour
            cand = [j for j in (i - 1, i + 1) if 0 <= j < len(bins)]; nb = max(cand, key=lambda j: size(bins[j]))
        lo, hi = sorted((i, nb)); bins[lo] = bins[lo] + bins[hi]; del bins[hi]
    T3 = 0.0
    for b in bins:
        idx = np.concatenate([groups[k] for k in b]).astype(int)
        if len(idx) == 0: continue
        D = np.mean(z[idx] ** 2); T3 += len(idx) / len(y) * np.log(max(D, 1e-300)) ** 2
    out["T3"] = float(T3)
    # T4
    out["T4"] = float(abs(spearmanr(z, el.gap).statistic))
    # T5
    tt = np.array([z[r].sum() / np.sqrt(len(r)) for _, r in el.cells]); out["T5"] = float(np.abs(tt).max())
    # T6
    N0, N1 = float((y <= EPS).sum()), float((y >= 1 - EPS).sum()); E0, E1 = float(rq["p0"].sum()), float(rq["p1"].sum())
    out["T6"] = float((N0 - E0) ** 2 / (E0 + 1) + (N1 - E1) ** 2 / (E1 + 1))
    cb = np.array([(((y[r] <= EPS).sum() - rq["p0"][r].sum()) ** 2 / (rq["p0"][r].sum() + 1)) + (((y[r] >= 1 - EPS).sum() - rq["p1"][r].sum()) ** 2 / (rq["p1"][r].sum() + 1)) for r in el.rows_of_bench])
    # T7
    U = np.array([np.mean(z[el.rows_of_model[m]] ** 2) for m in el.t7_models]); out["T7"] = float(U.max())
    comp = dict(Qb=Q, q=qs, t=tt, cb=cb, U=U)
    maxima = dict(Qb=float(Q.max()), q=float(qs.max()), t=float(np.abs(tt).max()), cb=float(cb.max()))
    return (out, comp, maxima) if with_components else out


def max_t(obs, null):
    """obs: dict T->value; null: list of dicts. Returns unadjusted and max-T adjusted p (M6)."""
    R = len(null); res = {"R": R}
    L0 = np.array([[np.log(n[k] + 1e-12) for k in TNAMES] for n in null]); Lo = np.array([np.log(obs[k] + 1e-12) for k in TNAMES])
    allv = np.vstack([L0, Lo]); mean, sd = allv.mean(0), allv.std(0, ddof=1)
    sd = np.where(sd > 0, sd, 1.0)
    Zn = (L0 - mean) / sd; Zo = (Lo - mean) / sd; M = Zn.max(1)
    for j, k in enumerate(TNAMES):
        res[k] = dict(observed=float(obs[k]), p_unadjusted=float((1 + (L0[:, j] >= Lo[j]).sum()) / (R + 1)),
                      p_adjusted=float((1 + (M >= Zo[j]).sum()) / (R + 1)), z_obs=float(Zo[j]))
    return res


def raw_p(y, post, el, rq, T_obs, rng, n=N_DRAWS):
    """Raw in-sample posterior predictive p (M6): y_rep from each draw, residual quantities held at the real-data values."""
    mu, kap = mu_kappa(post, el); S = mu.shape[0]
    cnt = {k: 0 for k in TNAMES}
    for s in range(S):
        yrep = np.clip(rng.beta(mu[s] * kap[s], (1 - mu[s]) * kap[s]), EPS, 1 - EPS)
        t = stats(yrep, rq, el, with_components=False)
        for k in TNAMES: cnt[k] += t[k] >= T_obs[k]
    return {k: cnt[k] / S for k in TNAMES}
