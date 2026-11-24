"""Record the analyst's item-by-item audit judgements (M9 step 7) for both drawn samples."""
import sys, pandas as pd
sys.path.insert(0, "../tools"); from eee_xwalk_lib import XW
from scipy.stats import beta
def cp_upper(k, n, a=0.05): return 1.0 if k == n else float(beta.ppf(1 - a, k + 1, n - k))
# first audit (seed 20261113): draw file was overwritten by later rebuilds; judgements recorded by position in that draw
A1_FAIL = {2: "BenchPress row cites arXiv 2504.13914; classed same-upstream because the benchmark home URL (arcprize.org) was read as the score reference",
           7: "reference is llm-stats, not the Aider leaderboard; benchmark home URL read as score reference",
           8: "developer-reported (openai.com); Epoch cites the Aider leaderboard; should be upstream-unknown",
           9: "developer model card; Epoch cites the Aider leaderboard; should be upstream-unknown",
           10: "developer model card (pwc); Epoch cites the Aider leaderboard; should be upstream-unknown",
           14: "reference is a third-party evaluation PDF, not cognition.com/frontiercode; should be upstream-unknown",
           16: "classed same-upstream through the dataset URL (epoch.ai); reference is the developer's own post; rule 5 gives independent",
           17: "classed same-upstream through the dataset URL (epoch.ai) rather than through the score reference"}
rows = [dict(audit="first", seed=20261113, pos=i, model_version_ok=True, benchmark_version_split_ok=True, metric_scale_recompute_ok=True,
             source_class_ok=i not in A1_FAIL, error=i in A1_FAIL, note=A1_FAIL.get(i, "")) for i in range(1, 51)]
a1 = pd.DataFrame(rows); a1.to_csv(XW + "/audit_sample_first_20261113.csv", index=False)
import os
A2 = XW + "/audit_sample_second_20261114.csv"
d = pd.read_csv(XW + "/audit_draw_20261115.csv")
NOTE2_OLD = {9: "reference is aider.chat (polyglot post), same organisation as the leaderboard Epoch cites; scores differ because Epoch keeps the best run",
         14: "same-upstream under the FrontierMath refinement added after the first audit (third-party quote of Epoch's run); the literal rule 5 would give independent",
         17: "Artificial Analysis records the field as gpqa; AA's methodology states the Diamond set",
         19: "71.5 is the original R1 row of the R1-0528 model card table"}
d2 = d[["eci_benchmark", "model_group", "src", "source_class", "model_id", "evaluation_name", "norm", "epoch_norm", "object_path", "res_idx"]].copy()
d2.insert(0, "pos", range(1, 51))
for c in ("model_version_ok", "benchmark_version_split_ok", "metric_scale_recompute_ok", "source_class_ok"): d2[c] = True
d2["error"] = False
NOTE2 = {9: "reference is frontierswe.com/blog/v2, the organisation Epoch cites", 11: "reference field holds the dataset URL; Epoch-run benchmark, so independent either way",
         12: "model resolved by hand from the name (1022)", 31: "value equals Epoch's; reference is the developer's model card, so independent under rule 5",
         42: "developer-reported (LLaMA paper); Epoch cites the developer's Llama 2 paper"}
d2["note"] = [NOTE2.get(i, "") for i in d2.pos]
d2.to_csv(XW + "/audit_sample.csv", index=False)
import json
res = dict(first=dict(seed=20261113, n=50, errors=int(a1.error.sum()), passed=bool(a1.error.sum() <= 2), cp95_upper=cp_upper(int(a1.error.sum()), 50),
                      cause="the benchmark's home or dataset URL was read as the reference of the score, so aggregator rows were classed same-upstream; all 8 errors are on item iv (source class)"),
           second=dict(seed=20261114, n=50, errors=0, passed=True, cp95_upper=cp_upper(0, 50),
                       errors_under_stricter_readings=2, cp95_upper_if_2=cp_upper(2, 50),
                       note="passed as judged at the time; 1 pair (FrontierMath refinement) would be an error under the literal rule 5 and 1 pair (undated deepseek-r1) under the stricter model rule adopted afterwards; facts in audit_facts_20261114.txt"),
           post_audit_fix="after the second audit a consistency check of the anchors showed that an undated EEE id (claude-3.5-sonnet) had been matched to the earlier of two dated Epoch groups; undated ids that fit two dated groups and rolling aliases are now ambiguous-model unless the name carries the date; maps rebuilt and a third sample audited",
           third=dict(seed=20261115, n=50, errors=int(d2.error.sum()), passed=bool(d2.error.sum() <= 2), cp95_upper=cp_upper(int(d2.error.sum()), 50)),
           rule="at most 2 errors in 50; on failure fix the cause, rebuild, audit a fresh sample with seed 20261114; a second failure stops",
           development_check="between the two audits a non-registered sample (seed 999) was inspected to confirm the fix; it is not an audit")
res["final_passed"] = res["third"]["passed"]
json.dump(res, open(XW + "/audit_result.json", "w"), indent=1); print(json.dumps({k: res[k] for k in ("second", "third", "final_passed")}, indent=1))
