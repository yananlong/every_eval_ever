"""TAX: apply Epoch's ECI domain tags (EvalGap Analysis doc, tab "Epoch AI") to our 57 ECI benchmarks.
Analysis only, no fits.  Run from runs/../v11 inside tpu-jupyter (see tools/ header convention).
Inputs: runs/TAX/epoch_ai_tab.md (verbatim copy of the doc tab), runs/EEE/input/eee_fit_input_annotated.csv,
runs/EEE/eci_compare.csv, runs/EEE/crosswalk/pairs.csv, runs/EEE/input/benchmark_data.zip, runs/W/BSEL/{design,chart_data}.json.
Outputs: runs/TAX/epoch_*.csv / .json / .md."""
import json, re, zipfile, io
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import spearmanr

R = Path("runs"); OUT = R / "TAX"; OUT.mkdir(exist_ok=True)
DOMAINS = ["Agent", "Computer use", "Conceptual reasoning", "Games", "Language understanding", "Long context", "Mathematics",
           "Multimodal", "Science", "Software engineering", "World knowledge", "Writing & creativity"]

# ---- 1. parse the doc tab -----------------------------------------------------------------------------------
txt = (OUT / "epoch_ai_tab.md").read_text().splitlines()
i0 = next(i for i, l in enumerate(txt) if l.startswith("A. ECI domain tags")); i1 = next(i for i, l in enumerate(txt) if l.startswith("B. "))
doc_tags, cur = {}, None
for l in txt[i0 + 1:i1]:
    l = l.strip()
    if not l: continue
    if l in DOMAINS: cur = l; continue
    doc_tags.setdefault(l, []).append(cur)
doc_size = {d: sum(d in t for t in doc_tags.values()) for d in DOMAINS}

# our name -> (doc name, note).  None = not in the doc.
XW = {
 "APEX-Agents": ("APEX-Agents", "exact"), "ANLI": ("Adversarial NLI", "renamed (abbreviation)"),
 "ARC AI2": ("ARC AI2", "exact"), "ARC-AGI": ("ARC-AGI-1", "renamed (doc adds version -1)"), "ARC-AGI-2": ("ARC-AGI-2", "exact"),
 "Aider polyglot": ("Aider Polyglot", "case"), "BBH": ("BBH", "exact"), "Balrog": ("BALROG", "case"),
 "CL-bench": ("CL-bench", "exact"), "CL-bench Life": ("CL-bench Life", "exact"), "CadEval": ("CadEval", "exact"),
 "Chess Puzzles": ("Chess Puzzles", "exact"), "Cybench": ("Cybench", "exact"), "DTBench": ("DTBench", "exact"),
 "ExploitBench": ("ExploitBench v0.1", "doc pins v0.1; our snapshot has no version label"),
 "Fiction.LiveBench": ("Fiction.liveBench", "case"), "FrontierCode": ("FrontierCode", "exact"),
 "FrontierMath-Tiers-1-3-v2-Private": ("FrontierMath Tiers 1-3 (v2)", "renamed (doc drops -Private)"),
 "FrontierMath-Tier-4-v2-Private": ("FrontierMath Tier 4 (v2)", "renamed (doc drops -Private)"),
 "FrontierMath-2025-02-28-Private": (None, "v1 Tiers 1-3, superseded_by FrontierMath-Tiers-1-3-v2-Private in Epoch's metadata; doc lists only v2; tags inherited from FrontierMath Tiers 1-3 (v2)"),
 "FrontierMath-Tier-4-2025-07-01-Private": (None, "v1 Tier 4, superseded_by FrontierMath-Tier-4-v2-Private in Epoch's metadata; doc lists only v2; tags inherited from FrontierMath Tier 4 (v2)"),
 "FrontierSWE": ("FrontierSWE (v2)", "doc pins v2; our snapshot has no version label (released 2026-09-02 in metadata)"),
 "Furniture Assembly": ("Furniture Assembly Benchmark", "renamed"), "GDPval": ("GDPval", "exact"),
 "GPQA diamond": ("GPQA Diamond", "case"), "GSM8K": ("GSM8K", "exact"), "GSO-Bench": ("GSO", "renamed"),
 "HellaSwag": ("HellaSwag", "exact"), "LAMBADA": ("LAMBADA", "exact"), "MATH level 5": ("MATH Level 5", "case"),
 "MMLU": ("MMLU", "exact"), "MirrorCode": ("MirrorCode", "exact"), "Mystery Game Puzzles": ("Mystery Game Puzzles", "exact"),
 "OSWorld": ("OS World", "renamed (spacing)"), "OSWorld 2.0": ("OSWorld 2.0", "exact"),
 "OTIS Mock AIME 2024-2025": ("OTIS Mock AIME 2024-2025", "exact"), "OpenBookQA": ("OpenBookQA", "exact"),
 "PIQA": ("PIQA", "exact"), "PostTrainBench": ("PostTrainBench v1.1", "doc pins v1.1; our snapshot has no version label"),
 "ProofBench": ("ProofBench", "exact"), "Remote Labor Index": ("Remote Labor Index", "exact"),
 "SimpleBench": ("SimpleBench", "exact"), "SimpleQA Verified": ("SimpleQA Verified", "exact"), "SpireClimb": ("SpireClimb", "exact"),
 "Surface Evolver Bench": ("Surface Evolver Bench", "exact"),
 "Terminal Bench": ("Terminal-Bench 2.0", "renamed; Epoch's rows cite the tbench.ai 2.0 leaderboard, metadata release date 2025-05-19 is v1's"),
 "The Agent Company": ("The Agent Company", "exact"), "TriviaQA": ("TriviaQA", "exact"), "VPCT": ("VPCT", "exact"),
 "WeirdML": ("WeirdML (v2)", "renamed (doc adds v2)"), "WeirdML v3": ("WeirdML (v3)", "renamed"),
 "Winogrande": ("WinoGrande", "case"),
 "LMCA": (None, "not in doc; in_eci in our 2026-11-13 snapshot (released 2026-08-12, conceptualreasoning.ai, same creator as DTBench); guess: dropped from the ECI list after our snapshot or omitted in the doc"),
 "GeoBench": (None, "not in doc; in_eci in our snapshot; guess: retired from the ECI list after our snapshot (benchmark from 2025-03) or omitted"),
 "METR Time Horizons": (None, "not in doc; in_eci in our snapshot; guess: retired from the ECI list after our snapshot or omitted"),
 "EBR-bench": (None, "not in doc; Epoch-run, in_eci in our snapshot (released 2026-07-01); guess: retired after our snapshot or omitted"),
 "DeepResearch Bench": (None, "not in doc; in_eci in our snapshot; guess: retired from the ECI list after our snapshot or omitted"),
}
INHERIT = {"FrontierMath-2025-02-28-Private": "FrontierMath Tiers 1-3 (v2)", "FrontierMath-Tier-4-2025-07-01-Private": "FrontierMath Tier 4 (v2)"}

