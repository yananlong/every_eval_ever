"""Extension of block WA (anchor sensitivity; exploratory, beyond plan M11a). Post-processing of the W2 seed-12345 draws only.
(1) Gaps between posterior-mean ECIs for ALL pairs of models (WA reported the nine top-10 adjacent gaps only), and the 90% width
    of each pair's per-draw gap, under every WA anchor pair and two added pairs with a low-ECI anchor.
(2) Anchor VALUES changed with the anchor models fixed (WA moved identity only): exact rescaling, checked numerically.
(3) The three G-2D replicates that crashed in anchoring (2d_4, 2d_6, 2d_18): their truths are regenerated from the same
    posterior position and generator seed, and the two anchors are compared on the planted first and second capability.
Writes runs/W/WA_ext/ext.json. Run from eci_work/v11."""
import sys, json, os, warnings
sys.path.insert(0, "runs"); warnings.filterwarnings("ignore")
import numpy as np, xarray as xr
CRASHED = tuple(int(x) for x in os.environ.get("EEE_CRASHED_2D", "").split(",") if x)   # G-2D replicates that crashed in anchoring in the EEE-data W3
from lib import data, generators as G, anchors as A

eci, cap, names = A.load_seed(12345)
M = len(names); S = eci.shape[0]
df = data.fit_input(); vc = df["Model"].value_counts(); counts = np.array([int(vc.get(n, 0)) for n in names])
m0 = eci.mean(0)
io = [names.index(a) for a in A.ORIG]
wa = json.load(open("runs/W/WA/anchor_pairs.json"))["pairs"]
pairs = [dict(id=p["id"], low=p["low"], high=p["high"], tl=p["target_low"], th=p["target_high"], source="WA (M11a rule)") for p in wa]

# added exploratory pairs: the best-measured model below the original low anchor (most scores, then smallest capability SD)
sd = cap.std(0, ddof=1)
below = [i for i in range(M) if m0[i] < 125 and i not in io]
lo_x = sorted(below, key=lambda i: (-counts[i], sd[i]))[0]
top = int(np.argmax(m0))
for pid, hi in (("X-lowGPT5", io[1]), ("X-lowTop", top)):
    pairs.append(dict(id=pid, low=names[lo_x], high=names[hi], tl=float(m0[lo_x]), th=float(m0[hi]), source="added here (exploratory)"))

def gap_stats(d, excl):
    keep = np.array([i for i in range(M) if i not in excl])
    m = d.mean(0)[keep]; G0 = m0[keep]
    iu = np.triu_indices(len(keep), 1)
    g0 = (G0[:, None] - G0[None, :])[iu]; gk = (m[:, None] - m[None, :])[iu]
    lam = float((g0 * gk).sum() / (g0 * g0).sum())
    big = np.abs(g0) >= 1.0
    rel = np.abs(gk[big] / g0[big] - 1); relc = np.abs(gk[big] / (lam * g0[big]) - 1)
    # per-draw gap width ratio, frontier (top 20 by m0) pairs and all pairs (subsample of rows for memory)
    order = keep[np.argsort(-G0)]
    fr = order[:20]
    def wid(dd, idx):
        out = []
        for a in range(len(idx)):
            diff = dd[:, idx[a], None] - dd[:, idx[a + 1:]]
            if diff.shape[1]: q = np.quantile(diff, [.05, .95], axis=0); out.append(q[1] - q[0])
        return np.concatenate(out)
    rng = np.random.default_rng(0); sub = np.sort(rng.choice(keep, 80, replace=False))
    wf = wid(d, fr) / wid(eci, fr); wa_ = wid(d, sub) / wid(eci, sub)
    return dict(n_pairs=int(len(g0)), max_abs_gap_change=float(np.abs(gk - g0).max()), median_abs_gap_change=float(np.median(np.abs(gk - g0))),
                p95_abs_gap_change=float(np.quantile(np.abs(gk - g0), .95)),
                n_pairs_gap_ge1=int(big.sum()), rel_change_median=float(np.median(rel)), rel_change_p95=float(np.quantile(rel, .95)), rel_change_max=float(rel.max()),
                common_scale_lambda=lam, rel_change_after_lambda_p95=float(np.quantile(relc, .95)), rel_change_after_lambda_max=float(relc.max()),
                gap_width_ratio_frontier=dict(median=float(np.median(wf)), min=float(wf.min()), max=float(wf.max()), n=int(len(wf))),
                gap_width_ratio_sample80=dict(median=float(np.median(wa_)), min=float(wa_.min()), max=float(wa_.max()), n=int(len(wa_))))

res = []
for p in pairs:
    il, ih = names.index(p["low"]), names.index(p["high"])
    d, b, nbad = A.reanchor(cap, il, ih, p["tl"], p["th"])
    excl = set(io) | {il, ih}
    st = gap_stats(d, excl)
    w0 = A.widths(eci); wk = A.widths(d); keep = [i for i in range(M) if i not in excl]
    res.append(dict(**p, low_obs=int(counts[il]), high_obs=int(counts[ih]), n_bad_draws=nbad, scale_cv=float(np.nanstd(b) / np.nanmean(b)),
                    width_ratio_median=float(np.median(wk[keep] / w0[keep])), **st))
    print(p["id"], p["low"], "->", p["high"], {k: (round(v, 4) if isinstance(v, float) else v) for k, v in st.items() if not isinstance(v, dict)},
          "fw", {k: round(v, 3) for k, v in st["gap_width_ratio_frontier"].items()})

