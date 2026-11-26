"""M9 stage a on the latest EEE manifest: benchmark map, model map, source classes, pairs, audit sample.
Run from eci_work/v11:  eee_crosswalk.py [--audit-seed 20261113]
Hand-made inputs: tools/eee_bmap_rules.py, tools/eee_aliases.json, tools/eee_model_overrides.csv, SOURCES below.
Outputs under runs/EEE/crosswalk/."""
import sys, os, re, json, hashlib, argparse
import numpy as np, pandas as pd
sys.path.insert(0, "../tools")
from eee_xwalk_lib import *
from eee_bmap_rules import INCLUDE, MISMATCH

ap = argparse.ArgumentParser(); ap.add_argument("--audit-seed", type=int, default=20261113); A = ap.parse_args()
EEE = "ext/eee"

# ---- per-source table (hand-made; written to source_class.csv) ------------------------------------
# kind: own-run = the source runs the evaluation itself; leaderboard = benchmark owner's leaderboard;
# aggregator = relays numbers from papers, developer pages and leaderboards.
# epoch_pat: regex on Epoch's `source` string that identifies this organisation as the one Epoch cites.
SOURCES = [
 ("Artificial Analysis", "own-run", r"artificial ?analysis"),
 ("Vals.ai", "own-run", r"vals\.ai"),
 ("Hugging Face", "own-run", r"open llm leaderboard|huggingface"),
 ("Kensho", "own-run", r"kensho"),
 ("crfm", "own-run", r"crfm|helm"),
 ("Writer, Inc.", "own-run", r"writer"),
 ("Arcadia Impact", "own-run", r"arcadia|inspect evals"),
 ("ARC Prize Foundation", "leaderboard", r"arcprize|arc prize"),
 ("Terminal-Bench", "leaderboard", r"tbench|terminal-bench"),
 ("Mercor", "leaderboard", r"mercor"),
 ("Papers with Code", "aggregator", r"paperswithcode|papers with code"),
 ("LLM Stats", "aggregator", r"llm-stats|llm stats|llmstats"),
 ("BenchPress", "aggregator", r"benchpress"),
]
# Epoch source strings given as titles -> keyword expected in the EEE reference URL
EPOCH_SRC_ALIAS = {"arc prize leaderboard": "arcprize.org", "aider llm leaderboards": "aider.chat",
                   "terminal-bench v2 leaderboard": "tbench.ai", "cybench leaderboard": "cybench",
                   "os world website": "os-world", "theagentcompany": "theagentcompany",
                   "stanford crfm leaderboard": "crfm.stanford.edu", "stanford helm": "crfm.stanford.edu",
                   "vpct leaderboard": "vpct"}

os.makedirs(XW, exist_ok=True)
flat = pd.read_parquet(XW + "/flat.parquet")
flat = flat[flat.score.notna()].reset_index(drop=True)
bm = zread("benchmark_metadata.csv"); bm = bm[bm.in_eci].set_index("benchmark")
fi = zread("epoch_capabilities_index/processed_data_for_eci.csv")
sc = zread("epoch_capabilities_index/eci_scores.csv").drop_duplicates("Model").set_index("Model")
fit_groups = set(fi.Model)
cell = fi.set_index(["Model", "benchmark"])
EPOCH_RUN = {b for b in bm.index if "_external" not in str(bm.loc[b, "source_file"])}

# ---- benchmark map ---------------------------------------------------------------------------------
AL = json.load(open("../tools/eee_aliases.json"))
for c in ("collection", "evaluation_name", "dataset_name"):
    flat["n_" + c] = flat[c].map(norm_text)
KEY = ["collection", "evaluation_name", "dataset_name", "metric_id"]
flat["metric_id"] = flat.metric_id.fillna("")
flat["dataset_name"] = flat.dataset_name.fillna("")
cand = pd.Series(False, index=flat.index); cand_b = {}
uk = flat[KEY + ["n_collection", "n_evaluation_name", "n_dataset_name"]].drop_duplicates(KEY)
for b, als in AL.items():
    m = pd.Series(False, index=uk.index)
    for a in als:
        a = norm_text(a)
        for c in ("n_collection", "n_evaluation_name", "n_dataset_name"):
            m |= uk[c].str.contains(a, regex=False)
    for t in uk[m][KEY].itertuples(index=False):
        cand_b.setdefault(tuple(t), []).append(b)
inc_rule = {}
for (b, c, e, d, mid, scale, note) in INCLUDE:
    q = uk[(uk.collection == c) & (uk.evaluation_name == e)]
    if d: q = q[q.dataset_name == d]
    if mid: q = q[q.metric_id == mid]
    for t in q[KEY].itertuples(index=False):
        inc_rule[tuple(t)] = (b, scale, note)