fit = pd.read_csv(R / "EEE/input/eee_fit_input_annotated.csv")
ours = sorted(fit.benchmark.unique()); assert len(ours) == 57 and set(ours) == set(XW), set(ours) ^ set(XW)
for b, (dn, _) in XW.items():
    if dn is not None: assert dn in doc_tags, dn
rows = []
for b in ours:
    dn, note = XW[b]
    tags = doc_tags[dn] if dn else (doc_tags[INHERIT[b]] if b in INHERIT else [])
    basis = "doc" if dn else ("inherited" if b in INHERIT else "untagged")
    rows.append(dict(benchmark=b, doc_name=dn or "", tags=";".join(tags), n_tags=len(tags), tag_basis=basis, match_note=note))
bm = pd.DataFrame(rows)


def primary(tags):
    """Primary-tag rule: the benchmark's tag with the fewest benchmarks in the doc's list (most specific); ties by doc order."""
    return min(tags, key=lambda t: (doc_size[t], DOMAINS.index(t))) if tags else "Untagged"


bm["primary_tag"] = [primary(t.split(";") if t else []) for t in bm.tags]
bm.to_csv(OUT / "epoch_domain_map.csv", index=False)
doc_only = sorted(set(doc_tags) - {v[0] for v in XW.values() if v[0]})
tagmap = {r.benchmark: (r.tags.split(";") if r.tags else []) for r in bm.itertuples()}
prim = dict(zip(bm.benchmark, bm.primary_tag))
DOMX = DOMAINS + ["Untagged"]