# (2) values changed, identity fixed
vals = []
for tl, th in ((100.0, 150.0), (130.0, 170.0), (0.0, 100.0), (130.0, 140.0)):
    d, _, _ = A.reanchor(cap, io[0], io[1], tl, th)
    k = (th - tl) / 20.0
    keep = [i for i in range(M) if i not in io]
    g0 = m0[keep][:, None] - m0[keep][None, :]; gk = d.mean(0)[keep][:, None] - d.mean(0)[keep][None, :]
    vals.append(dict(t_low=tl, t_high=th, factor=k, max_dev_gap_vs_factor=float(np.abs(gk - k * g0).max()),
                     max_dev_width_vs_factor=float(np.abs(A.widths(d)[keep] - k * A.widths(eci)[keep]).max()),
                     max_dev_mean_affine=float(np.abs(d.mean(0) - (tl + k * (m0 - 130.0))).max())))
print("values", vals)

# (3) crashed G-2D replicates: regenerate truth and second capability
pat = G.Pattern(df, data.read_member(data.SCORES))
t = xr.open_datatree("runs/W/W2/seed12345.nc"); post = t["posterior"].to_dataset()
P = {v: post[v].stack(s=("chain", "draw")).transpose("s", ...).to_numpy() for v in ["capability", "difficulty", "slope", "sigma"]}
mid_names = list(df["Model"].drop_duplicates())  # Pattern order = df model order
def second_cap(r):
    pos = G.position("2d", r, P["capability"].shape[0]); c = P["capability"][pos]
    rng = np.random.default_rng(G.seed_of("2d", r)); e = rng.standard_normal(pat.M)
    c2 = c.mean() + 0.7 * (c - c.mean()) + np.sqrt(1 - 0.49) * c.std() * e
    use = np.zeros(pat.K, bool); use[rng.choice(pat.K, 28, replace=False)] = True
    return pos, c, c2, use
# check the regeneration against a saved truth and the benchmarks recorded for a converged replicate
chk = {}
for r in (0, 1):
    pos, c, c2, use = second_cap(r)
    z = np.load(f"runs/W/W3/truth/2d_{r}.npz"); chk[r] = dict(cap_match=float(np.abs(z["capability"] - c).max()))
    js = f"runs/W/W3/rep/2d_{r}.json"
    if os.path.exists(js):
        info = json.load(open(js)); sdb = info.get("info", {}).get("second_dim_benchmarks") or info.get("second_dim_benchmarks")
        chk[r]["bench_match"] = None if sdb is None else bool(sorted(sdb) == np.where(use)[0].tolist())
print("regeneration check", chk)
# map anchor names to Pattern model index (posterior 'model' coordinate order is the same as df order: verify)
same_order = names == mid_names
bnames = list(df["benchmark_id"].unique())
crash = []
for r in CRASHED:
    pos, c, c2, use = second_cap(r)
    lo, hi = io  # posterior index == pattern index if same_order
    rows_lo = set(pat.bi[pat.mi == lo]); rows_hi = set(pat.bi[pat.mi == hi])
    crash.append(dict(r=r, position=int(pos), c1_low=float(c[lo]), c1_high=float(c[hi]), c2_low=float(c2[lo]), c2_high=float(c2[hi]),
                      second_dim_reversed=bool(c2[hi] <= c2[lo]),
                      low_bench_total=len(rows_lo), low_bench_on_c2=int(sum(use[b] for b in rows_lo)),
                      high_bench_total=len(rows_hi), high_bench_on_c2=int(sum(use[b] for b in rows_hi)),
                      c1_gap=float(c[hi] - c[lo]), c2_gap=float(c2[hi] - c2[lo]), c2_sd_noise=float(np.sqrt(.51) * c.std())))
print("same model order", same_order); print("crash", crash)
# the same quantities for the converged and non-crashed replicates, for comparison
allr = []
for r in range(20):
    pos, c, c2, use = second_cap(r); lo, hi = io
    allr.append(dict(r=r, c2_gap=float(c2[hi] - c2[lo]), c1_gap=float(c[hi] - c[lo]), reversed=bool(c2[hi] <= c2[lo])))
os.makedirs("runs/W/WA_ext", exist_ok=True)
json.dump(dict(seed=12345, n_draws=S, added_low_anchor=dict(name=names[lo_x], obs=int(counts[lo_x]), mean_eci=float(m0[lo_x]), cap_sd=float(sd[lo_x])),
               pairs=res, values=vals, regeneration_check=chk, same_model_order=same_order, crashed_2d=crash, all_2d=allr),
          open("runs/W/WA_ext/ext.json", "w"), indent=1)
print("all 2d", [(x["r"], round(x["c2_gap"], 3), x["reversed"]) for x in allr])