counts = flat.groupby(KEY).size()
rows = []
for t in sorted(set(cand_b) | set(inc_rule)):
    n = int(counts.get(t, 0))
    if t in inc_rule:
        b, scale, note = inc_rule[t]
        rows.append(dict(zip(KEY, t), eci_benchmark=b, cls="include", version_match=True, split_match=True, metric_match=True, scale=scale, n_rows=n, note=note))
    else:
        s = "|".join(t); cls, why = "not-this-benchmark", "alias substring only; a different benchmark"
        for pat, c2, r2 in MISMATCH:
            if pat.lower() in s.lower():
                cls, why = c2, r2; break
        rows.append(dict(zip(KEY, t), eci_benchmark=";".join(sorted(set(cand_b.get(t, [])))), cls=cls,
                         version_match=cls not in ("version-mismatch", "not-this-benchmark"), split_match=cls != "split-mismatch",
                         metric_match=cls != "metric-mismatch", scale="", n_rows=n, note=why))
bmap = pd.DataFrame(rows)
bmap.to_csv(XW + "/benchmark_map.csv", index=False)
cs = flat.groupby("collection").size().rename("n_results").to_frame()
cs["n_candidate_rows"] = bmap[bmap.cls != "not-this-benchmark"].groupby("collection").n_rows.sum()
cs["n_alias_rows"] = bmap.groupby("collection").n_rows.sum()
cs["n_included_rows"] = bmap[bmap.cls == "include"].groupby("collection").n_rows.sum()
cs.fillna(0).astype(int).to_csv(XW + "/collection_screen.csv")
print("benchmark_map:", bmap.cls.value_counts().to_dict(), "| collections:", len(cs))

inc = flat.merge(bmap[bmap.cls == "include"][KEY + ["eci_benchmark", "scale"]], on=KEY)
inc = inc[inc.score >= 0]
inc["scale"] = inc.scale.astype(float)

# ---- model map -------------------------------------------------------------------------------------
exact, loose, mm = epoch_keys()
ov = pd.read_csv("../tools/eee_model_overrides.csv").fillna("")
mods = inc.groupby(["model_id", "model_name"], dropna=False).size().rename("n_rows").reset_index()
mods["model_name"] = mods.model_name.fillna("")
out = []
for mid, mname, n in mods.itertuples(index=False):
    st, gs, how = auto_map(mid, mname, exact, loose)
    reason = ""
    for r in ov.itertuples(index=False):
        if re.search(r.id_regex, str(mid)) and (not r.name_regex or re.search(r.name_regex, str(mname))):
            if r.group == "AMBIGUOUS":
                st, gs, how, reason = "ambiguous", sorted(set(gs)) or ["?"], "manual", r.reason
            else:
                st, gs, how, reason = "mapped", [r.group], "manual", r.reason
            break
    if st == "ambiguous":
        cls = "ambiguous-model"
    elif st == "unmapped":
        cls = "model-unmapped"
    else:
        cls = "mapped" if gs[0] in fit_groups else "model-not-in-fit"
    out.append(dict(model_id=mid, model_name=mname, n_rows=n, cls=cls, how=how, model_group=gs[0] if st == "mapped" else "",
                    candidates="; ".join(gs) if st == "ambiguous" else "", reason=reason))
mmap = pd.DataFrame(out)
mmap.to_csv(XW + "/model_map.csv", index=False)
print("model_map:", mmap.cls.value_counts().to_dict(), "| fitted groups reached:", mmap[mmap.cls == "mapped"].model_group.nunique())
inc["model_name"] = inc.model_name.fillna("")
inc = inc.merge(mmap[mmap.cls == "mapped"][["model_id", "model_name", "model_group", "how"]], on=["model_id", "model_name"])
inc = inc[[(g, b) in cell.index for g, b in zip(inc.model_group, inc.eci_benchmark)]].copy()
print("rows on Epoch cells:", len(inc))

# ---- normalise on Epoch's scale ---------------------------------------------------------------------
base = inc.eci_benchmark.map(bm.random_baseline); ceil = inc.eci_benchmark.map(bm.score_ceiling)
inc["raw_prop"] = inc.score * inc.scale
inc["norm"] = ((inc.raw_prop - base) / (ceil - base)).clip(0, 1)