# ---- 2. cell-level frame --------------------------------------------------------------------------------------
eci = pd.read_csv(R / "EEE/eci_compare.csv").set_index("model").eci_epoch
pairs = pd.read_csv(R / "EEE/crosswalk/pairs.csv")
ps = pairs.groupby(["model_group", "eci_benchmark", "src"]).agg(norm=("norm", "mean"), indep=("source_class", lambda s: (s == "independent").any()),
                                                                 rel=("evaluator_relationship", lambda s: ";".join(sorted(set(s))))).reset_index()
pc = ps.groupby(["model_group", "eci_benchmark"]).agg(n_src=("src", "nunique"), indep=("indep", "any"), rng=("norm", lambda x: x.max() - x.min()),
                                                      srcs=("src", lambda s: ";".join(sorted(s))),
                                                      first=("rel", lambda s: any("first_party" in x for x in s))).reset_index()
cells = fit[["Model", "benchmark", "epoch_performance", "eee_class", "source"]].merge(pc, left_on=["Model", "benchmark"], right_on=["model_group", "eci_benchmark"], how="left")
cells["n_src"] = cells.n_src.fillna(0).astype(int); cells["indep"] = cells.indep.fillna(False).astype(bool); cells["first"] = cells["first"].fillna(False).astype(bool)
assert (cells.n_src > 0).sum() == 688 and (cells.indep == (cells.eee_class == "independent")).all()
cells["eci"] = cells.Model.map(eci)
cells["primary"] = cells.benchmark.map(prim)
long = pd.DataFrame([dict(idx=i, domain=t) for i, b in cells.benchmark.items() for t in (tagmap[b] or ["Untagged"])])
cl = cells.join(long.set_index("idx"), how="inner")
N_MULTI, N_IND, N_COV = int((cells.n_src >= 2).sum()), int(cells.indep.sum()), int((cells.n_src > 0).sum())


def dstats(g, label):
    cov = g[g.n_src > 0]; mul = g[g.n_src >= 2]; per_model = g.groupby("Model").size()
    srcs = set(";".join(cov.srcs.dropna()).split(";")) - {""}
    bset = sorted(g.benchmark.unique())
    return dict(domain=label, benchmarks=len(bset), cells=len(g), models=g.Model.nunique(), median_scores_per_model=float(per_model.median()),
                eee_cells=len(cov), eee_share=round(len(cov) / len(g), 3), eee_benchmarks=cov.benchmark.nunique(),
                cells_2plus_src=len(mul), independent_cells=int(g.indep.sum()), first_party_cells=int(g["first"].sum()),
                median_between_src_range=round(float(mul.rng.median()), 4) if len(mul) else np.nan,
                share_of_all_multi=round(len(mul) / N_MULTI, 3), share_of_all_indep=round(g.indep.sum() / N_IND, 3), n_eee_sources=len(srcs),
                mean_eci_models=round(float(eci[g.Model.unique()].mean()), 1), median_eci_models=round(float(eci[g.Model.unique()].median()), 1),
                benchmarks_list=";".join(bset), uncovered_benchmarks=";".join(b for b in bset if b not in set(cov.benchmark)))


cov_multi = pd.DataFrame([dstats(cl[cl.domain == d], d) for d in DOMX] + [dstats(cells, "All 57")])
cov_prim = pd.DataFrame([dstats(cells[cells.primary == d], d) for d in DOMX] + [dstats(cells, "All 57")])
cov_multi.to_csv(OUT / "epoch_domain_coverage.csv", index=False)
cov_prim.to_csv(OUT / "epoch_domain_coverage_primary.csv", index=False)

# ---- 3. per-model profile --------------------------------------------------------------------------------------
prof = cl.pivot_table(index="Model", columns="domain", values="benchmark", aggfunc="size", fill_value=0).reindex(columns=DOMX, fill_value=0)
profp = cells.pivot_table(index="Model", columns="primary", values="benchmark", aggfunc="size", fill_value=0).reindex(columns=DOMX, fill_value=0)
P = pd.DataFrame(index=prof.index)
P["eci_epoch"] = eci[P.index]
P["band"] = pd.cut(P.eci_epoch, [-np.inf, 100, 130, 150, np.inf], right=False, labels=["<100", "100-130", "130-150", ">=150"])
top20 = set(eci.sort_values(ascending=False).index[:20]); P["frontier20"] = P.index.isin(top20)
P["n_cells"] = cells.groupby("Model").size()[P.index]
P["n_domains"] = (prof[DOMAINS] > 0).sum(axis=1); P["n_domains_primary"] = (profp[DOMAINS] > 0).sum(axis=1)
P["untagged_cells"] = prof["Untagged"]
for d in DOMX: P[d] = prof[d]
P = P.sort_values("eci_epoch", ascending=False)
P.reset_index().to_csv(OUT / "epoch_model_domain_profile.csv", index=False)


def band_tab(P, prof, profp):
    out = []
    groups = [(b, P[P.band == b]) for b in ["<100", "100-130", "130-150", ">=150"]] + [("frontier 20", P[P.frontier20]), ("all", P)]
    for lab, g in groups:
        m = prof.loc[g.index]; mp = profp.loc[g.index]
        r = dict(group=lab, models=len(g), median_cells=float(g.n_cells.median()), median_domains=float(g.n_domains.median()),
                 models_1_2_domains=int((g.n_domains <= 2).sum()), models_1_2_domains_primary=int((g.n_domains_primary <= 2).sum()))
        for d in DOMX:
            r[f"pct_models::{d}"] = round(100 * (m[d] > 0).mean(), 0)
            r[f"pct_cells_primary::{d}"] = round(100 * mp[d].sum() / mp.values.sum(), 1)
        out.append(r)
    return pd.DataFrame(out)


bt = band_tab(P, prof, profp); bt.to_csv(OUT / "epoch_band_by_domain.csv", index=False)
which12 = P[P.n_domains <= 2]
combos = which12.apply(lambda r: "+".join(d for d in DOMAINS if r[d] > 0) or "(none)", axis=1).value_counts()

# ---- 4. BSEL overlap --------------------------------------------------------------------------------------------
des = json.loads((R / "W/BSEL/design.json").read_text()); ch = json.loads((R / "W/BSEL/chart_data.json").read_text())
ref = {r["id"]: r for r in ch["refits"]}
def res(fid):
    r = ref.get(fid)
    if r is None or r.get("status") != "converged":
        alt = [k for k in ref if k.startswith(fid + "__s") and ref[k].get("status") == "converged"]
        r = ref[alt[0]] if alt else r
    return r
fits = des["fits"]
clusters = {f["id"]: f["drop"] for f in fits if f["kind"] == "cluster"}
ov = []
for cid, drop in clusters.items():
    r = res(cid); row = dict(cluster=cid, n_bench=len(drop), benchmarks=";".join(drop))
    for d in DOMX:
        members = [b for b in drop if (d in tagmap[b]) or (d == "Untagged" and not tagmap[b])]
        dsize = int((bm.tags.str.split(";").apply(lambda t: d in t)).sum()) if d != "Untagged" else int((bm.n_tags == 0).sum())
        row[d] = f"{len(members)}/{dsize}" if members else ""
    row.update(frontier_max_abs_shift=r["frontier_max_abs_shift"], stretch_change=r["stretch_change"], low_end_mean_shift=r["low_end_mean_shift"],
               scale_slope=r["affine_slope"], models_dropped=r["n_dropped_models"])
    ov.append(row)
ov = pd.DataFrame(ov); ov.to_csv(OUT / "epoch_bsel_cluster_overlap.csv", index=False)

lobo_id = {}
for f in fits:
    if f["kind"] in ("lobo", "a4") or (len(f["drop"]) == 1 and f["kind"] != "cluster"):
        lobo_id.setdefault(f["drop"][0], f["id"])