# ---- provenance of each row (re-read the JSON for the reference fields) -----------------------------
def prov(path, idx):
    """Score-level reference of one result: where the number itself was taken from. The benchmark's home
    or dataset URL (source_data.url of pwc/benchpress, dataset_url) is NOT a reference for the score
    (first audit, 2026-11-21: treating it as one misclassified aggregator rows as same-upstream)."""
    d = json.load(open(os.path.join(EEE, "repo", path)))
    r = d["evaluation_results"][idx]
    sd = r.get("source_data") or {}; det = (r.get("score_details") or {}).get("details") or {}
    sda = (sd.get("additional_details") or {}) if isinstance(sd, dict) else {}
    coll = d.get("evaluation_id", "")
    urls = []
    if "llm-stats.com" in json.dumps(sd) or "llm_stats" in str(r.get("evaluation_name")):
        u = sd.get("url") if isinstance(sd, dict) else None
        u = u if isinstance(u, list) else ([u] if u else [])
        urls += [x for x in u if "llm-stats.com" not in str(x)][:1]      # first URL is the upstream page
    elif str(r.get("evaluation_name", "")).startswith(("paperswithcode.", "benchpress.")):
        for k in ("external_source_url", "source_url", "paper_arxiv_url", "paper_source_url", "reference_url"):
            if det.get(k): urls.append(det[k])
        if sda.get("reference_url"): urls.append(sda["reference_url"])
    else:
        u = sd.get("url") if isinstance(sd, dict) else None
        urls += u if isinstance(u, list) else ([u] if u else [])
    return " ".join(dict.fromkeys(str(u) for u in urls)), str(det.get("paper_title") or ""), str(det.get("benchpress_source_type") or ""), str(sda.get("reported_by") or "")
pv = [prov(p, i) for p, i in zip(inc.object_path, inc.res_idx)]
inc["ref_urls"] = [p[0] for p in pv]; inc["ref_title"] = [p[1] for p in pv]; inc["bp_type"] = [p[2] for p in pv]; inc["reported_by"] = [p[3] for p in pv]

SRC = {s[0]: s for s in SOURCES}
def src_org(row):
    c = row.collection
    if c == "terminal-bench-2.0": return "Terminal-Bench"
    if c in ("gpqa_diamond", "cybench", "gsm8k", "hellaswag", "piqa"): return "Arcadia Impact"
    return {"ARC Prize": "ARC Prize Foundation"}.get(row.source_org, row.source_org)
inc["src"] = inc.apply(src_org, axis=1)
missing = sorted(set(inc.src) - set(SRC))
assert not missing, missing
inc["src_kind"] = inc.src.map(lambda s: SRC[s][1])

def own_report(group, src):
    """Does Epoch's source string read as the developer's own paper or report for this model?"""
    s = str(src).lower()
    if s.startswith("http"): return False
    org = str(sc.Organization.get(group, "")).lower()
    toks = set(re.findall(r"[a-z]{3,}", group.lower())) | set(re.findall(r"[a-z]{4,}", org))
    toks -= {"jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec", "mini", "nano", "flash", "lite", "turbo", "preview", "max", "plus", "pro", "the", "large", "medium", "small", "open", "meta", "google", "research"}
    if "anthropic" in org: toks |= {"claude", "opus", "sonnet", "haiku", "anthropic"}
    if "openai" in org: toks |= {"openai", "gpt"}
    if "google" in org: toks |= {"gemini", "gemma", "palm"}
    if "meta" in org: toks |= {"llama"}
    if "xai" in org: toks |= {"grok"}
    return any(t in s for t in toks)

def classify(r):
    es = cell.loc[(r.model_group, r.eci_benchmark), "source"]
    es_s = "" if pd.isna(es) else str(es)
    refs = (r.ref_urls + " " + r.ref_title + " " + r.reported_by).lower()
    if r.eci_benchmark in EPOCH_RUN:
        if "epoch.ai" in refs or "epochai" in refs or "epoch ai" in refs:
            return "same-upstream", "reference is Epoch"
        if r.eci_benchmark.startswith("FrontierMath") and r.src_kind == "aggregator" and r.evaluator_relationship != "first_party":
            # the private FrontierMath sets are administered by Epoch; a page that is not the model's developer
            # and quotes a FrontierMath score relays Epoch's measurement
            return "same-upstream", "FrontierMath private set: third-party quote of Epoch's run"
        return "independent", "Epoch-run benchmark, non-Epoch source"
    if not es_s:
        return "upstream-unknown", "Epoch row has no source"
    esl = es_s.lower()
    if r.src_kind in ("own-run", "leaderboard"):
        if re.search(SRC[r.src][2], esl):
            return "same-upstream", "EEE source is the one Epoch cites"
        if r.src_kind == "leaderboard" and r.src == "Terminal-Bench" and "terminal-bench" in esl.replace(" ", "-"):
            return "same-upstream", "EEE source is the one Epoch cites"
        return ("independent", "own evaluation, not the source Epoch cites") if r.src_kind == "own-run" else ("upstream-unknown", "leaderboard not cited by Epoch's row")
    # aggregator
    if re.search(SRC[r.src][2], esl):
        return "same-upstream", "Epoch cites this aggregator"
    key = None
    if esl.startswith("http"):
        key = re.sub(r"^https?://(www\.)?", "", esl).split("/")[0]
    else:
        for k, v in EPOCH_SRC_ALIAS.items():
            if k in esl: key = v
    if key and key in refs:
        return "same-upstream", "aggregator reference is the source Epoch cites"
    nt, ne = norm_text(r.ref_title), norm_text(es_s)
    if len(nt) >= 12 and len(ne) >= 12 and (nt in ne or ne in nt):
        return "same-upstream", "aggregator cites the paper Epoch cites"
    dev = r.evaluator_relationship == "first_party" or r.bp_type in ("model_card", "official_blog", "system_card", "paper")
    if r.src == "Papers with Code" and r.ref_title:
        dev = own_report(r.model_group, r.ref_title)
    if dev and own_report(r.model_group, es_s):
        return "same-upstream", "developer-reported score relayed; Epoch cites the developer's report"
    return "upstream-unknown", "aggregated number not tied to the source Epoch cites"
cl = [classify(r) for r in inc.itertuples(index=False)]
inc["source_class"] = [c[0] for c in cl]; inc["class_reason"] = [c[1] for c in cl]
pd.DataFrame(SOURCES, columns=["source_org", "kind", "epoch_source_pattern"]).assign(
    n_rows=lambda d: d.source_org.map(inc.groupby("src").size()).fillna(0).astype(int)).to_csv(XW + "/source_class.csv", index=False)

# ---- pairs ------------------------------------------------------------------------------------------
inc = inc.sort_values(["model_group", "eci_benchmark", "src", "source_class", "norm", "eval_ts", "object_uuid"], ascending=[True, True, True, True, False, False, True])
g = inc.groupby(["model_group", "eci_benchmark", "src", "source_class"], sort=False)
pairs = g.head(1).copy()
pairs["n_records"] = g.size().to_numpy()
pairs["epoch_norm"] = [cell.loc[(m, b), "performance"] for m, b in zip(pairs.model_group, pairs.eci_benchmark)]
pairs["epoch_source"] = [cell.loc[(m, b), "source"] for m, b in zip(pairs.model_group, pairs.eci_benchmark)]
pairs["epoch_version"] = [cell.loc[(m, b), "model_version"] for m, b in zip(pairs.model_group, pairs.eci_benchmark)]
pairs["absdiff"] = (pairs.norm - pairs.epoch_norm).abs()
cols = ["model_group", "eci_benchmark", "src", "src_kind", "source_class", "class_reason", "norm", "raw_prop", "score", "scale", "epoch_norm", "absdiff",
        "epoch_source", "epoch_version", "n_records", "collection", "evaluation_name", "dataset_name", "metric_id", "model_id", "model_name", "how",
        "evaluator_relationship", "ref_urls", "ref_title", "object_path", "res_idx", "object_uuid"]
pairs = pairs[cols].sort_values(["eci_benchmark", "model_group", "src", "source_class"]).reset_index(drop=True)
pairs.to_csv(XW + "/pairs.csv", index=False)
inc[cols[:-0] if False else [c for c in cols if c not in ("n_records", "epoch_norm", "absdiff", "epoch_source", "epoch_version")]].to_parquet(XW + "/included_rows.parquet")
print("pairs:", len(pairs), pairs.source_class.value_counts().to_dict())
print("cells with any EEE pair:", pairs.groupby(["model_group", "eci_benchmark"]).ngroups, "of", len(fi))
su = pairs[pairs.source_class == "same-upstream"]
print(f"same-upstream control: n={len(su)} median|diff|={su.absdiff.median():.4f} share<=0.0015: {(su.absdiff <= 0.0015).mean():.3f}")
print(pairs.groupby("source_class").absdiff.describe()[["count", "50%", "mean", "75%"]].round(4).to_string())

# ---- audit sample -----------------------------------------------------------------------------------
pool = pairs[pairs.source_class.isin(["independent", "same-upstream"])].reset_index(drop=True)
rng = np.random.default_rng(A.audit_seed)
idx = np.sort(rng.choice(len(pool), size=50, replace=False))
aud = pool.loc[idx].copy()
aud.to_csv(XW + f"/audit_draw_{A.audit_seed}.csv", index=False)
sha = {f: hashlib.sha256(open(XW + "/" + f, "rb").read()).hexdigest() for f in ("benchmark_map.csv", "model_map.csv", "source_class.csv")}
json.dump(dict(maps_sha256=sha, n_pairs=int(len(pairs)), audit_pool=int(len(pool)), audit_seed=A.audit_seed,
               hand_inputs={f: hashlib.sha256(open("../tools/" + f, "rb").read()).hexdigest() for f in ("eee_bmap_rules.py", "eee_aliases.json", "eee_model_overrides.csv", "eee_crosswalk.py", "eee_xwalk_lib.py")}),
          open(XW + "/crosswalk_freeze.json", "w"), indent=1)
print("audit pool", len(pool), "drawn 50 with seed", A.audit_seed)