# prefer A4 id where both exist (A4 benchmarks have no separate LOBO in the design)
lobo = {b: res(fid) for b, fid in lobo_id.items()}
assert set(lobo) == set(ours), set(ours) - set(lobo)
rand = [f for f in fits if f["kind"] == "random"]
allfits = [f for f in fits]
dom_rows = []
for d in DOMX:
    B = [b for b in ours if (d in tagmap[b]) or (d == "Untagged" and not tagmap[b])]
    L = pd.DataFrame([dict(b=b, fs=lobo[b]["frontier_max_abs_shift"], st=lobo[b]["stretch_change"], lowend=lobo[b]["low_end_mean_shift"]) for b in B])
    # best coverage of this domain's benchmark set by any BSEL refit
    best = max(((len(set(B) & set(f["drop"])) / len(B), f["id"]) for f in allfits), key=lambda x: x[0])
    exact = [f["id"] for f in allfits if set(f["drop"]) == set(B)]
    contains = [f["id"] for f in allfits if set(B) <= set(f["drop"]) and len(B) > 1]
    # random-drop association: number of the domain's benchmarks dropped vs outcomes (n=20)
    k = np.array([len(set(B) & set(f["drop"])) for f in rand]); rr = [res(f["id"]) for f in rand]
    def sp(key):
        y = np.array([x[key] for x in rr]);
        return round(float(spearmanr(k, y).statistic), 2) if k.std() > 0 else np.nan
    cdrop = np.array([cells[cells.benchmark.isin(set(B) & set(f["drop"]))].shape[0] for f in rand])
    dom_rows.append(dict(domain=d, benchmarks=len(B), lobo_max_frontier_shift=round(L.fs.max(), 2), lobo_max_frontier_bench=L.loc[L.fs.idxmax(), "b"],
                         lobo_sum_stretch=round(L.st.sum(), 2), lobo_min_low_end=round(L.lowend.min(), 1), lobo_max_low_end=round(L.lowend.max(), 1),
                         lobo_low_end_extreme_bench=L.loc[L.lowend.abs().idxmax(), "b"],
                         bsel_exact_refit=";".join(exact), bsel_superset_refits=";".join(contains),
                         bsel_best_coverage=round(best[0], 2), bsel_best_refit=best[1],
                         rand_k_range=f"{k.min()}-{k.max()}", rand_spearman_k_stretch=sp("stretch_change"), rand_spearman_k_low_end=sp("low_end_mean_shift"),
                         rand_spearman_k_frontier_max=sp("frontier_max_abs_shift"), rand_spearman_k_slope=sp("affine_slope"),
                         rand_spearman_cells_low_end=round(float(spearmanr(cdrop, [x["low_end_mean_shift"] for x in rr]).statistic), 2) if cdrop.std() > 0 else np.nan))
dom_bsel = pd.DataFrame(dom_rows); dom_bsel.to_csv(OUT / "epoch_domain_vs_bsel.csv", index=False)

# ---- 4b. leave-one-domain-out feasibility (inclusion rule only, no fits) ------------------------------------------
import sys
sys.path.insert(0, str(Path("../tools").resolve())); sys.path.insert(0, str(R.resolve()))
import bsel_common as C
from lib import data
fdf = data.fit_input(); _, base_drop = C.subset(fdf, []); assert not base_drop
lodo = []
for d in DOMX:
    B = [b for b in ours if (d in tagmap[b]) or (d == "Untagged" and not tagmap[b])]
    sub, gone = C.subset(fdf, B)
    g = P.loc[[m for m in gone if m in P.index]]
    lodo.append(dict(domain=d, benchmarks_dropped=len(B), cells_dropped=int(cells.benchmark.isin(B).sum()), models_dropped=len(gone),
                     dropped_below100=int((g.band == "<100").sum()), dropped_frontier20=int(g.frontier20.sum()),
                     anchor_dropped=";".join(a for a in C.ANCHORS if a in gone), models_left=sub["Model"].nunique(),
                     new_vs_bsel=bool(dom_bsel.set_index("domain").loc[d, "bsel_best_coverage"] < 1)))
lodo = pd.DataFrame(lodo); lodo.to_csv(OUT / "epoch_lodo_feasibility.csv", index=False)

# ---- 5. Epoch's source per cell ---------------------------------------------------------------------------------
z = zipfile.ZipFile(R / "EEE/input/benchmark_data.zip")
meta = pd.read_csv(io.BytesIO(z.read("benchmark_metadata.csv"))).set_index("benchmark")
has_src_col = {}
for b in ours:
    f = meta.loc[b, "source_file"]
    hdr = z.read(f).decode("utf-8", "replace").splitlines()[0]
    has_src_col[b] = "Source" in [h.strip() for h in hdr.split(",")]
THIRD = re.compile(r"Stanford CRFM|Stanford HELM|lmcouncil|PapersWithCode", re.I)
CREATOR = re.compile(r"leaderboard|dashboard|website|https?://|github|tweet from .*creator|METR - Measuring", re.I)
DEV = re.compile(r"technical report|system card|model card|annou?nc|Open Foundation|Open and Efficient|Mixtral of Experts|Open Large-scale|Gemma:|Falcon Series|Textbooks Are All You Need|Model Card and Evaluations", re.I)


FALLBACK = set()
def origin(b, s):
    if not str(meta.loc[b, "source_file"]).endswith("_external.csv"): return "Epoch AI"
    if pd.isna(s) or s == "":
        return "Benchmark creator (assumed: file has no per-row source)" if not has_src_col[b] else "unknown (blank source)"
    if THIRD.search(s): return "Other third party"
    if DEV.search(s): return "Model developer"
    if CREATOR.search(s): return "Benchmark creator"
    FALLBACK.add(s); return "Model developer"   # remaining free-text titles are developer papers/reports (printed for review)


cells["origin"] = [origin(b, s) for b, s in zip(cells.benchmark, cells.source)]
print("developer by fallback:", sorted(FALLBACK))
otab = cells.groupby("origin").agg(cells=("Model", "size"), benchmarks=("benchmark", "nunique"), eee_cells=("n_src", lambda x: int((x > 0).sum())),
                                    multi=("n_src", lambda x: int((x >= 2).sum())), indep=("indep", "sum"),
                                    mean_eci=("eci", "mean")).reset_index()
otab["eee_share"] = (otab.eee_cells / otab.cells).round(3); otab["mean_eci"] = otab.mean_eci.round(1)
bsrc = cells.groupby("benchmark").origin.agg(lambda s: "; ".join(f"{k}={v}" for k, v in s.value_counts().items())).rename("origin_counts")
bmaj = cells.groupby("benchmark").origin.agg(lambda s: s.value_counts().index[0]).rename("origin_majority")
bsrc = pd.concat([bmaj, bsrc], axis=1).reset_index().merge(bm[["benchmark", "primary_tag", "tags"]], on="benchmark")
bsrc["epoch_run_file"] = [not str(meta.loc[b, "source_file"]).endswith("_external.csv") for b in bsrc.benchmark]
bsrc.to_csv(OUT / "epoch_source_by_benchmark.csv", index=False); otab.to_csv(OUT / "epoch_source_cells.csv", index=False)
odom = cl.assign(origin=cl.index.map(cells.origin)).pivot_table(index="domain", columns="origin", values="Model", aggfunc="size", fill_value=0).reindex(DOMX)
odom.to_csv(OUT / "epoch_source_by_domain.csv")

# ---- console summary ------------------------------------------------------------------------------------------
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40); pd.set_option("display.max_colwidth", 60)
print("doc benchmarks", len(doc_tags), "doc-only", doc_only, "doc sizes", doc_size)
print("tags per benchmark (ours, doc+inherited):", bm.n_tags.value_counts().sort_index().to_dict(), "mean", round(bm[bm.n_tags > 0].n_tags.mean(), 2))
print(bm[["benchmark", "doc_name", "tags", "primary_tag", "tag_basis"]].to_string())
cols = ["domain", "benchmarks", "cells", "models", "median_scores_per_model", "eee_cells", "eee_share", "eee_benchmarks", "cells_2plus_src", "independent_cells",
        "first_party_cells", "median_between_src_range", "share_of_all_multi", "share_of_all_indep", "n_eee_sources", "mean_eci_models", "uncovered_benchmarks"]
print("\n== coverage, multi-tag\n", cov_multi[cols].to_string())
print("\n== coverage, primary tag\n", cov_prim[cols[:-1]].to_string())
print("\n== bands\n", bt[["group", "models", "median_cells", "median_domains", "models_1_2_domains", "models_1_2_domains_primary"]].to_string())
print(bt.set_index("group")[[c for c in bt.columns if c.startswith("pct_models::")]].rename(columns=lambda c: c.split("::")[1][:10]).to_string())
print(bt.set_index("group")[[c for c in bt.columns if c.startswith("pct_cells_primary::")]].rename(columns=lambda c: c.split("::")[1][:10]).to_string())
print("\n1-2 domain models: band x n", pd.crosstab(which12.band, which12.n_domains).to_string()); print(combos.head(12).to_string())
print("n_domains dist", P.n_domains.value_counts().sort_index().to_dict()); print("frontier20 n_domains", P[P.frontier20].n_domains.describe().to_dict())
print("\n== BSEL clusters\n", ov.drop(columns="benchmarks").to_string())
print("\n== domain vs BSEL\n", dom_bsel.to_string())
print("\n== LODO feasibility\n", lodo.to_string())
print(cov_multi[["domain","mean_eci_models","median_eci_models","n_eee_sources"]].to_string())
print("\n== origin\n", otab.to_string()); print(odom.to_string()); print(bsrc[["benchmark", "origin_majority", "origin_counts"]].to_string())
